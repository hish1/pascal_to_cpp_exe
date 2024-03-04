class Node:
    def __get_class_name(self):
        c = str(self.__class__)
        pos_1 = c.find('.')+1
        pos_2 = c.find("'", pos_1)
        return f"{c[pos_1:pos_2]}"

    def __repr__(self, level=0):
        attrs = self.__dict__
        if len(attrs) == 1 and isinstance(list(attrs.values())[0], list):
            is_sequence = True
        else:
            is_sequence = False
        res = f"{self.__get_class_name()}\n"
        if is_sequence:
            elements = list(attrs.values())[0]
            for el in elements:
                res += '|   ' * level
                res += "|+-"
                res += el.__repr__(level+1)
        else:
            for attr_name in attrs:
                res += '|   ' * level
                res += "|+-"
                if isinstance(attrs[attr_name], Node):
                    res += f"{attr_name}: {attrs[attr_name].__repr__(level+1)}"
                else:
                    res += f"{attr_name}: {attrs[attr_name]}\n"
                    
        return res