from sly import Lexer

class GRLLexer(Lexer):
    ignore = ' \t'

    keywords = {
        STR, NUM, BOOL, # type: ignore
        ADD, RM, GET, SET, IS, # type: ignore
        GRAPH_TYPE, NODE, EDGE, WEIGHT, LENGTH, # type: ignore
        DISTANCE, BETWEEN, FROM, MATRIX, DFS, BFS, # type: ignore
        NODES, EDGES, TOPOLOGICAL_SORT, SHORTEST_PATH, NEIGHBORS, # type: ignore
        DRAW, PRINT, EXPORT, IMPORT, EXIT, RUN, # type: ignore
        FOR, OF, IF, ELSEIF, ELSE, # type: ignore
        HAS, EXISTS, COUNT, # type: ignore
    }

    tokens = {
        *keywords,
        BOOLEAN, STRING, NUMBER, # type: ignore
        PLUS, MINUS, MULTIPLY, DIVIDE, POWER, # type: ignore
        LOGICAL_NOT, LOGICAL_AND, LOGICAL_OR, LOGICAL_XOR, LOGICAL_IMPLIES, # type: ignore
        COMPARATOR,  # type: ignore
        LEFT_CURLY, RIGHT_CURLY, # type: ignore
        LEFT_PARENT, RIGHT_PARENT, # type: ignore
        COMMA, LINE_SEPARATOR, # type: ignore
        ID, # type: ignore
    }

    BOOLEAN = r"(TRUE|FALSE)"
    STRING = r'"(?:[^"\\]|\\.)*"'
    NUMBER = r"-?\d+(\.\d*)?"

    STR = r"STR"
    NUM = r"NUM"
    BOOL = r"BOOL"

    COMPARATOR = r"(==|!=|<=|<|>=|>)"
    HAS = r"HAS"
    EXISTS = r"EXISTS"
    COUNT = r"COUNT"

    POWER = r"\*\*"
    PLUS = r"\+"
    MINUS = r"\-"
    MULTIPLY = r"\*"
    DIVIDE = r"\/"

    LOGICAL_NOT = r"NOT"
    LOGICAL_AND = r"AND"
    LOGICAL_OR = r"OR"
    LOGICAL_XOR = r"XOR"
    LOGICAL_IMPLIES = r"=>"

    NODES = r"NODES"
    EDGES = r"EDGES"
    TOPOLOGICAL_SORT = r"TOPOLOGICAL SORT"
    SHORTEST_PATH = r"SHORTEST PATH"
    NEIGHBORS = r"NEIGHBORS"

    GRAPH_TYPE = r"(DI)?GRAPH"
    NODE = r"NODE"
    EDGE = r"EDGE"
    WEIGHT = r"WEIGHT"
    LENGTH = r"LENGTH"

    ADD = r"ADD"
    RM = r"RM"
    GET = r"GET"
    SET = r"SET"
    IS = r"IS"

    DISTANCE = r"DISTANCE"
    BETWEEN = r"BETWEEN"
    FROM = r"FROM"
    MATRIX = r"MATRIX"
    DFS = r"DFS"
    BFS = r"BFS"

    FOR = r"FOR"
    OF = r"OF"
    IF = r"IF"
    ELSEIF = r"ELSEIF"
    ELSE = r"ELSE"

    LEFT_CURLY = r"{"
    RIGHT_CURLY = r"}"
    LEFT_PARENT = r"\("
    RIGHT_PARENT = r"\)"
    LINE_SEPARATOR = r"[;\n]"
    COMMA = r","

    DRAW = r"DRAW"
    PRINT = r"PRINT"
    RUN = r"RUN"
    EXPORT = r"EXPORT"
    IMPORT = r"IMPORT"
    EXIT = r"EXIT"

    ID = r"[_a-z][_a-z0-9]*"
