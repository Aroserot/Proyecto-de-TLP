# -*- coding: utf-8 -*-
# Analizador para archivos .brik (lenguaje de juegos)
# Uso:
#   (Dentro de la carpeta Entrega1_Proyecto_Practico)
#       python analizador.py Snake.brik
#       python analizador.py Tetris.brik
#   (Desde la raíz del repo Proyecto-de-TLP)
#       python Entrega1_Proyecto_Practico\analizador.py Entrega1_Proyecto_Practico\Snake.brik
#       python Entrega1_Proyecto_Practico\analizador.py Entrega1_Proyecto_Practico\Tetris.brik
# Genera: Snake.ast / Snake.json   Tetris.ast / Tetris.json
# Si 'python' falla usa: py analizador.py Snake.brik
# Autor: [Andres Rosero Toledo, Chris Ordoñez Alvarado, Edna Pamplona López]
# Fecha: 2025-10-04
# Este analizador realiza el análisis léxico y sintáctico de archivos .brik y genera un árbol sintáctico en arbol.ast

import re
import sys
import os
import json
import io

# Compatibilidad entre Py2 y Py3 para unicode
if sys.version_info[0] >= 3:
    unicode = str

# -----------------------------
# LÉXICO: Definición de tokens
# -----------------------------
TOKEN_SPECIFICATION = [
    ('COMMENT',    r'%.*'),
    ('NUMBER',     r'\d+(\.\d+)?'),
    ('STRING',     r"'[^']*'"),
    ('ID',         r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('LBRACKET',   r'\['),
    ('RBRACKET',   r'\]'),
    ('LPAREN',     r'\('),
    ('RPAREN',     r'\)'),
    ('COMMA',      r','),
    ('DOT',        r'\.'),
    ('EQUALS',     r'='),
    ('WS',         r'[ \t\n]+'),
]

TOKEN_REGEX = '|'.join('(?P<%s>%s)' % pair for pair in TOKEN_SPECIFICATION)

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
    def __repr__(self):
        return "Token({0}, {1}, {2}, {3})".format(self.type, self.value, self.line, self.column)

def lexer(code):
    tokens = []
    line_num = 1
    line_start = 0
    for mo in re.finditer(TOKEN_REGEX, code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start
        if kind == 'WS':
            if '\n' in value:
                line_num += value.count('\n')
                line_start = mo.end()
            continue
        if kind == 'COMMENT':
            continue
        tokens.append(Token(kind, value, line_num, column))
    return tokens

# -----------------------------
# SINTÁCTICO: Árbol sintáctico
# -----------------------------
class ASTNode:
    def __init__(self, type_, children=None, value=None):
        self.type = type_
        self.children = children or []
        self.value = value
    def __repr__(self, level=0):
        indent = '  ' * level
        s = "{0}{1}: {2}\n".format(indent, self.type, self.value if self.value else '')
        for child in self.children:
            s += child.__repr__(level+1)
        return s
    def to_dict(self):
        if self.type == 'Hecho':
            pred = self.children[0].value
            args = [c.to_dict() for c in self.children[1:]]
            return {'predicado': pred, 'args': args}
        if self.type in ('Numero', 'Cadena', 'ID'):
            return self.value
        if self.type == 'Lista':
            return [c.to_dict() for c in self.children]
        if self.type == 'Programa':
            return [c.to_dict() for c in self.children]
        return {'type': self.type, 'value': self.value}

def _convert_atom(v):
    if isinstance(v, str):
        if len(v) >= 2 and v.startswith("'") and v.endswith("'"):
            v = v[1:-1]
        try:
            if '.' in v:
                return float(v)
            return int(v)
        except:
            return v
    return v

def build_symbol_tables(ast):
    # Tabla tipo anterior (predicado -> lista de listas)
    raw = {}
    # Diccionario anidado (predicado -> {clave: valor / lista})
    nested = {}
    for hecho in ast.children:
        if hecho.type != 'Hecho' or not hecho.children:
            continue
        pred = hecho.children[0].value
        args_nodes = hecho.children[1:]
        args_vals = []
        for a in args_nodes:
            val = a.to_dict()
            if isinstance(val, list):
                val = [_convert_atom(x) for x in val]
            else:
                val = _convert_atom(val)
            args_vals.append(val)
        raw.setdefault(pred, []).append(args_vals)
        # Construcción anidada heurística: si primer arg es clave y hay segundo -> asignar
        if len(args_vals) >= 2 and isinstance(args_vals[0], (str, int, float)):
            clave = args_vals[0]
            valor = args_vals[1] if len(args_vals) == 2 else args_vals[1:]
            # Normalizar
            if isinstance(valor, list):
                valor = valor
            if pred not in nested:
                nested[pred] = {}
            # Si la clave se repite, acumular en lista
            if clave in nested[pred]:
                if not isinstance(nested[pred][clave], list):
                    nested[pred][clave] = [nested[pred][clave]]
                nested[pred][clave].append(valor)
            else:
                nested[pred][clave] = valor
        else:
            # Sin forma clave-valor: guardar lista completa
            nested.setdefault(pred, {}).setdefault('_records', []).append(args_vals)
    return raw, nested

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # Utilidades básicas
    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', '', -1, -1)

    def advance(self):
        self.pos += 1

    def expect(self, type_):
        tok = self.current()
        if tok.type != type_:
            raise SyntaxError("Se esperaba {0} y se encontró {1} en línea {2}, col {3}".format(type_, tok.type, tok.line, tok.column))
        self.advance()
        return tok

    def match(self, type_):
        if self.current().type == type_:
            tok = self.current()
            self.advance()
            return tok
        return None

    # Gramática:
    # Programa -> Hecho*
    def parse(self):
        hechos = []
        while self.current().type not in ('EOF',):
            hechos.append(self.parse_hecho())
        return ASTNode('Programa', hechos)

    # Hecho -> ID '(' ArgList? ')' '.'
    def parse_hecho(self):
        pred_tok = self.expect('ID')
        self.expect('LPAREN')
        args = []
        if self.current().type != 'RPAREN':
            args = self.parse_arg_list()
        self.expect('RPAREN')
        self.expect('DOT')
        # Nodo Hecho: primer hijo el predicado como ID, luego argumentos
        return ASTNode('Hecho', [ASTNode('ID', value=pred_tok.value)] + args)

    # ArgList -> Elemento (',' Elemento)*
    def parse_arg_list(self):
        elems = [self.parse_elemento()]
        while self.match('COMMA'):
            elems.append(self.parse_elemento())
        return elems

    # Elemento -> Lista | Atom
    def parse_elemento(self):
        tok = self.current()
        if tok.type == 'LBRACKET':
            return self.parse_lista()
        return self.parse_atom()

    # Lista -> '[' (Elemento (',' Elemento)*)? ']'
    def parse_lista(self):
        self.expect('LBRACKET')
        items = []
        if self.current().type != 'RBRACKET':
            items.append(self.parse_elemento())
            while self.match('COMMA'):
                items.append(self.parse_elemento())
        self.expect('RBRACKET')
        return ASTNode('Lista', items)

    # Atom -> NUMBER | STRING | ID
    def parse_atom(self):
        tok = self.current()
        if tok.type == 'NUMBER':
            self.advance()
            return ASTNode('Numero', value=tok.value)
        if tok.type == 'STRING':
            self.advance()
            return ASTNode('Cadena', value=tok.value)
        if tok.type == 'ID':
            self.advance()
            return ASTNode('ID', value=tok.value)
        raise SyntaxError("Token inesperado {0} en línea {1}, col {2}".format(tok.type, tok.line, tok.column))

__all__ = ['Token', 'lexer', 'ASTNode', 'Parser', 'build_symbol_tables', 'parse_code']

def parse_code(code):
    """Conveniencia: devuelve AST directamente desde el texto."""
    tokens = lexer(code)
    parser = Parser(tokens)
    return parser.parse()

def write_outputs(ast, raw, nested, src_path):
    base = os.path.splitext(os.path.basename(src_path))[0]
    out_dir = os.path.dirname(os.path.abspath(src_path))
    ast_path = os.path.join(out_dir, base + ".ast")
    symbols_path = os.path.join(out_dir, base + ".json")
    with io.open(ast_path, 'w', encoding='utf-8') as f:
        f.write(unicode(str(ast)))
    with io.open(symbols_path, 'w', encoding='utf-8') as f:
        f.write(unicode(json.dumps({'raw': raw, 'nested': nested}, ensure_ascii=False, indent=2)))
    print("OK: AST -> {0}".format(ast_path))
    print("OK: Símbolos -> {0}".format(symbols_path))

# -----------------------------
# FUNCION PRINCIPAL
# -----------------------------
def main():
    if len(sys.argv) < 2:
        print('Uso: python analizador.py archivo.brik')
        return
    archivo = sys.argv[1]
    if not os.path.isfile(archivo):
        print('Error: no existe el archivo {0}'.format(archivo))
        return
    # Compatibilidad Py2: usar io.open para encoding
    try:
        with io.open(archivo, 'r', encoding='utf-8') as f:
            code = f.read()
    except TypeError:
        # Fallback si no soporta encoding
        with open(archivo, 'r') as f:
            code = f.read()
    tokens = lexer(code)
    if not tokens:
        print('Archivo vacío o sin tokens válidos.')
        return
    parser = Parser(tokens)
    try:
        ast = parser.parse()
    except Exception as e:
        print('Error de sintaxis:', e)
        return
    raw, nested = build_symbol_tables(ast)
    if not raw:
        print('Advertencia: no se reconocieron hechos. ¿Faltan puntos finales "."?')
    write_outputs(ast, raw, nested, archivo)

if __name__ == '__main__':
    main()
# (Sin impresión de TOKENS cuando se importa como módulo)