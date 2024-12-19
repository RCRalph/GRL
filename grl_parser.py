import networkx as nx
import matplotlib.pyplot as plt
from sly import Parser

from grl_lexer import GRLLexer

class GRLParser(Parser):
    tokens = GRLLexer.tokens

    precedence = [
        ("nonassoc", "COMPARATOR")
    ]

    def __init__(self):
        self.graphs: dict[str, nx.Graph] = {}

    def _get_graph(self, graph_id: str) -> nx.Graph:
        if graph_id not in self.graphs:
            raise ValueError(f"Graph {graph_id} doesn't exist")

        return self.graphs[graph_id]

    # ----- STATEMENTS -----

    @_("EXIT") # type: ignore
    def statement(self, production):
        exit(0)

    @_("PRINT boolean") # type: ignore
    def statement(self, production):
        print(production.boolean)

    @_("PRINT number") # type: ignore
    def statement(self, production):
        print(production.number)

    @_("PRINT string") # type: ignore
    def statement(self, production):
        print(production.string)

    @_("PRINT ID") # type: ignore
    def statement(self, production):
        graph = self._get_graph(production.ID)
        pos = nx.nx_agraph.graphviz_layout(graph)
        weights = nx.get_edge_attributes(graph, 'weight')

        nx.draw(graph, pos, with_labels=True)
        if any(item != 1 for item in weights):
            nx.draw_networkx_edge_labels(graph, pos, edge_labels=weights)

        plt.show()

    @_("ADD entity ID") # type: ignore
    def statement(self, production):
        if isinstance(production.entity, nx.Graph):
            if production.ID in self.graphs:
                raise ValueError(f"Graph {production.ID} already exists")

            self.graphs[production.ID] = production.entity
            return

        graph = self._get_graph(production.ID)
        match production.entity:
            case str() as node:
                graph.add_node(node)
            case (start, end):
                graph.add_edge(start, end)

    @_("RM entity ID") # type: ignore
    def statement(self, production):
        if isinstance(production.entity, nx.Graph):
            self._get_graph(production.ID)
            del self.graphs[production.ID]
            return

        graph = self._get_graph(production.ID)
        match production.entity:
            case str() as node:
                graph.remove_node(node)
            case (start, end):
                graph.remove_edge(start, end)

    @_("SET WEIGHT OF edge number ID") # type: ignore
    def statement(self, production):
        graph = self._get_graph(production.ID)
        if production.edge not in graph.edges:
            raise ValueError(f"Edge {production.edge} not in graph {production.ID}")

        graph.edges[production.edge]["weight"] = production.number

    # ----- ENTITIES -----

    @_("GRAPH") # type: ignore
    def entity(self, production) -> str:
        match production.GRAPH:
            case "GRAPH":
                return nx.Graph()
            case "DIGRAPH":
                return nx.DiGraph()
            case _:
                raise ValueError(f"Unknown graph type: {production.entity}")

    @_("node") # type: ignore
    def entity(self, production) -> str:
        return production.node

    @_("edge") # type: ignore
    def entity(self, production) -> tuple[str, str]:
        return production.edge

    # ----- GRAPH PROPERTIES -----

    @_("EXISTS ID") # type: ignore
    def boolean(self, production) -> bool:
        return production.ID in self.graphs

    @_("HAS node ID") # type: ignore
    def boolean(self, production) -> bool:
        graph = self._get_graph(production.ID)
        return graph.has_node(production.node)

    @_("HAS edge ID") # type: ignore
    def boolean(self, production) -> bool:
        graph = self._get_graph(production.ID)
        return graph.has_edge(*production.edge)

    @_("GET WEIGHT OF edge ID") # type: ignore
    def number(self, production) -> int | float:
        graph = self._get_graph(production.ID)
        if production.edge not in graph.edges:
            raise ValueError(f"Edge {production.edge} not in graph {production.ID}")

        return graph.edges[production.edge].get("weight", 1)

    # ----- COMPARISONS -----

    @_("comparable COMPARATOR comparable") # type: ignore
    def boolean(self, production) -> bool:
        match production.COMPARATOR:
            case "==":
                return production.comparable0 == production.comparable1
            case "!=":
                return production.comparable0 != production.comparable1
            case "<":
                return production.comparable0 < production.comparable1
            case "<=":
                return production.comparable0 <= production.comparable1
            case ">":
                return production.comparable0 > production.comparable1
            case ">=":
                return production.comparable0 > production.comparable1

    @_("ID") # type: ignore
    def comparable(self, production) -> nx.Graph:
        return self._get_graph(production.ID)

    @_("boolean") # type: ignore
    def comparable(self, production) -> bool:
        return production.boolean

    @_("number") # type: ignore
    def comparable(self, production) -> int | float:
        return production.number

    # ----- LITERALS -----

    @_("NODE string") # type: ignore
    def node(self, production) -> str:
        return production.string

    @_("EDGE string string") # type: ignore
    def edge(self, production) -> tuple[str, str]:
        return production.string0, production.string1

    @_("BOOLEAN") # type: ignore
    def boolean(self, production) -> bool:
        return production.BOOLEAN_LITERAL == "TRUE"

    @_("NUMBER") # type: ignore
    def number(self, production) -> int | float:
        float_value = float(production.NUMBER)
        if float_value.is_integer():
            return int(float_value)

        return float_value

    @_("STRING") # type: ignore
    def string(self, production) -> str:
        return production.STRING[1:-1]
