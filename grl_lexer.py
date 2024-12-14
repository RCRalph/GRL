from sly import Lexer

class GRLLexer(Lexer):
    ignore = ' \t'

    keywords = {
        ADD, RM, GET, SET, # type: ignore
        GRAPH, DIGRAPH, NODE, EDGE, WEIGHT, # type: ignore
        DISTANCE_BETWEEN, DISTANCE_FROM, DISTANCE_MATRIX, # type: ignore
        NODES, EDGES, TOPOLOGICAL_SORT, SHORTEST_PATH, NEIGHBORS, # type: ignore
        PRINT, EXPORT, IMPORT # type: ignore
    }

    literals = {
        TRUE, FALSE, # type: ignore
    }

    tokens = {
        *keywords, *literals,
        ID, STRING, NUMBER, # type: ignore
        EQ, NEQ, LT, LEQ, GT, GEQ, # type: ignore
    }

    TRUE = r"TRUE"
    FALSE = r"FALSE"
    STRING = r'"(?:[^"\\]|\\.)*"'
    NUMBER = r"(\d+|\d+\.\d*)"

    EQ = r"=="
    NEQ = r"!="
    LEQ = r"<="
    LT = r"<"
    GEQ = r">="
    GT = r">"

    GRAPH = r"GRAPH"
    DIGRAPH = r"DIGRAPH"
    NODE = r"NODE"
    EDGE = r"EDGE"
    WEIGHT = r"WEIGHT"

    ADD = r"ADD"
    RM = r"RM"
    GET = r"GET"
    SET = r"SET"

    DISTANCE_BETWEEN = r"DISTANCE BETWEEN"
    DISTANCE_FROM = r"DISTANCE FROM"
    DISTANCE_MATRIX = r"DISTANCE MATRIX"

    NODES = r"NODES"
    EDGES = r"EDGES"
    TOPOLOGICAL_SORT = r"TOPOLOGICAL SORT"
    SHORTEST_PATH = r"SHORTEST PATH"
    NEIGHBORS = r"NEIGHBORS"

    FOR = r"FOR"
    COMMA = r","
    OF = r"OF"
    IF = r"IF"
    ELSEIF = r"ELSEIF"
    ELSE = r"ELSE"

    LEFT_PARENT = r"\("
    RIGHT_PARENT = r"\)"
    LEFT_CURLY = r"{"
    RIGHT_CURLY = r"}"

    PRINT = r"PRINT"
    EXPORT = r"EXPORT"
    IMPORT = r"IMPORT"

    ID = r"[_a-z][_a-z0-9]*"
