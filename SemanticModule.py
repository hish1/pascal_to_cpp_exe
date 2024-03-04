from other.SupportClasses import PrimitiveType, Operator
from other.SupportClasses import NodeType
from other.SupportClasses import NodeVariable, NodeSubroutine, NodeCallParams, NodeArrayType, NodeValue
from other.SupportClasses import NodeBinaryOperator, NodeUnaryOperator
import other.SemanticTools as semantic_tools

from enum import Enum

class UseStateEnum(Enum):
    DECLARED = 0; LINKED = 1; USED = 2

# Класс для хранения объявленных переменных в семантике
class Variable:
    def __init__(self, 
                 identifier = '', 
                 _type = PrimitiveType.UNDEFINED,
                 is_immutable = False):
        self.identifier = identifier
        self.type = _type
        self.IS_IMMUTABLE = is_immutable
        self.use_count = 0

    def __str__(self):
        return self.identifier

class TypeVariable(Variable):
    pass

class SubroutineVariable(Variable):
    def __init__(self, 
                 identifier = '',
                 _type = PrimitiveType.UNDEFINED,
                 formal_params = None):
        super().__init__(identifier, _type)
        self.formal_params = formal_params
        self.use_count = 2**32 - 1

class SemanticModule:

    def __init__(self):
        self.__scope_table = dict()
        self.use_count_score = 0

    def __raise_exception(self, message):
        raise AttributeError(f'Semantic Module error: {message}')

    # Convert scope and identifier to key
    def convert_to_name(self, scope, identifier):
        return f'{".".join(scope)}.{identifier}' if len(scope) != 0 else identifier

    # Add variable or Type to scope
    def __add_to_scope(self, scope, identifier, variable : Variable):
        full_name = self.convert_to_name(scope, identifier)
        if full_name in self.__scope_table:
            self.__raise_exception(f'Try to redefine identifier {name} is same scope .{".".join(scope)}')
        type_iter = variable.type
        while isinstance(type_iter, TypeVariable):
            type_iter.use_count += 1
            type_iter = type_iter.type
        self.__scope_table[full_name] = variable

    def __get_object(self, scope, identifier, prefered_object = None):
        local_scope = scope.copy()
        scope_len_counter = len(scope)
        while scope_len_counter >= 0:
            full_name = self.convert_to_name(local_scope, identifier)
            if full_name in self.__scope_table:
                object = self.__scope_table[full_name]
                if (prefered_object is None) or (isinstance(object, prefered_object)):
                    if self.use_count_score and not isinstance(object, TypeVariable): 
                        object.use_count += 1
                    return object
            if len(local_scope) > 0:
                local_scope.pop()
            scope_len_counter -= 1
        self.__raise_exception(f'Identifier {identifier} doesn\'t declared')

    def get_type(self, scope, type_name):
        return self.__get_object(scope, type_name, TypeVariable)

    def get_variable(self, scope, variable_name):
        obj = self.__get_object(scope, variable_name, Variable)
        if isinstance(obj, SubroutineVariable) or isinstance(obj.type, TypeVariable):
            obj.use_count += 15
        return obj

    def return_value_type(self, value):
        return semantic_tools.get_value_type(value)

    def add_variable(self, scope, identifier, _type, constant = False):
        variable = Variable(identifier, _type, constant)
        self.__add_to_scope(scope, identifier, variable)

    def add_type(self, scope, identifier, original_type : NodeType):
        variable = TypeVariable(identifier, original_type)
        self.__add_to_scope(scope, identifier, variable)

    def add_subroutine(self, scope, identifier, _type, formal_params):
        variable = SubroutineVariable(identifier, _type, formal_params)
        self.__add_to_scope(scope, identifier, variable)

    def get_scope_table(self):
        # not_used = filter(lambda pair: pair[1].state != UseStateEnum.USED, self.__scope_table.items())
        # return list(pair[0] for pair in not_used)
        return self.__scope_table

    def check_type_operation_support(self, condition, oper : Operator, scope = None):
        if PrimitiveType.__contains__(condition):
            predict_type = condition
        elif 'type' in condition.__dict__:
            predict_type = condition.type
        else:
            predict_type = self.predict_condition_type(condition, scope)
        if not oper in predict_type.operators:
            self.__raise_exception(f'Unsupported operator {str(oper)} for type {str(type)}')

    def check_subroutine_call(self, scope, subroutine_name, input_params):
        subroutine = self.get_variable(scope, subroutine_name)
        if not isinstance(subroutine, SubroutineVariable):
            self.__raise_exception(f'Identifier {subroutine.identifier} is not callable')
        formal_params = subroutine.formal_params.params
        call_params = input_params.params
        if len(call_params) != len(formal_params):
            self.__raise_exception(f'Subroute {subroutine.identifier} expect {len(formal_params)} params, got {len(call_params)}')
        for index in range (0, len(formal_params)):
            formal_param = formal_params[index]
            call_param = call_params[index]
            if isinstance(call_param, NodeVariable):
                call_param = self.get_variable(scope, call_param.identifier)
            formal_type = self.predict_condition_type(formal_param, scope)
            call_type = self.predict_condition_type(call_param, scope)
            if not self.check_type_compatibility(formal_type, call_type):
                self.__raise_exception(f'TypeAttribute error: Subroutine {subroutine.identifier} expect {str(formal_type)} in {index}, got {str(call_type)}')
        return True

    def check_array_access(self, scope, variable_name, params):
        params = params.params
        variable = self.get_variable(scope, variable_name)
        variable_type = variable.type
        while isinstance(variable_type, Variable):
            variable_type = variable_type.type
        if not isinstance(variable_type, NodeArrayType):
            self.__raise_exception(f'Identifier {variable_name} is not callable')
        ranges = variable_type.array_ranges
        if len(ranges) != len(params):
            self.__raise_exception(f'{variable.identifier} call expect {len(ranges)} params, got {len(params)}')
        for index in range(0, len(ranges)):
            param = params[index]
            if isinstance(param, NodeVariable):
                param = self.get_variable(scope, param.identifier)
            if not PrimitiveType.is_type_integer(param.type):
                self.__raise_exception(f'Хз что тут написать, однако параметр должен быть исчесляемый у массивов')
            if isinstance(param, NodeValue):
                left_bound = ranges[index].left_bound.value
                right_bound = ranges[index].right_bound.value
                if not int(left_bound) <= int(param.value) <= int(right_bound):
                    self.__raise_exception(f'Array {variable.identifier} index out of bound [{left_bound}..{right_bound}]')
        return True

    def check_type_compatibility(self, type_1, type_2):
        while isinstance(type_1, TypeVariable):
            type_1 = type_1.type
        while isinstance(type_2, TypeVariable):
            type_2 = type_2.type
        if not isinstance(type_1, PrimitiveType) and not isinstance(type_2, PrimitiveType):
            result = type_1 == type_2
        elif isinstance(type_1, NodeArrayType):
            result = (type_1.type, type_2) in semantic_tools.assign_support
        elif isinstance(type_2, NodeArrayType):
            result = (type_2.type, type_1) in semantic_tools.assign_support
        else:
            result = (type_1, type_2) in semantic_tools.assign_support
        return result

    def check_assign(self, scope, variable_name, condition):
        variable = self.get_variable(scope, variable_name)
        if variable.IS_IMMUTABLE:
            self.__raise_exception(f'Try to change value of constant {variable.identifier}')
        variable_type = variable.type
        if isinstance(condition, NodeVariable):
            condition = self.get_variable(scope, condition.identifier)
        condition_type = self.predict_condition_type(condition, scope)
        if not self.check_type_compatibility(variable_type, condition_type):
            self.__raise_exception(f'Identifier type {variable_type} is not compatibility with type {condition_type}')
        return True

    def __get_primitive_type(self, type):
        while not PrimitiveType.__contains__(type):
            type = type.type
        return type

    def predict_condition_type(self, condition, scope = None):
        if 'type' in condition.__dict__:
            return condition.type
        order_result = self.__post_order_condition(condition, scope)
        predict_type = self.__convolute_type_operator_vector(order_result)
        return predict_type

    def convert_to_bool(self, value):
        return semantic_tools.conver_value_to_boolean(value)

    def __post_order_condition(self, top, scope = None):
        stack = [top]
        visited = []
        result = []
        while len(stack) > 0:
            top = stack.pop()
            if isinstance(top, NodeBinaryOperator):
                if top.left not in visited and top.right not in visited:
                    stack.append(top)
                    stack.append(top.right)
                    stack.append(top.left)
                else:
                    visited.append(top)
                    if top.operation_type in Operator.get_value_operators():
                        result.append(top.operation_type)
            elif isinstance(top, NodeUnaryOperator):
                if top.left not in visited:
                    stack.append(top)
                    stack.append(top.left)
                else:
                    visited.append(top)
                    result.append(top.operation_type)
            else:
                visited.append(top)
                if isinstance(top, NodeVariable):
                    variable = self.__get_object(scope, top.identifier)
                    result.append(self.__get_primitive_type(variable.type))
                else:
                    if 'type' in top.__dict__:
                        result.append(self.__get_primitive_type(top.type))
        return result

    def __convolute_type_operator_vector(self, post_order_result):
        while len(post_order_result) != 1:
            index = 0
            while len(post_order_result) > index:
                if isinstance(post_order_result[index], Operator):
                    index += 1  
                else:
                    first = post_order_result[index]
                    if post_order_result[index + 1] == Operator.UNARY_MINUS or post_order_result[index + 1] == Operator.UNARY_PLUS:
                        operator = post_order_result[index + 1]
                        self.check_type_operation_support(first, operator)
                        post_order_result[0] = semantic_tools.cast_types_by_operator(first, None, operator)
                        post_order_result.pop(1)
                        index += 2
                    else:
                        second = post_order_result[index + 1]
                        operator = post_order_result[index + 2]
                        self.check_type_operation_support(first, operator)
                        self.check_type_operation_support(second, operator)
                        post_order_result[0] = semantic_tools.cast_types_by_operator(first, second, operator)
                        post_order_result.pop(1)
                        post_order_result.pop(1)
                        index += 3
        return post_order_result[0]

if __name__ == '__main__':
    t1 = NodeValue('254', PrimitiveType.BYTE)
    t2 = NodeValue('124', PrimitiveType.BYTE)
    node = NodeBinaryOperator(t1, t2, Operator.DIVIDE)
    semantic_module = SemanticModule()
    print(semantic_module.predict_condition_type(node))
 