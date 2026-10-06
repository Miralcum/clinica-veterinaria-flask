# Clínica Veterinaria Patitas – Sistema de citas (Flask)

## Estructura

```
vetclinic/
├── app.py                  ← sistema Flask (rutas, BD, login, CSV)
├── requirements.txt
├── docs/DOCUMENTACION.md   ← requisitos, casos de uso, diagramas y reporte
├── templates/              ← base, login, inicio, ficha, formulario, macros
└── static/
    ├── css/estilos.css
    └── img/                ← AQUÍ van tus fotos
```

## Imágenes que debes poner en `static/img/`

| Archivo | Qué foto buscar |
|---|---|
| banner.jpg | Interior de una clínica veterinaria (horizontal) |
| perro1.jpg | Max – perro |
| gato1.jpg | Luna – gato |
| perro2.jpg | Rocky – perro |
| gato2.jpg | Michi – gato |
| conejo.jpg | Copo – conejo |
| perro3.jpg | Bella – perro |
| hamster.jpg | Nina – hámster |
| loro.jpg | Kiwi – loro/ave |
| tortuga.jpg | Tito – tortuga |
| gato3.jpg | Simba – gato |

Deben ser **.jpg** con esos nombres exactos (en minúsculas). Si falta alguna, se muestra una huellita de reemplazo. Las fotos que subas desde el formulario se guardan solas en la misma carpeta.

## Cómo ejecutarlo

```bash
pip install flask
python app.py
```

Abre http://127.0.0.1:5000

| Usuario | Contraseña |
|---|---|
| cristina | Patitas123 |
| daniel | Huellitas456 |

La base de datos `veterinaria.db` se crea sola la primera vez con los 10 pacientes. Si quieres reiniciar los datos, borra ese archivo y vuelve a ejecutar.
