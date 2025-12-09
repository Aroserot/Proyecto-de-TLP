Motor gráfico (Tkinter) para la materia "Teoría de Lenguajes de Programación".

Requisitos:

- Python 2.7 (Tkinter viene incluido en la instalación estándar)

Estructura relevante:

- `Entrega1_Proyecto_Practico/analizador.py`: parser de archivos `.brik` y generación de AST/símbolos.
- `Entrega1_Proyecto_Practico/motor.py`: motor y juegos (Snake, Tetris) renderizados con Tkinter.
- `Entrega1_Proyecto_Practico/Snake.brik` y `Entrega1_Proyecto_Practico/Tetris.brik`: definición de reglas/elementos.

Cómo ejecutar (Windows PowerShell):

```powershell
# Desde la raíz del repo
python .\Entrega1_Proyecto_Practico\motor.py
```

Controles:

- Menú: flechas o `W/S` para moverse, `Enter` para seleccionar.
- Snake: flechas para mover; `P` pausa; `R` reinicia; `Esc` menú.
- Tetris: `A/D` mover; `S` caída rápida; `W` mantener; `E` rotar; `P` pausa; `R` reinicia; `Esc` menú.

Notas:

- El proyecto ya no usa `pygame`; el motor ha sido migrado totalmente a Tkinter para cumplir con el objetivo de compatibilidad con Python 2.7.
