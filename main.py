from lexer import Lexer
from Parser import Parser
from SemanticModule import SemanticModule
from CodeOptimizationProcessor import CodeOptimizationProcessor as Optimizator
from other.OptimizeChain import NotUsedVariableOptimize as NotUsedChain
from gen import Gen
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget, QMessageBox
import os

Form, Window = uic.loadUiType("qt/Main.ui")
app = QApplication([])
window, form = Window(), Form()
widget = QWidget()
form.setupUi(window)

# Form1, Window1 = uic.loadUiType("qt/Tree.ui")
# window1, form1 = Window(), Form()
# form1.setupUi(window1)

code = ''
pascal = 'pascal.pas'

parser = Parser()
semantic_module = SemanticModule()
optimizator = Optimizator()
optimizator.add_new_chain(NotUsedChain(semantic_module= semantic_module))


def openf():
    file = QFileDialog.getOpenFileName()

    global code
    with open(file[0], 'r') as f:
        code = f.read()
    form.pas_code.setPlainText(code)

    # global pascal
    # with open(pascal, 'w') as f:
    #     f.write(code)
    #     f.flush()
    #     f.close()

    print("Open file")


def trans():
    global code
    if code != '':
        try:
            code = form.pas_code.toPlainText()
            # global pascal
            # with open(pascal, 'w') as f:
            #     f.write(code)
            #     f.flush()
            #     f.close()

            lexer = Lexer(pascal)
            parser.set_lexer(lexer)
            parser.set_semantic_module(semantic_module)
            before = parser.parse()
            # after = optimizator.start_optimization(before)
            gen = Gen(before)
            code = gen.code
            form.cpp_code.setPlainText(code)

        except AttributeError as e:
            error = QMessageBox()
            error.setWindowTitle("Error")
            error.setText(e.args[0])
            error.setIcon(QMessageBox.Icon.Critical)
            error.setStandardButtons(QMessageBox.StandardButton.Ok)

            error.exec()
            form.cpp_code.clear()
    else:
        form.cpp_code.clear()

    print("Translate")


def savef():
    global code
    code = form.cpp_code.toPlainText()

    file = QFileDialog.getSaveFileName()
    with open(file[0]+'.cpp', 'w') as f:
        f.write(code)
        f.flush()
        f.close()

    print("Save file")


def pas_clear():
    form.pas_code.clear()
def cpp_clear():
    form.cpp_code.clear()
def show_tree():
    os.startfile('result.txt')

def main():
    form.open_button.clicked.connect(openf)
    form.translate_button.clicked.connect(trans)
    form.save_button.clicked.connect(savef)
    form.pas_clear.clicked.connect(pas_clear)
    form.cpp_clear.clicked.connect(cpp_clear)
    form.tree_button.clicked.connect(show_tree)

    window.show()
    app.exec()

if __name__ == '__main__':
    main()