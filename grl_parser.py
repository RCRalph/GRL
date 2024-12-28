from typing import Any
import networkx as nx
import matplotlib.pyplot as plt
from sly import Parser

from parse_tree_node import ParseTreeNode
from grl_lexer import GRLLexer


class GRLParser(Parser):
    tokens = GRLLexer.tokens

    precedence = [
        ("nonassoc", "COMPARATOR"),
        ('right', 'PRINT'),
    ]

    def __init__(self):
        self.variables: dict[str, Any] = {}

    def _get_variable(self, variable_name: str) -> Any:
        if variable_name not in self.variables:
            raise ValueError(f"Variable {variable_name} doesn't exist")

        return self.variables[variable_name]

    def _get_graph(self, graph_id: str) -> nx.Graph:
        if graph_id not in self.variables:
            raise ValueError(f"Graph {graph_id} doesn't exist")

        if isinstance(variable := self.variables[graph_id], nx.Graph):
            return variable

        raise TypeError(f"Variable {graph_id} is not a graph")

    @_("statement_sequence") # type: ignore
    def program(self, production):
        statement_sequence: list[ParseTreeNode[None]] = production.statement_sequence
        for statement in statement_sequence:
            statement.evaluate()

    # ----- ITERATION -----

    @_("FOR ID OF single_iterator LEFT_CURLY statement_sequence RIGHT_CURLY") # type: ignore
    def statement(self, production):
        def evaluator(iterator_id: str, single_iterator: list[Any], statement_sequence: list[ParseTreeNode[None]]):
            for item in single_iterator:
                self.variables[iterator_id] = item
                for statement in statement_sequence:
                    statement.evaluate()

            del self.variables[iterator_id]

        return ParseTreeNode(
            evaluator,
            production.ID, production.single_iterator, production.statement_sequence
        )

    @_("NODES ID") # type: ignore
    def single_iterator(self, production):
        return ParseTreeNode(
            lambda graph_id: [
                str(item)
                for item in self._get_graph(graph_id).nodes
            ],
            production.ID
        )

    @_("TOPOLOGICAL_SORT ID") # type: ignore
    def single_iterator(self, production):
        return ParseTreeNode(
            lambda graph_id: [
                str(item)
                for item in nx.topological_sort(self._get_graph(graph_id))
            ],
            production.ID
        )

    @_("SHORTEST_PATH edge ID") # type: ignore
    def single_iterator(self, production):
        def evaluator(graph_id: str, edge: tuple[str, str]):
            graph = self._get_graph(graph_id)
            has_negative_weights = any(
                graph.get_edge_data(source, dest).get("weight", 1) < 0
                for source, dest in graph.edges
            )

            return [
                str(item)
                for item in nx.shortest_path(
                    graph,
                    edge[0],
                    edge[1],
                    "weight",
                    "bellman-ford" if has_negative_weights else "dijkstra"
                )
            ]

        return ParseTreeNode(evaluator, production.ID, production.edge)

    @_("NEIGHBORS node ID") # type: ignore
    def single_iterator(self, production):
        return ParseTreeNode(
            lambda graph_id, node: [
                str(item)
                for item in self._get_graph(graph_id).neighbors(node)
            ],
            production.ID, production.node
        )

    # ----- STATEMENTS -----

    @_("statement { LINE_SEPARATOR statement }") # type: ignore
    def statement_sequence(self, production) -> list[ParseTreeNode[None]]:
        return [production.statement0] + production.statement1

    @_("") # type: ignore
    def statement(self, production) -> list[ParseTreeNode[None]]:
        return ParseTreeNode(lambda: None)

    @_("EXIT") # type: ignore
    def statement(self, production):
        return ParseTreeNode(exit, 0)

    @_("PRINT boolean") # type: ignore
    def statement(self, production):
        return ParseTreeNode(
            lambda x: print(str(x).upper()), production.boolean
        )

    @_("PRINT number") # type: ignore
    def statement(self, production):
        return ParseTreeNode(print, production.number)

    @_("PRINT string") # type: ignore
    def statement(self, production):
        return ParseTreeNode(print, production.string)

    @_("PRINT ID") # type: ignore
    def statement(self, production):
        return ParseTreeNode(
            lambda x: print(self._get_variable(x)),
            production.ID
        )

    @_("DRAW ID") # type: ignore
    def statement(self, production):
        def evaluator(graph_id: str):
            graph = self._get_graph(graph_id)
            pos = nx.nx_agraph.graphviz_layout(graph)
            weights = nx.get_edge_attributes(graph, 'weight')

            nx.draw(graph, pos, with_labels=True)
            if any(item != 1 for item in weights):
                nx.draw_networkx_edge_labels(graph, pos, edge_labels=weights)

            plt.show()

        return ParseTreeNode(evaluator, production.ID)

    @_("ADD entity ID") # type: ignore
    def statement(self, production):
        def evaluator(graph_id: str, entity: nx.Graph | str | tuple[str, str]):
            if isinstance(entity, nx.Graph):
                if graph_id in self.variables:
                    raise ValueError(f"Entity {graph_id} already exists")

                self.variables[graph_id] = entity
                return

            graph = self._get_graph(graph_id)
            match entity:
                case str() as node:
                    graph.add_node(node)
                case (source, dest):
                    graph.add_edge(source, dest)
                case _:
                    raise ValueError(f"Unknown entity: {entity}")

        return ParseTreeNode(evaluator, production.ID, production.entity)

    @_("RM entity ID") # type: ignore
    def statement(self, production):
        def evaluator(graph_id: str, entity: nx.Graph | str | tuple[str, str]):
            graph = self._get_graph(graph_id)
            if isinstance(entity, nx.Graph):
                del self.variables[graph_id]
                return

            match entity:
                case str() as node:
                    graph.remove_node(node)
                case (source, dest):
                    graph.remove_edge(source, dest)
                case _:
                    raise ValueError(f"Unknown entity: {entity}")

        return ParseTreeNode(evaluator, production.ID, production.entity)

    @_("SET WEIGHT OF EDGE edge number ID") # type: ignore
    def statement(self, production):
        def evaluator(graph_id: str, edge: tuple[str, str], weight: int | float):
            graph = self._get_graph(graph_id)
            if not graph.has_edge(*edge):
                raise ValueError(f"Edge {edge} not in graph {graph_id}")

            graph.edges[edge]["weight"] = weight

        return ParseTreeNode(
            evaluator, production.ID, production.edge, production.number
        )

    # ----- ENTITIES -----

    @_("GRAPH_TYPE") # type: ignore
    def entity(self, production):
        def evaluator(graph_type: str):
            match graph_type:
                case "GRAPH":
                    return nx.Graph()
                case "DIGRAPH":
                    return nx.DiGraph()
                case _:
                    raise ValueError(f"Unknown graph type: {graph_type}")

        return ParseTreeNode(evaluator, production.GRAPH_TYPE)

    @_("NODE node") # type: ignore
    def entity(self, production):
        return ParseTreeNode[str](lambda x: x, production.node)

    @_("EDGE edge") # type: ignore
    def entity(self, production):
        return ParseTreeNode[tuple[str, str]](lambda x: x, production.edge)

    # ----- PROPERTIES -----

    @_("EXISTS ID") # type: ignore
    def boolean(self, production):
        return ParseTreeNode(lambda x: x in self.variables, production.ID)

    @_("IS GRAPH_TYPE ID") # type: ignore
    def boolean(self, production):
        def evaluator(variable_id: str, graph_type: str):
            variable = self._get_variable(variable_id)
            match graph_type:
                case "GRAPH":
                    return isinstance(variable, nx.Graph)
                case "DIGRAPH":
                    return isinstance(variable, nx.DiGraph)
                case _:
                    raise ValueError(f"Unknown graph type: {production.entity}")

        return ParseTreeNode(evaluator, production.ID, production.GRAPH_TYPE)

    @_("HAS node ID") # type: ignore
    def boolean(self, production):
        return ParseTreeNode(
            lambda graph_id, node: node in self._get_graph(graph_id),
            production.ID, production.node
        )

    @_("HAS EDGE edge ID") # type: ignore
    def boolean(self, production):
        return ParseTreeNode(
            lambda graph_id, edge: self._get_graph(graph_id).has_edge(*edge),
            production.ID, production.edge
        )

    @_("GET WEIGHT OF EDGE edge ID") # type: ignore
    def number(self, production):
        def evaluator(graph_id: str, edge: tuple[str, str]):
            graph = self._get_graph(graph_id)
            if not graph.has_edge(*edge):
                raise ValueError(f"Edge {edge} not in graph {graph_id}")

            return graph.get_edge_data(*edge).get("weight", 1)

        return ParseTreeNode(evaluator, production.ID, production.edge)

    # ----- COMPARISONS -----

    @_("comparable COMPARATOR comparable") # type: ignore
    def boolean(self, production):
        def evaluator(left: Any, comparator: str, right: Any):
            match comparator:
                case "==":
                    return left == right
                case "!=":
                    return left != right
                case "<":
                    return left < right
                case "<=":
                    return left <= right
                case ">":
                    return left > right
                case ">=":
                    return left > right

        return ParseTreeNode(
            evaluator,
            production.comparable0, production.COMPARATOR, production.comparable1
        )

    @_("boolean") # type: ignore
    def comparable(self, production):
        return ParseTreeNode[bool](lambda x: x, production.boolean)

    @_("number") # type: ignore
    def comparable(self, production):
        return ParseTreeNode[int | float](lambda x: x, production.number)

    @_("string") # type: ignore
    def comparable(self, production):
        return ParseTreeNode[str](lambda x: x, production.string)

    # ----- LITERALS AND VARIABLES -----

    @_("node node") # type: ignore
    def edge(self, production):
        return ParseTreeNode[tuple[str, str]](
            lambda x, y: (x, y), production.node0, production.node1
        )

    @_("string") # type: ignore
    def node(self, production):
        return ParseTreeNode[str](lambda x: x, production.string)

    @_("ID") # type: ignore
    def node(self, production):
        return ParseTreeNode[str](lambda x: self._get_variable(x), production.ID)

    @_("BOOLEAN") # type: ignore
    def boolean(self, production):
        return ParseTreeNode[bool](lambda x: x == "TRUE", production.BOOLEAN)

    @_("NUMBER") # type: ignore
    def number(self, production):
        def evaluator(number: str):
            float_value = float(number)
            return int(float_value) if float_value.is_integer() else float_value

        return ParseTreeNode(evaluator, production.NUMBER)

    @_("STRING") # type: ignore
    def string(self, production):
        return ParseTreeNode[str](lambda x: x[1:-1], production.STRING)

