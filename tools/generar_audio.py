#!/usr/bin/env python3
"""Genera los clips de audio de Kotoba no Mori.

Motores:
  edge (por defecto): voz neuronal de Microsoft (ja-JP-NanamiNeural) vía edge-tts; necesita internet.
  openjtalk:          Open JTalk (voz Mei, libre), funciona sin conexión; suena más sintética.

Uso:  python3 tools/generar_audio.py                       # edge, solo lo que falta
      python3 tools/generar_audio.py --motor openjtalk     # Open JTalk
      python3 tools/generar_audio.py --todo                # regenera todo
      python3 tools/generar_audio.py --voz ja-JP-KeitaNeural

Salida (mp3 mono 48 kb/s, recortado y normalizado):
  audio/kana/<romaji>.mp3        un clip por sonido (hiragana y katakana comparten)
  audio/w/<idPalabra>.mp3        la palabra (por su lectura en kana)
  audio/w/<idPalabra>-s.mp3      la frase de ejemplo
  audio/k/<idKanji>.mp3          la lectura principal del kanji (kun, si no on)
  audio/p/<idPaquete>-r<i>.mp3   líneas de lectura del paquete
  audio/p/<idPaquete>-g<i>.mp3   ejemplos de gramática
  audio/index.json               lista de claves disponibles (la app la usa para saber qué hay)

Requiere: edge → pip install edge-tts ; openjtalk → pip install pyopenjtalk soundfile numpy y ffmpeg en el PATH.
"""
import asyncio, glob, json, os, re, subprocess, sys, tempfile

MOTOR = sys.argv[sys.argv.index("--motor") + 1] if "--motor" in sys.argv else "edge"
VOZ = sys.argv[sys.argv.index("--voz") + 1] if "--voz" in sys.argv else "ja-JP-NanamiNeural"
if MOTOR == "openjtalk":
    import numpy as np, soundfile as sf, pyopenjtalk
else:
    import edge_tts

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio")
TODO = "--todo" in sys.argv

KANA = ("あa いi うu えe おo かka きki くku けke こko さsa しshi すsu せse そso たta ちchi つtsu てte とto "
        "なna にni ぬnu ねne のno はha ひhi ふfu へhe ほho まma みmi むmu めme もmo やya ゆyu よyo "
        "らra りri るru れre ろro わwa をwo んn "
        "がga ぎgi ぐgu げge ごgo ざza じji ずzu ぜze ぞzo だda ぢdji づdzu でde どdo ばba びbi ぶbu べbe ぼbo "
        "ぱpa ぴpi ぷpu ぺpe ぽpo "
        "きゃkya きゅkyu きょkyo しゃsha しゅshu しょsho ちゃcha ちゅchu ちょcho にゃnya にゅnyu にょnyo "
        "ひゃhya ひゅhyu ひょhyo みゃmya みゅmyu みょmyo りゃrya りゅryu りょryo "
        "ぎゃgya ぎゅgyu ぎょgyo じゃja じゅju じょjo びゃbya びゅbyu びょbyo ぴゃpya ぴゅpyu ぴょpyo").split()
KANA = [(re.match(r"[^\x00-\x7f]+", x).group(0), re.sub(r"[^\x00-\x7f]+", "", x)) for x in KANA]

def synth(text, speed=1.0):
    x, sr = pyopenjtalk.tts(text, speed=speed)
    x = x.astype(np.float32) / 32768.0
    # recorta silencio al principio y al final, deja 120 ms de aire
    thr = 0.01; idx = np.where(np.abs(x) > thr)[0]
    if len(idx): a = max(0, idx[0] - int(0.12 * sr)); b = min(len(x), idx[-1] + int(0.15 * sr)); x = x[a:b]
    peak = np.max(np.abs(x)) or 1.0; x = x * (0.9 / peak)
    return x, sr

def write_mp3(path, text, speed=1.0):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if MOTOR == "edge":
        # speed 0.85 → "-15%"; un kana suelto va más despacio para que se oiga entero
        rate = "%+d%%" % round((speed - 1) * 100)
        for intento in range(3):
            try:
                asyncio.run(edge_tts.Communicate(text, VOZ, rate=rate).save(path)); break
            except Exception as e:
                if intento == 2: raise
        if os.path.getsize(path) == 0: raise RuntimeError("clip vacío: " + text)
        return
    x, sr = synth(text, speed)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as t: tmp = t.name
    sf.write(tmp, x, sr)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "48k", path], check=True)
    os.unlink(tmp)

def clean_reading(r): return re.sub(r"[.\-()（）]", "", r or "")

jobs = []  # (clave, texto, velocidad)
for ch, ro in KANA:
    if ro == "n": continue
    jobs.append(("kana/" + ro, ch, 0.7))
for f in sorted(glob.glob(os.path.join(ROOT, "paquetes", "*.json"))):
    if f.endswith("index.json"): continue
    d = json.load(open(f, encoding="utf-8"))
    for wid, w in d.get("words", {}).items():
        jobs.append(("w/" + wid, w.get("kana") or w.get("jp"), 0.9))
        s = (w.get("sentence") or {}); txt = s.get("kana") or s.get("jp")
        if txt: jobs.append(("w/" + wid + "-s", txt, 0.9))
    for kid, k in d.get("kanji", {}).items():
        r = clean_reading((k.get("kun") or [None])[0]) or clean_reading((k.get("on") or [None])[0])
        if r: jobs.append(("k/" + kid, r, 0.9))
    for pid, p in d.get("packs", {}).items():
        for i, l in enumerate(p.get("reading") or []):
            txt = l.get("kana") or l.get("jp")
            if txt: jobs.append(("p/%s-r%d" % (pid, i), txt, 0.9))
        for i, g in enumerate(p.get("grammar") or []):
            ex = g.get("example") or {}; txt = ex.get("kana") or ex.get("jp")
            if txt: jobs.append(("p/%s-g%d" % (pid, i), txt, 0.9))

seen = set(); made = 0
for key, text, speed in jobs:
    if key in seen: continue
    seen.add(key)
    path = os.path.join(OUT, key + ".mp3")
    if TODO or not os.path.exists(path):
        write_mp3(path, text, speed); made += 1
json.dump({"motor": MOTOR, "voz": VOZ if MOTOR == "edge" else "mei", "keys": sorted(seen)}, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("clips:", len(seen), "generados ahora:", made)
