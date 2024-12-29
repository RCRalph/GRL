from sly import Lexer

class GRLLexer(Lexer):
    ignore = ' \t'

    keywords = {
        ADD, RM, GET, SET, IS, # type: ignore
        GRAPH_TYPE, NODE, EDGE, WEIGHT, # type: ignore
        DISTANCE, BETWEEN, FROM, MATRIX, # type: ignore
        NODES, EDGES, TOPOLOGICAL_SORT, SHORTEST_PATH, NEIGHBORS, # type: ignore
        DRAW, PRINT, EXPORT, IMPORT, EXIT, RUN, # type: ignore
        FOR, OF, IF, ELSEIF, ELSE, # type: ignore
        HAS, EXISTS, COUNT # type: ignore
    }

    tokens = {
        *keywords,
        BOOLEAN, STRING, NUMBER, # type: ignore
        COMPARATOR,  # type: ignore
        LEFT_CURLY, RIGHT_CURLY, # type: ignore
        COMMA, LINE_SEPARATOR, # type: ignore
        ID, # type: ignore
    }

    BOOLEAN = r"(TRUE|FALSE)"
    STRING = r'"(?:[^"\\]|\\.)*"'
    NUMBER = r"-?(\d+|\d+\.\d*)"

    COMPARATOR = r"(==|!=|<=|<|>=|>)"
    HAS = r"HAS"
    EXISTS = r"EXISTS"
    COUNT = r"COUNT"

    NODES = r"NODES"
    EDGES = r"EDGES"
    TOPOLOGICAL_SORT = r"TOPOLOGICAL SORT"
    SHORTEST_PATH = r"SHORTEST PATH"
    NEIGHBORS = r"NEIGHBORS"

    GRAPH_TYPE = r"(DI)?GRAPH"
    NODE = r"NODE"
    EDGE = r"EDGE"
    WEIGHT = r"WEIGHT"

    ADD = r"ADD"
    RM = r"RM"
    GET = r"GET"
    SET = r"SET"
    IS = r"IS"

    DISTANCE = r"DISTANCE"
    BETWEEN = r"BETWEEN"
    FROM = r"FROM"
    MATRIX = r"MATRIX"

    FOR = r"FOR"
    OF = r"OF"
    IF = r"IF"
    ELSEIF = r"ELSEIF"
    ELSE = r"ELSE"

    LEFT_CURLY = r"{"
    RIGHT_CURLY = r"}"
    LINE_SEPARATOR = r"[;\n]"
    COMMA = r","

    DRAW = r"DRAW"
    PRINT = r"PRINT"
    RUN = r"RUN"
    EXPORT = r"EXPORT"
    IMPORT = r"IMPORT"
    EXIT = r"EXIT"

    ID = r"[_a-z][_a-z0-9]*"
