import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))
try:
    sys.path.remove(str(parent))
except ValueError: # Already removed
    pass

from other.Node import Node
from enum import StrEnum

class ProgramType(StrEnum):
    PROGRAM = 'PROGRAM'; MODULE = 'MODULE'

class Operator(StrEnum):
    PLUS = 'PLUS'; MINUS = 'MINUS'; MULTIPLY = 'MULTIPLY'; DIVIDE = 'DIVIDE';
    UNARY_PLUS = 'UNARY_PLUS'; UNARY_MINUS = 'UNARY_MINUS'; NOT = 'NOT';
    EQUALITY = 'EQUALITY'; NONEQUALITY = 'NONEQUALITY'; GREATER = 'GREATER'; SMALLER = 'SMALLER';
    GREATER_OR_EQUAL = 'GREATER_OR_EQUAL'; SMALLER_OR_EQUAL = 'SMALLER_OR_EQUAL';
    MOD = 'MOD'; DIV = 'DIV'; IN = 'IN'; SHL = 'SHL'; SHR = 'SHR'; ASSIGN = 'ASSIGN';
    ARRAY_CALL = 'ARRAY_CALL'; SUBROUTINE_CALL = 'SUBROUTINE_CALL'; 
    OBJECT_CALL = 'OBJECT_CALL'; AND = 'AND'; OR = 'OR'; XOR = 'XOR'

    def __str__(self):
        return self.value

    @classmethod
    def get_value_operators(cls):
        return [cls.PLUS, cls.MINUS, cls.MULTIPLY, cls.DIVIDE, cls.UNARY_PLUS, cls.UNARY_MINUS, cls.NOT,
        cls.EQUALITY, cls.NONEQUALITY, cls.GREATER, cls.SMALLER, cls.GREATER_OR_EQUAL, cls.SMALLER_OR_EQUAL, 
        cls.MOD, cls.DIV]

    @classmethod
    def get_condition_operators(cls):
        return [cls.GREATER, cls.SMALLER, cls.EQUALITY, cls.NONEQUALITY, cls.GREATER_OR_EQUAL, cls.SMALLER_OR_EQUAL]

# Тип функции
class SubroutineType(StrEnum):
    PROCEDURE = 'PROCEDURE'; FUNCTION = 'FUNCTION'

class PrimitiveType(StrEnum):
    UNDEFINED = 'UNDEFINED', -1; # Standart type
    BYTE = 'BYTE', 1; WORD = 'WORD', 2; LONGWORD = 'LONGWORD', 4; UINT64 = 'UINT64', 8; # Unsigned integer
    SHORTINT = 'SHORTINT', 1; SMALLINT = 'SMALLINT', 2; INTEGER = 'INTEGER', 4; INT64 = 'INT64', 8 # Signed integer
    SINGLE = 'SINGLE', 4; REAL = 'REAL', 8; DOUBLE = 'DOUBLE', 8; DECIMAL = 'DECIMAL', 16; # Float values
    BOOLEAN = 'BOOLEAN', 1; CHAR = 'CHAR', 1; STRING = 'STRING', -1 # Other

    def __new__(cls, value, byte_weight):
        member = str.__new__(cls, value)
        member._value_ = value
        member.byte_weight = byte_weight
        match value:
            case 'BYTE' | 'WORD' | 'LONGWORD' | 'UINT64' | 'SHORTINT' | 'SMALLINT' | 'INTEGER' | 'INT64':
                member.operators = (Operator.PLUS, Operator.MINUS, Operator.MULTIPLY, Operator.DIVIDE, 
                                    Operator.DIV, Operator.MOD, Operator.GREATER, Operator.SMALLER,
                                    Operator.GREATER_OR_EQUAL, Operator.SMALLER_OR_EQUAL, 
                                    Operator.EQUALITY, Operator.NONEQUALITY, Operator.UNARY_MINUS, 
                                    Operator.UNARY_PLUS, Operator.NOT)
            case 'SINGLE' | 'REAL' | 'DOUBLE' | 'DECIMAL':
                member.operators = (Operator.PLUS, Operator.MINUS, Operator.MULTIPLY, Operator.DIVIDE, 
                                    Operator.GREATER, Operator.SMALLER, Operator.EQUALITY, 
                                    Operator.GREATER_OR_EQUAL, Operator.SMALLER_OR_EQUAL,Operator.NONEQUALITY,
                                    Operator.NONEQUALITY, Operator.UNARY_MINUS, Operator.UNARY_PLUS, Operator.NOT)
            case 'BOOLEAN':
                member.operators = (Operator.NOT, Operator.AND, Operator.OR, Operator,Operator.XOR,
                                    Operator.GREATER_OR_EQUAL, Operator.SMALLER_OR_EQUAL, 
                                    Operator.GREATER, Operator.SMALLER, Operator.EQUALITY, Operator.NOT)
            case 'CHAR' | 'STRING' :
                member.operators = (Operator.PLUS, Operator.GREATER, Operator.SMALLER, Operator.EQUALITY, 
                                    Operator.NONEQUALITY, Operator.NOT)
            case _: member.operators = ()
        return member

    def __str__(self):
        return self.value

    def support_operation(self, operation_type):
        return operation_type in self.operators

    @classmethod
    def __contains__(cls, item):
        return item in cls.__members__

    @classmethod
    def get_unsigned_int_by_weight(cls, weight):
        if weight > 8: weight = 8
        types = [cls.BYTE, cls.WORD, cls.LONGWORD, cls.UINT64]
        return list(filter(lambda x: x.byte_weight == weight, types))[0]

    @classmethod
    def get_signed_int_by_weight(cls, weight):
        if weight > 8: weight = 8
        types = [cls.SHORTINT, cls.SMALLINT, cls.INTEGER, cls.INT64]
        return list(filter(lambda x: x.byte_weight == weight, types))[0]
    
    @classmethod
    def is_type_unsigned_integer(cls, type):
        return type in [cls.BYTE, cls.WORD, cls.LONGWORD, cls.UINT64]
    
    @classmethod
    def is_type_signed_integer(cls, type):
        return type in [cls.SHORTINT, cls.SMALLINT, cls.INTEGER, cls.INT64]

    @classmethod
    def is_type_integer(cls, type):
        return type in [cls.BYTE, cls.WORD, cls.LONGWORD, cls.UINT64, cls.SHORTINT, cls.SMALLINT, cls.INTEGER, cls.INT64]

    @classmethod
    def get_all_integer_types(cls):
        return [cls.BYTE, cls.WORD, cls.LONGWORD, cls.UINT64, cls.SHORTINT, cls.SMALLINT, cls.INTEGER, cls.INT64]

    @classmethod
    def get_float_types(cls):
        return [cls.SINGLE, cls.REAL, cls.DOUBLE, cls.SINGLE]

class NodeStatementPart(Node):
    def __init__(self, statements = list()):
        self.statements = statements
    def append(self, statement):
        self.statements.append(statement)

# Основная программа
class MainNode(Node):
    def __init__(self, program_type = ProgramType.PROGRAM, node_body = None):
        self.program_type = program_type
        self.node_body = node_body

class NodeDeclarationPart(Node):
    def __init__(self, declaration_list = list()):
        self.declaration_list = declaration_list

# Класс для описания программы (НЕ модуля)
class NodeProgram(Node):
    def __init__(self, 
                 identifier= '', 
                 global_declaration= NodeDeclarationPart(list()), 
                 statement_part = NodeStatementPart()):
        self.identifier = identifier
        self.global_declaration = global_declaration
        self.statement_part = statement_part

# Класс для хранение значения и его типа (возможно уберу)
class NodeValue(Node):
    def __init__(self, value, _type):
        self.value = value
        self.type = _type

# Классы для объявление переменных, констант и типов
# identifier - название объявляемого - всегда строка
# type - тип объявляемого - всегда строка и НЕ ХРАНИТ УЗЕЛ ДЕРЕВА (для себя)
# value - для константы - начальное значение
class NodeVariableDeclaration(Node):
    def __init__(self, 
                 identifier = '', 
                 _type = ''):
        self.identifier = identifier
        self.type = _type
class NodeTypeDeclaration(NodeVariableDeclaration):
    pass
class NodeConstantDeclaration(NodeVariableDeclaration):
    def __init__(self,
                 identifier = '',
                 _type = '',
                 expression = None):
        super().__init__(identifier, _type)
        self.expression = expression

# Формальные параметры для класса (Что объявляется при создании)
class NodeSubroutineFormalParams(Node):
    def __init__(self, params = list()):
        self.params = params
    def append(self, param):
        self.params.append(param)
    def extend(self, params):
        self.params.extend(params)
# Класс описания подпрограммы
# identifier - имя
# subroutine_type - тип подпрограммы
# formal_params - передаваемые значения
# declaration_part - блок объявления переменных .типов и т.д.
# statement_part - блок операндов
# is_forward_declaration - объявление подпрограммы заранее (ещё не обрабатывается, но скоро будет)
class NodeSubroutine(Node):
    def __init__(self, 
                 subroutine_type = SubroutineType.PROCEDURE, 
                 identifier = '',
                 type = None,
                 formal_params = NodeSubroutineFormalParams(),
                 declaration_part = NodeDeclarationPart(),
                 statement_part = NodeStatementPart(),
                 is_forward_declaration = False):
        self.identifier = identifier
        self.subroutine_type = subroutine_type
        self.type = type
        self.formal_params = formal_params
        self.declaration_part = declaration_part
        self.statement_part = statement_part
        self.is_forward_declaration = is_forward_declaration

# Класс для объявления границ массива
class NodeArrayRange(Node):
    def __init__(self,
                 left_bound = NodeValue(0, PrimitiveType.BYTE),
                 right_bound = NodeValue(0, PrimitiveType.BYTE)):
        self.left_bound = left_bound
        self.right_bound = right_bound
class NodeArrayType(Node):
    def __init__(self,
                 array_ranges = list(), 
                 _type = None):
        self.array_ranges = array_ranges
        self.type = _type
    def append(self, range : NodeArrayRange):
        self.array_ranges.append(range)
    def __str__(self):
        return hex(id(self))

# Класс для объявления типов (Нужен только для возврата из семантики)
class NodeType(Node):
    def __init__(self, identifier = None, _type = None):
        self.identifier = identifier
        self.type = _type
    def __str__(self):
        return self.identifier

# Класс для объявления переменной
class NodeVariable(Node):
    def __init__(self, 
                 identifier = ''):
        self.identifier = identifier

# Класс для объявления передаваемых параметров в подпрограмму (ещё использу для обращения к массиву)
class NodeCallParams(Node):
    def __init__(self, params = list()):
        self.params = params
    def append(self, param):
        self.params.append(param) 

# Класс унарной операции 
class NodeUnaryOperator(Node):
    def __init__(self, 
                 left, 
                 operation_type = Operator.UNARY_PLUS):
        self.left = left
        self.operation_type = operation_type

# Класс бинарной операции
# left - левое значение
# right - правое значение
# ВАЖНО! При создании ноды присваивания переменной, 
# в left нужно вставить NodeVariable, а в right - что присваивается
# Так: NodeBinaryOperator(NodeVariable('test_name'), <Выражение>, Operator.ASSIGN)
# Аналогично и для операций обращения к массиву (Operator.ARRAY_CALL) и для вызова подпрограмм
class NodeBinaryOperator(Node):
    def __init__(self, left, right, operation_type = Operator.PLUS):
        self.left = left
        self.right = right
        self.operation_type = operation_type

# Далее все класс понятны
# Только одно - в condition должен быть один из четырёх операторов:
# [GREATER, SMALLER, EQUALITY, NONEQUALITY]
# иначе возвразаемый тип не будет BOOLEAN и выкенет ошибку
# expression - не счиьается
class NodeIfStatement(Node):
    def __init__(self, 
                 condition = None, 
                 then_statement_part = NodeStatementPart(), 
                 else_statement_part = NodeStatementPart()):
        self.condition = condition
        self.then_statement_part = then_statement_part
        self.else_statement_part = else_statement_part 
      
class NodeSwitchStatement(Node):
    def __init__(self, 
                 variable = None, 
                 case_blocks = list(),
                 default_block = NodeStatementPart()):
        self.variable = variable
        self.case_blocks = case_blocks
    def append(self, case_block):
        self.case_blocks.append(case_block)
class NodeCaseBlock(Node):
    def __init__(self, 
                 case_list = list(), 
                 statement_part = NodeStatementPart(list())):
        self.case_list = case_list
        self.statement_part = statement_part
    
    def append_case(self, case):
        self.case_list.append( case)
    def append_statement(self, statement):
        self.statement_part.append(statement)

# Класс для цикла while и repeat
class NodeCycleStatement(Node):
    def __init__(self, condition = None, statement_part = NodeStatementPart(list())):
        self.condition = condition
        self.statement_part = statement_part

class NodeWhileStatement(NodeCycleStatement): pass
class NodeRepeatUntilStatement(NodeCycleStatement): pass

class NodeForStatement(Node):
    def __init__(self, 
                 variable = None, 
                 initial_expression = None, 
                 end_expression = None, 
                 statement_part = NodeStatementPart(), 
                 is_increase = False):
        self.variable = variable
        self.initial_expression = initial_expression
        self.end_expression = end_expression
        self.statement_part = statement_part
        self.is_increase = is_increase

class NodeComment(Node):
    def __init__(self, comment):
        self.comment = comment
