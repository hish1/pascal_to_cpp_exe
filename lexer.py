import sys

class Lexer:
    def __init__(self, file_path : str = None):
        if file_path:
            self.file = open(file_path, 'r')
        else:
            self.file = None
        self.current_pos = 0
        self.current_char = None
        self.row, self.col = 1, 0

    def __del__(self):
        if self.file:
            self.file.close()

    KEYWORDS = {
        'if': 'IF',
        'else': 'ELSE',
        'while': 'WHILE',
        'for': 'FOR',
        'do': 'DO',
        'function': 'FUNCTION',
        'procedure': 'PROCEDURE',
        'array': 'ARRAY',
        'repeat': 'REPEAT',
        'number': 'NUMBER',
        'and': 'AND',
        'in': 'IN',
        'end': 'END',
        'then': 'THEN',
        'begin': 'BEGIN',
        'var': 'VAR',
        'type': 'TYPE',
        'const': 'CONST',
        'program': 'PROGRAM',
        'true': 'TRUE',
        'to': 'TO',
        'false': 'FALSE',
        'until': 'UNTIL',
        'of': 'OF',
        'case' : 'CASE',
        'div' : 'DIV',
        'mod' : 'MOD'
    }

    TYPES = {
        'byte': 'BYTE',
        'word': 'WORD',
        'longword': 'LONGWORD',
        'uint64': 'UINT64',
        'shortint': 'SHORTINT',
        'smallint': 'SMALLINT',
        'integer': 'INTEGER',
        'int64': 'INT64',
        'boolean': 'BOOLEAN',
        'char': 'CHAR',
        'string': 'STRING',
        'real': 'REAL',
        'double': 'DOUBLE'
    }

    n_tabs = 4
    SYMBOLS = {
        ':=': 'ASSIGN',
        '=': 'EQUALITY',
        '+': 'PLUS',
        '-': 'MINUS',
        '*': 'MULTIPLY',
        '/': 'DIVIDE',
        '(': 'LPAREN',
        ')': 'RPAREN',
        '[': 'LBR',
        ']': 'RBR',
        '{': 'LCBR',
        '}': 'RCBR',
        '\t': 'TAB',
        '<=': 'GREATER_OR_EQUAL',
        '>=': 'SMALLER_OR_EQUAL',
        '<>': 'NONEQUALITY',
        ' ' * n_tabs: 'TAB',
        ',': 'COMMA',
        ':': 'COLON',
        ';': 'SEMICOLON',
        '<': 'SMALLER',
        '>': 'GREATER',
        "'": 'SINGLE_QUOTE',
        '"': 'DOUBLE_QUOTE',
        '.': 'DOT',
        '..': 'ARRDOT',
        '\n': 'NEWLINE'
    }

    def error(self, message):
        print("Lexer error:", message, f"at line {self.row}, index {self.col - 1}")
        sys.exit(1)

    def add_file(self, file_path):
        if self.file:
            self.file.close()
        self.file = open(file_path, 'r')

    def has_next(self):
        return self.current_char != ''

    def get_next_char(self):
        if self.has_next():
            self.current_char = self.file.read(1)
        if self.current_char == '\n':
            self.row += 1
            self.col = 0
        else:
            self.col += 1

    def get_next_token(self):
        self.state = None
        self.value = None
        while self.state is None:
            if self.current_char is None:
                self.get_next_char()

            # end of file
            if self.current_char == '':
                self.state = 'EOF'
                self.value = 'eof'

            # whitespaces and tabulation
            elif self.current_char in [' ', '\t', '\n']:
                self.get_next_char()

            # string quote1
            elif self.current_char == "'":
                self.value = ""
                self.get_next_char()
                while self.current_char != "'":
                    self.value += self.current_char
                    self.get_next_char()
                self.get_next_char()
                if self.current_char == "'":
                    self.value += "'"
                    self.get_next_char()
                    while self.current_char != "'":
                        self.value += self.current_char
                        self.get_next_char()
                    self.get_next_char()
                if len(self.value) == 1:
                    self.state = 'CHAR_VAL'
                else:
                    self.state = 'STRING_VAL'

            # symbols
            elif self.current_char in Lexer.SYMBOLS:

                # assign :=
                if self.current_char == ':':
                    self.get_next_char()
                    if self.current_char == '=':
                        self.state = 'ASSIGN'
                        self.value = ':='
                        self.get_next_char()
                    else:
                        self.state = 'COLON'
                        self.value = ':'
                        self.get_next_char()
                
                # <= >= and <>
                elif self.current_char in ('>', '<'):
                    val = self.current_char
                    self.get_next_char()
                    if self.current_char in ('=', '>'):
                        val += self.current_char
                        self.get_next_char()
                    self.state = Lexer.SYMBOLS[val]
                    self.value = val

                #  array dot ..
                elif self.current_char == '.':
                    self.get_next_char()
                    if self.current_char == '.':
                        self.state = 'ARRDOT'
                        self.value = '..'
                        self.get_next_char()
                    else:
                        self.state = 'DOT'
                        self.value = '.'
                        self.get_next_char()

                # comment (* *)
                elif self.current_char == '(':
                    prev = self.current_char
                    self.get_next_char()
                    if self.current_char == '*':
                        self.state = 'COMMENT'
                        self.value = '(*'
                        while self.current_char != "*":
                            self.value += self.current_char
                            self.get_next_char()
                        self.get_next_char()
                        if self.current_char != ")":
                            self.value += self.current_char
                            self.get_next_char()
                            while self.current_char != ")":
                                self.value += self.current_char
                                self.get_next_char()
                            self.value += ')'
                            self.get_next_char()
                    else:
                        self.state = 'LPAREN'
                        self.value = prev

                else:
                    self.state = Lexer.SYMBOLS[self.current_char]
                    self.value = self.current_char  # ?
                    self.get_next_char()  # ?

            # numbers float and integer
            elif self.current_char != None and self.current_char.isdigit():
                number = 0
                while self.current_char.isdigit():
                    number = number * 10 + int(self.current_char)
                    self.get_next_char()
                if self.current_char.isalpha() or self.current_char == "_":
                    self.error(f'Invalid identifier')
                if self.current_char == '.':
                    number = str(number)
                    number += '.'
                    self.get_next_char()
                    while self.current_char.isdigit():
                        number += self.current_char
                        self.get_next_char()
                    if self.current_char == '.':
                        number = number[:-1]
                        self.current_char += '.'
                    elif number[len(number) - 1] == '.':
                        self.error(f'Invalid number ')
                number = str(number)
                self.state = 'NUMBER'
                self.value = str(number)

            # identifiers, keywords and reserved names
            elif self.current_char != None and self.current_char.isalpha() or self.current_char == '_':
                identifier = ""
                while self.current_char.isalpha() or self.current_char.isdigit() or self.current_char == '_':
                    identifier += self.current_char
                    self.get_next_char()
                if identifier.lower() in Lexer.KEYWORDS:
                    self.state = Lexer.KEYWORDS[identifier.lower()]
                    self.value = identifier  # ?
                elif identifier.lower() in Lexer.TYPES:
                    self.state = Lexer.TYPES[identifier.lower()]
                    self.value = identifier
                else:
                    self.state = 'IDENTIFIER'
                    self.value = identifier
            else:
                self.error(f'Unexpected symbol: {self.current_char}')

        token = (self.state, self.value, self.row, self.col)
        return token

if __name__ == '__main__':
    lexer = Lexer()
    lexer.add_file('test/test pascal file.pas')
    while lexer.has_next():
        print(lexer.get_next_token())