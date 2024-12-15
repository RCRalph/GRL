import networkx as nx
from sly import Parser

from grl_lexer import GRLLexer

class GRLParser(Parser):
    tokens = GRLLexer.tokens

    def __init__(self):
        self.graphs: dict[str, nx.Graph] = {}

    @_("ADD entity ID") # type: ignore
    def statement(self, production):
        if isinstance(production.entity, nx.Graph):
            if production.ID in self.graphs:
                raise ValueError(f"Graph {production.ID} already exists")

            self.graphs[production.ID] = production.entity
            return

        if production.ID not in self.graphs:
            raise ValueError(f"Graph {production.ID} doesn't exist")

        match production.entity:
            case str() as node:
                self.graphs[production.ID].add_node(node)
            case (start, end):
                self.graphs[production.ID].add_edge(start, end)

    @_("RM entity ID") # type: ignore
    def statement(self, production):
        if isinstance(production.entity, nx.Graph):
            if production.ID in self.graphs:
                raise ValueError(f"Graph {production.ID} already exists")

            del self.graphs[production.ID]
            return

        if production.ID not in self.graphs:
            raise ValueError(f"Graph {production.ID} doesn't exist")

        match production.entity:
            case str() as node:
                self.graphs[production.ID].remove_node(node)
            case (start, end):
                self.graphs[production.ID].remove_edge(start, end)

    @_("GRAPH") # type: ignore
    def entity(self, production) -> str:
        match production.GRAPH:
            case "GRAPH":
                return nx.Graph()
            case "DIGRAPH":
                return nx.DiGraph()
            case _:
                raise ValueError(f"Unknown graph type: {production.entity}")

    @_("NODE STRING") # type: ignore
    def entity(self, production) -> str:
        return production.STRING[1:-1]

    @_("EDGE STRING STRING") # type: ignore
    def entity(self, production) -> tuple[str, str]:
        return production.STRING0, production.STRING1
