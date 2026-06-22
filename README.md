# Legión Binaria Arcade — versión Python + Frontend Web

Este proyecto es una conversión del proyecto original hecho en Java de consola a una aplicación web hecha con:

- **Python** para el backend.
- **HTML + CSS + JavaScript** para el frontend.
- **SQLite** como base de datos por defecto.

La app puede usar MongoDB opcionalmente si se configura una URI y se instala `pymongo`.

---

## Juegos incluidos

Se mantuvieron las reglas principales de los juegos del proyecto Java:

1. **Ahorcado**

   - Palabra aleatoria.
   - Letras usadas.
   - Máximo 6 errores.

2. **Auto con obstáculos**

   - 3 carriles.
   - Un obstáculo por turno.
   - El jugador gana si esquiva 5 obstáculos.
   - Pierde si queda en el mismo carril que el obstáculo.

3. **Piedra, papel o tijera**

   - 3 rondas.
   - Si hay empate general, se juega desempate.

4. **Penales**

   - El jugador elige izquierda, centro o derecha.
   - El arquero elige una dirección aleatoria.
   - Se gana con 7 goles antes de 3 atajadas.

5. **Torres de Hanoi**

   - 2 a 8 discos.
   - Solo se puede mover un disco por vez.
   - No se puede poner un disco grande sobre uno chico.
   - Se gana si se completa en la cantidad mínima de movimientos.

6. **Juego de memoria**
   - 4 niveles.
   - 5, 10, 15 y 20 palabras.
   - Hay que recordar el orden correcto.

---

## Base de datos

Por defecto el proyecto usa **SQLite** y crea el archivo:

```txt
data/los_idos.db
```

La app puede usar **MongoDB** si se configura la URI y se instala `pymongo`.

Las colecciones creadas son:

- `users`
- `login_sessions`
- `game_sessions`
- `scores`

### Variables de entorno para MongoDB

- `MONGODB_URI`: URI de conexión de MongoDB.
- `MONGODB_DB`: nombre de la base de datos.

También se pueden usar estas alternativas para el nombre de la base:

- `MONGO_DB`
- `MONGO_DATABASE`

### Ejemplo en Bash

```bash
export MONGODB_URI='mongodb+srv://<usuario>:<password>@<cluster>/<db>'
export MONGODB_DB='los_idos'
python app.py
```

### Ejemplo en PowerShell

```powershell
$env:MONGODB_URI = 'mongodb+srv://<usuario>:<password>@<cluster>/<db>'
$env:MONGODB_DB = 'los_idos'
python app.py
```

### Ejemplo en CMD

```cmd
set MONGODB_URI=mongodb+srv://<usuario>:<password>@<cluster>/<db>
set MONGODB_DB=los_idos
python app.py
```

Cuando `MONGODB_URI` está configurada y `pymongo` está instalada, la app usa MongoDB.
Si no, se mantiene con SQLite.

---

---

## Cómo abrirlo en Visual Studio Code

### 1. Descomprimir el ZIP

Descomprimí el archivo y abrí la carpeta:

```txt
los_idos_python
```

con Visual Studio Code.

---

### 2. Verificar que Python esté instalado

En la terminal de VS Code ejecutá:

```bash
python --version
```

Si en Windows no reconoce `python`, probá:

```bash
py --version
```

---

### 3. Crear entorno virtual

En la terminal, parado dentro de la carpeta del proyecto, ejecutá:

#### Windows

```bash
py -m venv .venv
```

Activar entorno:

```bash
.venv\Scripts\activate
```

#### Mac / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 4. Instalar dependencias

Este proyecto funciona con las librerías estándar de Python, pero si querés usar MongoDB también necesitás instalar la dependencia del driver:

```bash
python -m pip install -r requirements.txt
```

Si no vas a usar MongoDB, podés seguir usando la versión con SQLite sin instalar nada adicional.

---

### 5. Ejecutar el servidor

#### Windows

```bash
python app.py
```

O si usás el launcher de Python:

```bash
py app.py
```

#### Mac / Linux

```bash
python3 app.py
```

Deberías ver algo parecido a:

```txt
Los Idos - versión Python + HTML/CSS/JavaScript
Servidor iniciado en http://127.0.0.1:8000
Base de datos SQLite: .../data/los_idos.db
Presioná Ctrl+C para detener.
```

---

### 6. Abrir la página

Entrá desde el navegador a:

```txt
http://127.0.0.1:8000
```

Ahí vas a poder:

1. Crear un usuario.
2. Iniciar sesión.
3. Elegir juegos.
4. Jugar desde una página web.
5. Ver puntajes guardados.

---

## Cómo ver la base de datos

Opcionalmente, podés instalar la extensión de VS Code:

```txt
SQLite Viewer
```

Luego abrís el archivo:

```txt
data/los_idos.db
```

y vas a poder ver las tablas `users`, `login_sessions`, `game_sessions` y `scores`.

---

## Cómo reiniciar la base de datos

Si querés borrar todos los usuarios y puntajes:

1. Cerrá el servidor con `Ctrl + C`.
2. Borrá el archivo:

```txt
data/los_idos.db
```

3. Volvé a ejecutar:

```bash
python app.py
```

La base se va a crear nuevamente vacía.

---

## Estructura del proyecto

```txt
los_idos_python/
│
├── app.py                  # Backend Python, API, lógica de juegos y SQLite
├── README.md               # Instrucciones de uso
│
├── data/
│   └── los_idos.db   # Se crea automáticamente al ejecutar
│
└── static/
    ├── index.html          # Página principal
    ├── styles.css          # Estilos
    └── app.js              # Frontend JavaScript
```

---

## Qué hace Python en este proyecto

Python reemplaza la lógica que antes estaba en Java:

- Maneja usuarios y login.
- Crea y consulta la base de datos.
- Ejecuta las reglas de cada juego.
- Guarda sesiones de juego.
- Guarda resultados y puntajes.
- Expone una API para que JavaScript pueda comunicarse con el backend.

JavaScript se encarga de:

- Mostrar las pantallas.
- Enviar jugadas al backend.
- Actualizar la página sin usar consola.
- Renderizar tableros, botones, mensajes y resultados.
