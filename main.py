from grl_lexer import GRLLexer
from grl_parser import GRLParser


if __name__ == "__main__":
    lexer = GRLLexer()
    parser = GRLParser()

    while True:
        try:
            statement = input('GLR> ')
            parser.parse(lexer.tokenize(statement))
        except Exception as exc:
            print(exc)
