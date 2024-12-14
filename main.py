from grl_lexer import GRLLexer


if __name__ == "__main__":
    lexer = GRLLexer()

    for token in lexer.tokenize("DISTANCE FROM my_graph"):
        print('type=%r, value=%r' % (token.type, token.value))
