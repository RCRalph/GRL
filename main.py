from grl_lexer import GRLLexer
from grl_parser import GRLParser


if __name__ == "__main__":
    lexer = GRLLexer()
    parser = GRLParser()

    parser.parse(lexer.tokenize('ADD DIGRAPH my_graph'))
    parser.parse(lexer.tokenize('ADD NODE "meow" my_graph'))
    parser.parse(lexer.tokenize('ADD EDGE "meow" "meow_1" my_graph'))
    parser.parse(lexer.tokenize('SET WEIGHT "meow" "meow_1" 10 my_graph'))
    parser.parse(lexer.tokenize('RM NODE "meow" my_graph'))
    parser.parse(lexer.tokenize('RM GRAPH my_graph'))
