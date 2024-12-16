from sly import Lexer

class GRLLexer(Lexer):
    ignore = ' \t'

    keywords = {
        ADD, RM, GET, SET, # type: ignore
        GRAPH, NODE, EDGE, WEIGHT, # type: ignore
        DISTANCE, DISTANCE_TYPE, # type: ignore
        NODES, EDGES, TOPOLOGICAL_SORT, SHORTEST_PATH, NEIGHBORS, # type: ignore
        PRINT, EXPORT, IMPORT, # type: ignore
        FOR, COMMA, OF, IF, ELSEIF, ELSE, # type: ignore
    }

    tokens = {
        *keywords,
        BOOLEAN, STRING, NUMBER, # type: ignore
        COMPARATOR, HAS, # type: ignore
        LEFT_PARENT, RIGHT_PARENT, # type: ignore
        LEFT_CURLY, RIGHT_CURLY, # type: ignore
        ID, # type: ignore
    }

    BOOLEAN = r"(TRUE|FALSE)"
    STRING = r'"(?:[^"\\]|\\.)*"'
    NUMBER = r"(\d+|\d+\.\d*)"

    COMPARATOR = r"(==|!=|<=|<|>=|>)"
    HAS = r"HAS"

    GRAPH = r"(DI)?GRAPH"
    NODE = r"NODE"
    EDGE = r"EDGE"
    WEIGHT = r"WEIGHT"

    ADD = r"ADD"
    RM = r"RM"
    GET = r"GET"
    SET = r"SET"

    DISTANCE = r"DISTANCE"
    DISTANCE_TYPE = r"(BETWEEN|FROM|MATRIX)"

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
