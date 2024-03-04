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
from other.SupportClasses import *
from SemanticModule import SemanticModule, TypeVariable

from typing import final
from typing import abstractmethod
from enum import Enum

class OptimizeChain:

    def __init__(self, 
                 next = None):
        self.__next = None

    @final
    def set_next(self, next):
        self.__next = next

    @final
    def get_next(self):
        return self.__next

    @final
    def process_optimization(self, node_program : NodeProgram) -> NodeProgram:
        result = self._optimize(node_program)
        if self.__next is not None:
            return self.__next.process_optimization(result)
        else:
            return result
    
    @abstractmethod
    def _optimize(self, tree_node : Node) -> Node:
        pass 

class NotUsedVariableOptimize(OptimizeChain):

    def __init__(self, 
                 next = None,
                 semantic_module = None):
        super().__init__(next)
        self.__semantic_module = semantic_module
        self.__current_scope = list()

    def set_semantic_module(self, module):
        self.__semantic_module = module
    
    def _optimize(self, tree_node : NodeProgram) -> Node:
        scope_table = self.__semantic_module.get_scope_table().copy()
        self.__scope_table = scope_table
        while True:
            unused_variables = dict(filter(lambda pair: pair[1].use_count == 0, scope_table.items()))
            if len(unused_variables) == 0:
                break
            unused_names = [pair[1].identifier for pair in unused_variables.items()]
            declaration = tree_node.global_declaration
            tree_node.global_declaration = self.__cut_declarations(declaration, unused_names)
            statements = tree_node.statement_part
            tree_node.statement_part = self.__cut_statement_part(statements, unused_names)
            for full_name, unused_variable in unused_variables.items():
                type_iter = unused_variable.type
                while isinstance(type_iter, TypeVariable):
                    type_iter.use_count -= 1
                    type_iter = type_iter.type
                del scope_table[full_name]
        return tree_node
        
    def __cut_declarations(self, 
                           declaration_part: NodeDeclarationPart, 
                           unused_names : list[str]):
        filtered_declarations = list()
        for declaration in declaration_part.declaration_list:
            if isinstance(declaration, NodeSubroutine):
                self.__current_scope.append(declaration.identifier)
                subroutine = self.__cut_subroutine(declaration, unused_names)
                self.__current_scope.pop()
                filtered_declarations.append(subroutine)
            else:
                full_name = self.__semantic_module.convert_to_name(self.__current_scope, declaration.identifier)
                if full_name not in unused_names:
                    filtered_declarations.append(declaration)
        return NodeDeclarationPart(filtered_declarations)


    def __cut_subroutine(self, 
                         subroutine : NodeSubroutine, 
                         unused_names : list[str]):
        declaration = subroutine.declaration_part
        subroutine.declaration_part = self.__cut_declarations(declaration, unused_names)
        statements = subroutine.statement_part
        subroutine.statement_part = self.__cut_statement_part(statements, unused_names)
        return subroutine
        
    def __cut_statement_part(self, 
                             statement_part : NodeStatementPart, 
                             unused_names : list[str]):
        filtered_statements = list()
        for statement in statement_part.statements:
            match statement:
                case NodeIfStatement():
                    if statement.then_statement_part:
                        statement.then_statement_part = self.__cut_statement_part(statement.then_statement_part, unused_names)
                    if statement.else_statement_part:
                        statement.else_statement_part = self.__cut_statement_part(statement.else_statement_part, unused_names)
                    filtered_statements.append(statement)
                case NodeCycleStatement():
                    statement.statement_part = self.__cut_statement_part(statement.statement_part, unused_names)
                    filtered_statements.append(statement)
                case NodeForStatement():
                    statement.statement_part = self.__cut_statement_part(statement.statement_part, unused_names)
                    filtered_statements.append(statement)
                case NodeBinaryOperator() | NodeUnaryOperator():
                    if self.__make_post_order_traversal(statement, unused_names):
                        filtered_statements.append(statement)         
        return NodeStatementPart(filtered_statements)

    def __make_post_order_traversal(self, top, unused_names):
        all_variables = []
        stack = [top]
        visited = []
        assign_variable_name = ''
        while len(stack) > 0:
            top = stack.pop()
            if isinstance(top, NodeBinaryOperator):
                if top.operation_type == Operator.ASSIGN:
                    var_iter = top.left
                    while not isinstance(var_iter, NodeVariable):
                        var_iter = var_iter.left
                    assign_variable_name = self.__semantic_module.convert_to_name(self.__current_scope, var_iter.identifier)
                if top.left not in visited and top.right not in visited:
                    stack.append(top)
                    stack.append(top.right)
                    stack.append(top.left)
                else:
                    visited.append(top)
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
                    full_name = self.__semantic_module.convert_to_name(self.__current_scope, top.identifier)
                    all_variables.append(full_name)
        if assign_variable_name in unused_names:
            for variable in all_variables:
                self.__scope_table[variable].use_count -= 1
            return False
        return True