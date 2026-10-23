# Kotoba no Mori · 言葉の森

App de estudio de japonés de Max, camino a N2. Funciona sin conexión y se instala en el celular y la laptop.

## Cómo está armada

| Archivo | Para qué |
| --- | --- |
| `index.html` | La app completa |
| `sw.js` | Hace que funcione sin conexión |
| `manifest.webmanifest`, `icon-*.png` | Nombre e ícono al instalarla |
| `paquetes/index.json` | Lista de archivos de paquetes (con su versión) |
| `paquetes/AAAA-Www.json` | Un archivo por semana: `kanji`, `words`, `packs` y `cards` iniciales |

Cuando hay conexión, la app lee `paquetes/index.json` y descarga los archivos nuevos o con versión mayor. Sin conexión usa lo último que descargó.

El progreso (tarjetas, registro, diagnósticos, estado de paquetes) vive en el dispositivo. Si se configura la sincronización, se copia a `progreso.json` en el repositorio **privado** `kotoba-progreso`. Cada registro lleva su hora de cambio; al sincronizar gana el más reciente.

## Instalarla

- **Android (Chrome):** abrir la página → menú ⋮ → «Instalar app» o «Agregar a pantalla principal».
- **iPhone (Safari):** abrir la página → botón Compartir → «Agregar a pantalla de inicio».
- **Laptop (Chrome o Edge):** abrir la página → ícono de instalar en la barra de direcciones.

## Sincronizar celular y laptop

1. En GitHub: Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token.
2. Repository access: **Only select repositories** → `kotoba-progreso`.
3. Permissions → Repository permissions → **Contents: Read and write**. Nada más.
4. Expiración: la que prefieras (al vencer, la app avisa y se pega una nueva).
5. En la app: Progreso → Sincronización y respaldo → `usuario/kotoba-progreso` + la clave → Conectar.
6. Repetir el paso 5 en cada dispositivo.

La clave solo da acceso a ese repositorio privado y queda guardada en el dispositivo.

## Agregar paquetes (lo hace Claude)

1. Crear `paquetes/AAAA-Www.json` con el mismo formato de `2026-W43.json`.
2. Agregarlo a `paquetes/index.json`. Para corregir un archivo ya publicado, subir su `version`.
