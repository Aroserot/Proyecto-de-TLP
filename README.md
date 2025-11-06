Motor gráfico mínimo para la materia "Teoría de Lenguajes de Programación" (Entrega 2).

Requisitos:

- Python 2.7
- pygame (ver `requirements.txt`)

Archivos:

- `engine.py`: motor gráfico mínimo. Contiene inicialización de ventana, bucle principal, funciones para dibujar rectángulos y texto y manejo de entradas.
- `example_game.py`: ejemplo que mueve un ladrillo con las teclas de flecha.

Cómo ejecutar:

1. Crear un virtualenv con Python 2.7 (ejemplo usando virtualenv):

```powershell
virtualenv -p C:\\ruta\\a\\python2.7 venv; .\\venv\\Scripts\\activate
pip install -r requirements.txt
python example_game.py
```

Notas:

- He creado código compatible con Python 2.7; revisa y adapta la documentación que entregues según necesites.

Detalles rápidos del motor:

- Ventana de 640x480 por defecto.
- Bucle principal con control de FPS (60 por defecto).
- Funciones para dibujar rectángulos y texto, y registrar handlers de teclado.

"Contrato" básico:

- Input: eventos de teclado y función de actualización opcional.
- Output: render en ventana y terminación limpia al cerrar la ventana.

Próximos pasos recomendados:

- Añadir documentación técnica y ejemplos adicionales (p.ej. Tetris.brik y Snake.brik) que conformen los juegos a probar.

Nota sobre desarrollo sin pygame real:

He incluido un pequeño "stub" local en la carpeta `pygame/` para resolver importaciones y poder editar/analizar el código sin tener instalado pygame. Este stub NO implementa rendering ni eventos reales. Para ejecutar el juego en tu máquina instala la versión real de pygame y elimina o ignora la carpeta `pygame/` del proyecto.

Para usar pygame real:

1. Elimina la carpeta `pygame/` del repositorio (o renómbrala) para que la importación resuelva al paquete instalado en el entorno.
2. Instala pygame en tu virtualenv: `pip install -r requirements.txt`.
