from grl_lexer import GRLLexer
from grl_parser import GRLParser


if __name__ == "__main__":
    lexer = GRLLexer()
    parser = GRLParser()

    parser.parse(lexer.tokenize('ADD DIGRAPH my_graph'))
    parser.parse(lexer.tokenize('ADD NODE "meow" my_graph'))
    parser.parse(lexer.tokenize('RM NODE "meow" my_graph'))
    parser.parse(lexer.tokenize('RM my_graph'))
