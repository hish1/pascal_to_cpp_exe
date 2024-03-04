from other.OptimizeChain import OptimizeChain, NotUsedVariableOptimize
from lexer import Lexer
from Parser import Parser
from SemanticModule import SemanticModule
from other.SupportClasses import NodeProgram

class CodeOptimizationProcessor:
    
    def __init__(self, main_chain : OptimizeChain = None):
        self.__chain_head = main_chain

    def add_new_chain(self, chain : OptimizeChain):
        if self.__chain_head is None:
            self.__chain_head = chain
            return
        iter = self.__chain_head
        while iter.get_next() is not None:
            iter = iter.get_next()
        iter.set_next(chain)

    def start_optimization(self, program_node : NodeProgram) -> NodeProgram:
        return self.__chain_head.process_optimization(program_node)

def write_to_file(file_path, object):
    writer = open(file_path, 'w')
    writer.write(str(object))
    writer.flush()
    writer.close()

if __name__ == '__main__':
    lexer = Lexer(file_path= 'test/test pascal file.pas')
    semantic_module = SemanticModule()
    parser = Parser(lexer)
    parser.set_semantic_module(semantic_module)
    res = parser.parse()
    write_to_file('output/Not optimized program1.txt', res)
    # Цепочка оптимизации
    optimizer1 = NotUsedVariableOptimize()
    optimizer1.set_semantic_module(semantic_module) # Лайфхак с таблицей
    # Оптимизатор кода
    optimize_processor = CodeOptimizationProcessor()
    optimize_processor.add_new_chain(optimizer1)
    optimized_program = optimize_processor.start_optimization(res)
    write_to_file('output/Optimized program1.txt', optimized_program)
