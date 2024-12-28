import sys
from grl_lexer import GRLLexer
from grl_parser import GRLParser


if __name__ == "__main__":
    lexer = GRLLexer()
    parser = GRLParser()

    if len(sys.argv) == 2:
        with open(sys.argv[1]) as file:
            program = file.read()

        parser.parse(lexer.tokenize(program))
    else:
        while True:
            try:
                statement = input('GLR> ')
                parser.parse(lexer.tokenize(statement))
            except Exception as exc:
                print(exc)
