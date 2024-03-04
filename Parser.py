from lexer import Lexer
from other.SupportClasses import *
from SemanticModule import SemanticModule

class Parser:

    def __init__(self, lexer : Lexer = None):
        if lexer:
            self.lexer = lexer
            self.current_token = lexer.get_next_token()
        else:
            self.lexer = None
            self.current_token = 'EOF'
        self.current_scope = list()
        self.__semantic_module = None

    def __next_token(self):
        self.current_token = self.lexer.get_next_token()
    
    def __expect(self, _expected):
        if self.current_token[0] != _expected:
            self.__raise_exception(f'Unexpected token: expect {_expected}: got {self.current_token[0]}')
        return True

    def __expect_and_move(self, _expected):
        self.__expect(_expected)
        self.__next_token()
        return True
    
    def __check(self, _expected):
        return self.current_token[0] == _expected
    
    def __check_all(self, _expected_list):
        return self.current_token[0] in _expected_list

    def __pop_token(self):
        token = self.current_token[0]
        self.__next_token()
        return token

    def __pop_value(self):
        identifier = self.current_token[1]
        self.__next_token()
        return identifier

    def __get_current_scope_str(self):
        return '.'.join(self.current_scope)

    def __raise_exception(self, message):
        raise AttributeError(f'Parse error: {message}')

    def set_semantic_module(self, semantic_module):
        self.__semantic_module = semantic_module

    def set_lexer(self, lexer):
        self.lexer = lexer
        self.current_token = lexer.get_next_token()
    
    def parse(self):
        if not self.__check('EOF'):
            main_node = self._parse_prog()
        else:
            main_node = MainNode()
        return main_node
    
    def _parse_prog(self):
        node = NodeProgram()
        if self.__check('PROGRAM'):
            self.__next_token()
            node.identifier = self.__pop_value()
            self.__expect_and_move('SEMICOLON')
        node.global_declaration = self._parse_declaration_part()
        self.current_scope.append(node.identifier)
        node.statement_part = self.__parse_STATEMENT_BLOCK()
        self.__expect_and_move('DOT')
        return node

    def _parse_declaration_part(self):
        declaration_list = list()
        while not self.__check('BEGIN'):
            match self.current_token[0]:
                case 'VAR':
                    self.__next_token()
                    while self.__check('IDENTIFIER'):
                        declaration_list.extend(self.__parse_VAR_statement())
                        self.__expect_and_move('SEMICOLON')
                case 'TYPE':
                    self.__next_token()
                    while self.__check('IDENTIFIER'):
                        declaration_list.append(self.__parse_TYPE_statement())
                        self.__expect_and_move('SEMICOLON')
                case 'CONST':
                    self.__next_token()
                    while self.__check('IDENTIFIER'):
                        declaration_list.append(self.__parse_CONST_statement())
                        self.__expect_and_move('SEMICOLON')
                case 'PROCEDURE' | 'FUNCTION':
                    declaration_list.append(self.__parse_SUBROUTINE())
                case _:
                    self.__raise_exception('Impossible to parse declaration part. Infinity loop')
        return NodeDeclarationPart(declaration_list)

    # Parsing VAR declaration
    def __parse_VAR_statement(self):
        identifiers = []
        while not self.__check('COLON'):
            self.__expect('IDENTIFIER')
            identifiers.append(self.__pop_value())
            if self.__check('COMMA'):
                self.__next_token()
        self.__next_token()
        _type = self.__parse_type()
        if self.__check('ASSIGN'):
            raise Error('Not implement Variable assign')
        for identifier in identifiers:
            self.__semantic_module.add_variable(self.current_scope, identifier, _type)
        if not isinstance(_type, NodeArrayType):
            _type = str(_type)
        variables = [NodeVariableDeclaration(identifier, _type) for identifier in identifiers]
        # Add declaration to scope
        return variables
    
    # Parsing CONST declaration
    def __parse_CONST_statement(self):
        node = NodeConstantDeclaration()
        self.__expect('IDENTIFIER')
        node.identifier = self.__pop_value()
        self.__expect_and_move('EQUALITY')
        node.expression = self.__parse_CONDITION()
        node.type = self.__semantic_module.predict_condition_type(node.expression, self.current_scope)
        self.__semantic_module.add_variable(self.current_scope, node.identifier, node.type, True)
        if not isinstance(node.type, NodeArrayType):
            node.type = str(node.type)
        return node

    # Parsing TYPE declaration
    def __parse_TYPE_statement(self):
        node = NodeTypeDeclaration()
        self.__expect('IDENTIFIER')
        node.identifier = self.__pop_value()
        self.__expect_and_move('EQUALITY')
        node.type = self.__parse_type()
        self.__semantic_module.add_type(self.current_scope, node.identifier, node.type)
        if not isinstance(node.type, NodeArrayType):
            node.type = str(node.type)
        else:
            node.type.type = str(node.type.type)
        return node

    def __parse_SUBROUTINE(self):
        node = NodeSubroutine()
        node.subroutine_type = SubroutineType(self.__pop_token())
        self.__expect('IDENTIFIER')
        node.identifier = self.__pop_value()
        self.__expect_and_move('LPAREN')
        self.current_scope.append(node.identifier)
        node.formal_params = self.__parse_SUBROUTINE_FORMAL_PARAMS()
        self.__expect_and_move('RPAREN')
        if node.subroutine_type == SubroutineType.FUNCTION:
            self.__expect_and_move('COLON')
            node.type = self.__parse_type()
        else:
            node.type = PrimitiveType.UNDEFINED
        self.__semantic_module.add_subroutine(self.current_scope[:-1], node.identifier, node.type, node.formal_params)
        if not isinstance(node.type, NodeArrayType):
            node.type = str(node.type)
        self.__expect_and_move('SEMICOLON')
        if self.__check('FORWARD'):
            self.__next_token()
            node.is_forward_declaration = True
        else:
            node.declaration_part = self._parse_declaration_part()
            self.__expect('BEGIN')
            node.statement_part = self.__parse_STATEMENT_BLOCK()
            self.__expect_and_move('SEMICOLON')
        self.current_scope.pop()
        return node

    def __parse_SUBROUTINE_FORMAL_PARAMS(self):
        node = NodeSubroutineFormalParams(list())
        while not self.__check('RPAREN'):
            node.extend(self.__parse_VAR_statement())
            if self.__check('COMMA'):
                self.__expect_and_move('RPAREN') # TODO убрать костыль
            if self.__check('SEMICOLON'):
                self.__next_token()
        return node
            
    def __parse_type(self):
        if self.__check('ARRAY'):
            self.__next_token()
            return self.__parse_ARRAY_TYPE()
        elif self.__check('RECORD'):
            self.__next_token()
            raise NotImplementedError('ИМПЛЕМЕНТИРУЙ RECORD')
        elif PrimitiveType.__contains__(self.current_token[0]):
            return PrimitiveType[self.__pop_token()]
        else:
            self.__expect('IDENTIFIER')
            custom_type = self.__pop_value()
            return self.__semantic_module.get_type(self.current_scope, custom_type)
    
    def __parse_ARRAY_TYPE(self):
        node = NodeArrayType(array_ranges = list())
        self.__expect_and_move('LBR')
        while not self.__check('RBR'):
            array_range = NodeArrayRange()
            array_range.left_bound = self.__parse_FACTOR()
            self.__expect_and_move('ARRDOT')
            array_range.right_bound = self.__parse_FACTOR()
            if self.__check('COMMA'):
                self.__next_token()
            node.append(array_range)            
        self.__next_token()
        self.__expect_and_move('OF')
        node.type = self.__parse_type()
        return node
    
    # Parsing condition expression
    def __parse_CONDITION(self):
        left = self.__parse_EXPRESSION()
        while self.__check_all(Operator.get_condition_operators()):
            operator = Operator(self.__pop_token())
            right = self.__parse_EXPRESSION()
            left = NodeBinaryOperator(left, right, operator)
        return left

    # Prasing expression
    def __parse_EXPRESSION(self):
        left = self.__parse_TERM()
        while self.__check_all(('PLUS', 'MINUS', 'OR', 'XOR')):
            operator = Operator(self.__pop_token())
            right = self.__parse_TERM()
            left = NodeBinaryOperator(left, right, operator)
        return left

    # Parsing term
    def __parse_TERM(self):
        left = self.__parse_FACTOR()
        while self.__check_all(('MULTIPLY', 'DIVIDE','DIV', 'MOD', 'AND', 'SHL', 'SHR')):
            operator = Operator(self.__pop_token())
            right = self.__parse_FACTOR()
            left = NodeBinaryOperator(left, right, operator)
        return left

    # Parsing factor
    def __parse_FACTOR(self):
        match self.current_token[0]:
            case 'NUMBER':
                possible_number = self.__pop_value()
                _type = self.__semantic_module.return_value_type(possible_number)
                return NodeValue(possible_number, _type)
            case 'STRING_VAL':
                return NodeValue(self.__pop_value(), PrimitiveType.STRING)
            case 'CHAR_VAL':
                return NodeValue(self.__pop_value(), PrimitiveType.CHAR)
            case 'TRUE' | 'FALSE':
                return NodeValue(self.__pop_value(), PrimitiveType.BOOLEAN)
            case 'LPAREN':
                self.__next_token()
                condition = self.__parse_CONDITION()
                self.__expect_and_move('RPAREN')
                return condition
            case 'MINUS' | 'PLUS' | 'NOT':
                return self.__parse_UNARY_OPERATOR()
            case _:
                self.__expect('IDENTIFIER')
                return self.__parse_IDENTIFIER_STATEMENT()

    def __parse_UNARY_OPERATOR(self):
        operator = Operator[self.__pop_token()]
        factor = self.__parse_FACTOR()
        match operator:
            case Operator.PLUS:
                self.__semantic_module.check_type_operation_support(factor, Operator.UNARY_PLUS, self.current_scope)
                node = factor
            case Operator.MINUS:
                if isinstance(factor, NodeValue):
                    self.__semantic_module.check_type_operation_support(factor, Operator.UNARY_MINUS)
                    factor.value = '-' + factor.value
                    factor.type = self.__semantic_module.return_value_type(factor.value)
                    node = factor
                else:
                    node = NodeUnaryOperator(factor, Operator.UNARY_MINUS)
            case Operator.NOT:
                if isinstance(factor, NodeValue):
                    new_value = not self.__semantic_module.convert_to_bool(factor.value)
                    node = NodeValue(str(new_value), PrimitiveType.BOOLEAN)
                else:
                    node = NodeUnaryOperator(factor, Operator.NOT)
        return node

    # Parinsg variable or Subroutine/array call
    def __parse_IDENTIFIER_STATEMENT(self):    
        self.__expect('IDENTIFIER')
        left = NodeVariable(self.__pop_value())
        # Проверка на существование переменной
        self.__semantic_module.get_variable(self.current_scope, left.identifier)
        while self.__check_all(('ASSIGN', 'LPAREN', 'LBR', 'DOT')):
            match self.current_token[0]:
                case 'ASSIGN':
                    self.__next_token()
                    self.__semantic_module.use_count_score += 1
                    right = self.__parse_CONDITION()
                    self.__semantic_module.use_count_score -= 1
                    variable = left
                    while not isinstance(variable, NodeVariable):
                        variable = variable.left
                    self.__semantic_module.check_assign(self.current_scope, variable.identifier, right)
                    left = NodeBinaryOperator(left, right, Operator.ASSIGN)
                case 'LPAREN':
                    self.__next_token()
                    self.__semantic_module.use_count_score += 1
                    right = self.__parse_SUBROUTINE_CALL_PARAMS()
                    self.__semantic_module.use_count_score -= 1
                    self.__semantic_module.check_subroutine_call(self.current_scope, left.identifier, right)
                    left = NodeBinaryOperator(left, right, Operator.SUBROUTINE_CALL)
                case 'LBR':
                    self.__next_token()
                    self.__semantic_module.use_count_score += 1
                    right = self.__parse_ARRAY_CALL()
                    self.__semantic_module.use_count_score -= 1
                    self.__semantic_module.check_array_access(self.current_scope, left.identifier, right)
                    left = NodeBinaryOperator(left, right, Operator.ARRAY_CALL)
                case 'DOT':
                    raise NotImplementedError('ИМПЛЕМЕНТИРУЙ ОБРАЩЕНИЕ К ОБЪЕКТУ')
        return left

    # Parsing subroution call params
    def __parse_SUBROUTINE_CALL_PARAMS(self):
        node = NodeCallParams(list())
        self.__semantic_module.use_count_score += 1
        while not self.__check('RPAREN'):
            node.append(self.__parse_CONDITION())
            if self.__check('COMMA'):
                self.__next_token()
        self.__semantic_module.use_count_score -= 1
        self.__next_token()
        return node

    def __parse_ARRAY_CALL(self):
        node = NodeCallParams(list())
        self.__semantic_module.use_count_score += 1
        while not self.__check('RBR'):
            node.append(self.__parse_EXPRESSION())
            if self.__check('COMMA'):
                self.__next_token()
        self.__semantic_module.use_count_score -= 1
        self.__next_token()
        return node

    # Parsing statement block
    def __parse_STATEMENT_BLOCK(self):
        statement_block = NodeStatementPart(list())
        if self.__check('BEGIN'):
            self.__next_token()
            while not self.__check('END'):
                statement_block.append(self.__parse_STATEMENT())
                if self.__check('SEMICOLON'):
                    self.__next_token()
                else:
                    self.__expect('END')
            self.__next_token()
        else:
            statement_block.append(self.__parse_STATEMENT())
        return statement_block

    def __parse_STATEMENT(self):
        match self.current_token[0]:
            case 'LCOM':
                self.__next_token()
                pass
            case 'IF':
                self.__next_token()
                node = self.__parse_IF_STATEMENT()
            case 'CASE':
                self.__next_token()
                node = self.__parse_CASE_STATEMENT()
            case 'FOR':
                self.__next_token()
                node = self.__parse_FOR_STATEMENT()
            case 'WHILE':
                self.__next_token()
                node = self.__parse_WHILE_STATEMENT()
            case 'REPEAT':
                self.__next_token()
                node = self.__parse_REPEAT_STATEMENT()
            case _: 
                node = self.__parse_IDENTIFIER_STATEMENT()
        return node

    def __parse_IF_STATEMENT(self):
        self.__semantic_module.use_count_score += 1
        node = NodeIfStatement()
        node.condition = self.__parse_CONDITION()
        self.__expect_and_move('THEN')
        self.__semantic_module.use_count_score -= 1
        node.then_statement_part = self.__parse_STATEMENT_BLOCK()
        if self.__check('ELSE'):
            self.__next_token()
            node.else_statement_part = self.__parse_STATEMENT_BLOCK()
        return node

    def __parse_CASE_STATEMENT(self):
        node = NodeSwitchStatement(None, list())
        self.__expect('IDENTIFIER')
        node.variable = NodeVariable(self.__pop_value())
        self.__expect_and_move('OF')
        while not self.__check('END'):
            if self.__check('ELSE'):
                self.__next_token()
                node.default_block = self.__parse_STATEMENT_BLOCK()
            else:
                case_block = NodeCaseBlock(list(), None)
                while not self.__check('COLON'):
                    case_block.append_case(self.__parse_EXPRESSION())
                    if self.__check('COMMA'):
                        self.__next_token()
                self.__next_token()
                case_block.statement_part = self.__parse_STATEMENT_BLOCK()
            self.__expect_and_move('SEMICOLON')
            node.append(case_block)
        self.__next_token()
        return node

    def __parse_FOR_STATEMENT(self):
        self.__semantic_module.use_count_score += 1
        node = NodeForStatement()
        self.__expect('IDENTIFIER')
        node.variable = NodeVariable(self.__pop_value())
        self.__semantic_module.get_variable(self.current_scope, node.variable.identifier)
        if self.__check('ASSIGN'):
            self.__next_token()
            expression = self.__parse_EXPRESSION()
            self.__semantic_module.check_assign(self.current_scope, node.variable.identifier, expression)
            node.initial_expression = expression
        self.__expect_and_move('TO')
        node.end_expression = self.__parse_EXPRESSION()
        self.__semantic_module.use_count_score -= 1
        self.__expect_and_move('DO')
        node.statement_part = self.__parse_STATEMENT_BLOCK()
        return node

    def __parse_WHILE_STATEMENT(self):
        self.__semantic_module.use_count_score += 1
        node = NodeWhileStatement()
        node.condition = self.__parse_CONDITION()
        self.__semantic_module.use_count_score -= 1
        self.__expect_and_move('DO')
        node.statement_part = self.__parse_STATEMENT_BLOCK()
        return node       

    def __parse_REPEAT_STATEMENT(self):
        node = NodeRepeatUntilStatement(None, NodeStatementPart(list()))
        while not self.__check('UNTIL'):
            node.statement_part.append(self.__parse_STATEMENT())
            self.__expect_and_move('SEMICOLON')
        self.__next_token()
        self.__semantic_module.use_count_score += 1
        node.condition = self.__parse_CONDITION()
        self.__semantic_module.use_count_score -= 1
        return node
            
if __name__ == '__main__':
    lexer = Lexer(file_path= 'test/test pascal file.pas')
    parser = Parser(lexer)
    semantic_module = SemanticModule()
    parser.set_semantic_module(semantic_module)
    res = parser.parse()
    writer = open('output/parser.txt', 'w')
    writer.write(str(res))
    writer.flush()
    writer.close()