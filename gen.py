import other.SupportClasses as s
import Parser as p

type_map = {
    'BYTE' : 'unsigned char',
    'WORD' : 'unsigned short',
    'LONGWORD' : 'unsigned int',
    'UINT64' : 'unsigned long long',
    'SHORTINT' : 'signed char',
    'SMALLINT' : 'short',
    'INTEGER' : 'int',
    'INT64' : 'long long',
    'REAL' : 'float',
    'DOUBLE' : 'double'
}

class Gen:
    l = "   "
    types = []
    code = ""

    def __init__(self, parser: p.NodeProgram):
        self.code = self.generate(parser)
        self.current_function_variable = None

    def array_type_declaration(self, ar):
        c = self.type(ar)

        for i in ar.array_ranges:
            c += f"[{int(i.right_bound.value) - int(i.left_bound.value)}]"

        return c

    def array_type(self, ar):
        c = f"{self.type(ar.type)}"

        for i in ar.type.array_ranges:
            c += f"[{int(i.right_bound.value) - int(i.left_bound.value)}]"

        return c

    def type(self, t):
        if t.type in self.types:
            c = t.type
        elif t.type in type_map:
            c = type_map[t.type]
        elif t.type.lower() == "boolean":
            c = "bool"
        else:
            c = t.type.lower()

        return c

    def is_string(self, b):
        c = ""

        if b.type == "CHAR" or b.type == "STRING":
            c += f"'{b.value}'"
        else:
            c += f"{b.value}"

        return c

    def condition(self, node):
        c = ""

        if node.operation_type == "SMALLER":
            c = f" < "
        elif node.operation_type == "GREATER":
            c = f" > "
        elif node.operation_type == "GREATER_OR_EQUAL":
            c = f" >= "
        elif node.operation_type == "SMALLER_OR_EQUAL":
            c = f" <= "
        elif node.operation_type == "EQUALITY":
            c = f" == "
        elif node.operation_type == "NONEQUALITY":
            c = f" != "
        elif node.operation_type == "PLUS":
            c = f" + "
        elif node.operation_type == "MINUS":
            c = f" - "
        elif node.operation_type == "MULTIPLY":
            c = f" * "
        elif node.operation_type == "DIVIDE":
            c = f" / "
        elif node.operation_type == "NOD":
            c = f" % "
        elif node.operation_type == "ASSIGN":
            c = f" = "

        return c

    def unary_condition(self, node):
        c = ""

        if node.operation_type == "UNARY_MINUS":
            c += f" -"
        elif node.operation_type == "UNARY_PLUS":
            c += f" +"

        return c

    def if_statement(self, node, level):
        c = f"if ({self.bin_operation(node.condition)})" + " {\n"

        c += self.statement_part(node.then_statement_part, level+1)
        if len(node.else_statement_part.statements) > 0:
            c += "else {\n" + self.statement_part(node.else_statement_part, level+1)

        return c
    
    def while_statement(self, node, level):
        c = f"while ({self.bin_operation(node.condition)}) " + "{\n"
        c += f"{self.statement_part(node.statement_part, level+1)}"

        return c

    def repeat_statement(self, node, level):
        c = "do {\n"

        c += self.statement_part(node.statement_part, level+1)[:-1]
        c += f" while ({self.bin_operation(node.condition)});\n"

        return c + "\n"

    def for_statement(self, f, level):
        c = ""
        str = ""

        if isinstance(f.initial_expression, s.NodeVariable):
            str = f.initial_expression.identifier
        elif isinstance(f.initial_expression, s.NodeValue):
            str = f.initial_expression.value
        cond = f.variable.identifier + " = " + str + "; "

        if isinstance(f.end_expression, s.NodeVariable):
            str = f.end_expression.identifier
        elif isinstance(f.end_expression, s.NodeValue):
            str = f.end_expression.value
        cond += f.variable.identifier + " < " + str + "; "

        cond += f.variable.identifier + "++"
        c += "for (" + cond + ") {\n"

        c += self.statement_part(f.statement_part, level+1)

        return c

    def switch_condition(self, sw, level):
        c = f"switch ({sw.variable.identifier}) " + "{\n"
        sw.case_blocks.pop()

        for i in sw.case_blocks:
            str = ""
            for j in range(level):
                c += self.l
            for j in i.case_list:
                str += f"{self.is_string(j)}, "
            c += f"case {str[:-2]}:\n"
            c += self.statement_part(i.statement_part, level+1)[:-3]
        if sw.default_block is not None:
            for j in range(level):
                c += self.l
            c += "default:\n" + self.statement_part(sw.default_block, level+1)
        # c += "}\n"

        return c

    def bin_operation(self, b):
        c = ""

        if isinstance(b, s.NodeUnaryOperator):
            c += self.unary_condition(b) + "("

        f = isinstance(b, s.NodeVariable) or isinstance(b, s.NodeValue)
        while not f and b.left is not None:
            c += self.bin_operation(b.left)
            break

        if isinstance(b, s.NodeVariable):
            c += f"{b.identifier}"
        elif isinstance(b, s.NodeValue):
            c += self.is_string(b)
        elif isinstance(b, s.NodeBinaryOperator):
            if b.operation_type == 'ARRAY_CALL':
                for i in b.right.params:
                    if isinstance(i, s.NodeValue):
                        c += f'[{i.value}]'
                    else:
                        c += f"[{i.identifier}]"
            elif b.operation_type == 'SUBROUTINE_CALL':
                c += "("
                for i in b.right.params:
                    c += i.identifier + ", "
                c = c[:-2] + ")"
            else:
                c += self.condition(b)

        if isinstance(b, s.NodeUnaryOperator):
            c += ")"
        else:
            while not f and b.operation_type != 'ARRAY_CALL' and b.operation_type != 'SUBROUTINE_CALL' and b.right is not None:
                c += self.bin_operation(b.right)
                break

        return c

    def statement_part(self, sp, level):
        c = ""
        sp = sp.statements

        for i in sp:
            if not (isinstance(i, p.NodeBinaryOperator)):
                for j in range(level):
                    c += "\n" + self.l
            else:
                for j in range(level):
                    c += self.l
            if (isinstance(i, p.NodeBinaryOperator)):
                bin_operation = self.bin_operation(i)
                c += f"{bin_operation};\n"
            elif (isinstance(i, s.NodeIfStatement)):
                if_statement = self.if_statement(i, level)
                c += f"{if_statement}"
            elif (isinstance(i, s.NodeSwitchStatement)):
                switch = self.switch_condition(i, level)
                c += f"{switch}"
            elif (isinstance(i, s.NodeWhileStatement)):
                while_statement = self.while_statement(i, level)
                c += f"{while_statement}"
            elif (isinstance(i, s.NodeRepeatUntilStatement)):
                repeat_statement = self.repeat_statement(i, level)
                c += f"{repeat_statement}"
            elif (isinstance(i, s.NodeForStatement)):
                for_statement = self.for_statement(i, level)
                c += f"{for_statement}"
        for j in range(level-1):
            c += self.l

        return c + "}\n"

    def var(self, v, level):
        c = ""
        for i in range(level):
            c += self.l
        if isinstance(v.type, s.NodeArrayType):
            c += f"{self.array_type(v)}"
        else:
            c += f"{self.type(v)} {v.identifier}"
        return c

    def subroutine(self, sb):
        if sb.subroutine_type == "PROCEDURE":
            c = f"void {sb.identifier}("
        else:
            c = f"{self.type(sb)} {sb.identifier}("
        for i in sb.formal_params.params:
            c += f"{self.var(i, 0)}, "
            c = c[:-2]
        c += ") {\n"

        for i in sb.declaration_part.declaration_list:
            c += self.var(i, 1) + ";\n"

        self.current_function_variable = sb.identifier

        c += self.statement_part(sb.statement_part, 1)
        c = c[:-3] + "\n"

        if sb.subroutine_type == "FUNCTION":
            c += f"\n{self.l}return {sb.identifier};\n" + "}"
        else:
            c += "}"
        
        return c

    def type_declaration(self, td):
        c = f"using {td.identifier} = "

        if isinstance(td.type, s.NodeArrayType):
            c += f"{self.array_type(td)}"
        else:
            c += self.type(td)
        self.types.append(td.identifier)
        return c + ";\n"

    def global_declaration(self, dp):
        c = ""

        for i in dp.declaration_list:
            if isinstance(i, s.NodeConstantDeclaration):
                c += self.const(i, 0) + ";\n"
            elif isinstance(i, s.NodeTypeDeclaration):
                c += self.type_declaration(i) + "\n"
            elif isinstance(i, s.NodeVariableDeclaration):
                c += self.var(i, 0) + ";\n"
            elif isinstance(i, s.NodeSubroutine):
                c += "\n" + self.subroutine(i) + "\n"

        return c + "\n"

    def const(self, td, level):
        c = "const " + self.var(td, level)
        return c

    def generate(self, parser):
        code = ""

        code += self.global_declaration(parser.global_declaration)

        code += "int main(){\n"
        statement_part = self.statement_part(parser.statement_part, 1)
        code += f"{statement_part}"
        code = code[:-3]

        code += "\n" + self.l + "return 0;\n}"

        return code
