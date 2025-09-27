# Analizador para archivos .brik (lenguaje de juegos)
# Autor: [Tu Nombre]
# Fecha: 2025-09-26
# Este analizador realiza el análisis léxico y sintáctico de archivos .brik y genera un árbol sintáctico en arbol.ast

import re
import sys
import os

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
        return f"Token({self.type}, {self.value}, {self.line}, {self.column})"

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
        s = f"{indent}{self.type}: {self.value if self.value else ''}\n"
        for child in self.children:
            s += child.__repr__(level+1)
        return s

# Parser recursivo descendente para hechos y listas
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    def eat(self, type_=None):
        tok = self.current()
        if tok is None:
            raise Exception('Unexpected end of input')
        if type_ and tok.type != type_:
            raise Exception(f'Expected {type_}, got {tok.type} at line {tok.line}')
        self.pos += 1
        return tok
    def parse(self):
        facts = []
        while self.current() is not None:
            facts.append(self.fact())
        return ASTNode('Programa', facts)
    def fact(self):
        # id ( args ) .
        id_tok = self.eat('ID')
        self.eat('LPAREN')
        args = self.args()
        self.eat('RPAREN')
        self.eat('DOT')
        return ASTNode('Hecho', [ASTNode('ID', value=id_tok.value)] + args)
    def args(self):
        args = [self.arg()]
        while self.current() and self.current().type == 'COMMA':
            self.eat('COMMA')
            args.append(self.arg())
        return args
    def arg(self):
        tok = self.current()
        if tok.type == 'NUMBER':
            return ASTNode('Numero', value=tok.value)
        elif tok.type == 'STRING':
            return ASTNode('Cadena', value=tok.value)
        elif tok.type == 'ID':
            return ASTNode('ID', value=tok.value)
        elif tok.type == 'LBRACKET':
            return self.list_()
        else:
            raise Exception(f'Unexpected token {tok.type} at line {tok.line}')
    def list_(self):
        self.eat('LBRACKET')
        elements = []
        if self.current().type != 'RBRACKET':
            elements.append(self.arg())
            while self.current().type == 'COMMA':
                self.eat('COMMA')
                elements.append(self.arg())
        self.eat('RBRACKET')
        return ASTNode('Lista', elements)

# -----------------------------
# FUNCION PRINCIPAL
# -----------------------------
def main():
    if len(sys.argv) < 2:
        print('Uso: python analizador.py archivo.brik')
        return
    archivo = sys.argv[1]
    with open(archivo, 'r', encoding='utf-8') as f:
        code = f.read()
    tokens = lexer(code)
    parser = Parser(tokens)
    try:
        ast = parser.parse()
    except Exception as e:
        print('Error de sintaxis:', e)
        return
    # Guardar el árbol sintáctico
    with open('arbol.ast', 'w', encoding='utf-8') as f:
        f.write(str(ast))
    print('Análisis completado. Árbol sintáctico guardado en arbol.ast')

if __name__ == '__main__':
    main()
