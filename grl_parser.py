from io import TextIOWrapper
from typing import Any

import networkx as nx
import matplotlib.pyplot as plt
from sly import Parser

from parse_tree_node import ParseTreeNode
from grl_lexer import GRLLexer


class GRLParser(Parser):
    lexer = GRLLexer()

    tokens = lexer.tokens

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

    def _graph_has_negative_weights(self, graph: nx.Graph):
        return any(
            graph.get_edge_data(u, v).get("weight", 1) < 0
            for u, v in graph.edges
        )

    def _import_graph(self, graph_id: str, file_lines: list[str]):
        for line in file_lines:
            self.parse(self.lexer.tokenize(f"{line[:-1]} {graph_id}"))

    def _export_graph(self, graph: nx.Graph, file: TextIOWrapper):
        match graph:
            case nx.DiGraph():
                file.write("ADD DIGRAPH\n")
            case nx.Graph():
                file.write("ADD GRAPH\n")
            case _:
                raise ValueError(f"Unknown graph type: {type(graph)}")

        for node in graph:
            file.write(f"ADD NODE \"{node}\"\n")

        for source, dest in graph.edges:
            file.write(f"ADD EDGE \"{source}\" \"{dest}\"\n")
            if "weight" in (edge_data := graph.get_edge_data(source, dest)):
                file.write(
                    f"SET WEIGHT OF EDGE \"{source}\" \"{dest}\" {edge_data["weight"]}\n"
                )

    # ----- PROGRAM -----

    @_("statement_sequence") # type: ignore
    def program(self, production):
        statement_sequence: list[ParseTreeNode[None]] = production.statement_sequence
        for statement in statement_sequence:
            statement.evaluate()

    # ----- CONTROL FLOW -----

    @_("IF boolean LEFT_CURLY statement_sequence RIGHT_CURLY { elseif_statement } [ else_statement ]") # type: ignore
    def statement(self, production):
        def evaluator(
            boolean: bool,
            statement_sequence: list[ParseTreeNode[None]],
            elseif_statements: list[ParseTreeNode[None]],
            else_statement: tuple[ParseTreeNode[None]] | None,
        ):
            if boolean:
                for statement in statement_sequence:
                    statement.evaluate()
                return

            for elseif_statement in elseif_statements:
                if elseif_statement.evaluate():
                    return

            if else_statement:
                else_statement[0].evaluate()

        return ParseTreeNode(
            evaluator,
            production.boolean, production.statement_sequence,
            production.elseif_statement, production.else_statement
        )

    @_("ELSEIF boolean LEFT_CURLY statement_sequence RIGHT_CURLY") # type: ignore
    def elseif_statement(self, production):
        def evaluator(boolean: bool, statement_sequence: list[ParseTreeNode[None]]):
            if boolean:
                for statement in statement_sequence:
                    statement.evaluate()

            return boolean

        return ParseTreeNode(
            evaluator, production.boolean, production.statement_sequence
        )

    @_("ELSE LEFT_CURLY statement_sequence RIGHT_CURLY") # type: ignore
    def else_statement(self, production):
        def evaluator(statement_sequence: list[ParseTreeNode[None]]):
            for statement in statement_sequence:
                statement.evaluate()

        return (ParseTreeNode(evaluator, production.statement_sequence),)

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

    @_("FOR ID COMMA ID OF double_iterator LEFT_CURLY statement_sequence RIGHT_CURLY") # type: ignore
    def statement(self, production):
        def evaluator(
            first_iterator_id: str,
            second_iterator_id: str,
            double_iterator: list[Any],
            statement_sequence: list[ParseTreeNode[None]]
        ):
            for item1, item2 in double_iterator:
                self.variables[first_iterator_id] = item1
                self.variables[second_iterator_id] = item2
                for statement in statement_sequence:
                    statement.evaluate()

            del self.variables[first_iterator_id]
            del self.variables[second_iterator_id]

        return ParseTreeNode(
            evaluator,
            production.ID0, production.ID1,
            production.double_iterator, production.statement_sequence
        )

    @_("FOR ID COMMA ID COMMA ID OF triple_iterator LEFT_CURLY statement_sequence RIGHT_CURLY") # type: ignore
    def statement(self, production):
        def evaluator(
            first_iterator_id: str,
            second_iterator_id: str,
            third_iterator_id: str,
            triple_iterator: list[Any],
            statement_sequence: list[ParseTreeNode[None]]
        ):
            for item1, item2, item3 in triple_iterator:
                self.variables[first_iterator_id] = item1
                self.variables[second_iterator_id] = item2
                self.variables[third_iterator_id] = item3
                for statement in statement_sequence:
                    statement.evaluate()

            del self.variables[first_iterator_id]
            del self.variables[second_iterator_id]
            del self.variables[third_iterator_id]

        return ParseTreeNode(
            evaluator,
            production.ID0, production.ID1, production.ID2,
            production.triple_iterator, production.statement_sequence
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
            has_negative_weights = self._graph_has_negative_weights(graph)

            return [
                str(item)
                for item in nx.shortest_path(
                    graph, edge[0], edge[1], "weight",
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

    @_("EDGES ID") # type: ignore
    def double_iterator(self, production):
        return ParseTreeNode(
            lambda graph_id: [
                (str(source), str(dest))
                for source, dest in self._get_graph(graph_id).edges
            ],
            production.ID
        )

    @_("DISTANCE FROM node ID") # type: ignore
    def double_iterator(self, production):
        def evaluator(graph_id: str, node: str):
            graph = self._get_graph(graph_id)
            if node not in graph:
                raise ValueError(f"Node {node} not in graph {graph_id}")

            has_negative_weights = self._graph_has_negative_weights(graph)
            shortest_paths: dict[str, int | float] = nx.shortest_path_length(
                graph,
                source=node,
                weight="weight",
                method="bellman-ford" if has_negative_weights else "dijkstra"
            )

            return list(shortest_paths.items())

        return ParseTreeNode(evaluator, production.ID, production.node)

    @_("DISTANCE MATRIX ID") # type: ignore
    def triple_iterator(self, production):
        def evaluator(graph_id: str) -> list[tuple[str, str, int | float]]:
            graph = self._get_graph(graph_id)

            has_negative_weights = self._graph_has_negative_weights(graph)
            shortest_paths: dict[str, dict[str, int | float]] = nx.shortest_path_length(
                graph,
                weight="weight",
                method="bellman-ford" if has_negative_weights else "dijkstra"
            )

            return [
                (source, dest, length)
                for source, length_by_target in shortest_paths
                for dest, length in length_by_target.items()
            ]

        return ParseTreeNode(evaluator, production.ID)

    # ----- STATEMENTS -----

    @_("statement { LINE_SEPARATOR statement }") # type: ignore
    def statement_sequence(self, production) -> list[ParseTreeNode[None]]:
        return [production.statement0] + production.statement1

    @_("") # type: ignore
    def statement(self, production) -> list[ParseTreeNode[None]]:
        return ParseTreeNode.empty()

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

    @_("IMPORT ID string") # type: ignore
    def statement(self, production):
        def evaluator(graph_id: str, file_path: str):
            if graph_id in self.variables:
                raise ValueError(f"Entity {graph_id} already exists")

            with open(file_path + ".grlg") as file:
                file_lines = file.readlines()

            self._import_graph(graph_id, file_lines)

        return ParseTreeNode(evaluator, production.ID, production.string)

    @_("EXPORT ID string") # type: ignore
    def statement(self, production):
        def evaluator(graph_id: str, file_path: str):
            graph = self._get_graph(graph_id)
            with open(file_path + ".grlg", "w+") as file:
                self._export_graph(graph, file)

        return ParseTreeNode(evaluator, production.ID, production.string)

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

    @_("NODE COUNT ID") # type: ignore
    def number(self, production):
        return ParseTreeNode(
            lambda graph_id: len(self._get_graph(graph_id).nodes),
            production.ID
        )

    @_("EDGE COUNT ID") # type: ignore
    def number(self, production):
        return ParseTreeNode(
            lambda graph_id: len(self._get_graph(graph_id).edges),
            production.ID
        )

    @_("GET WEIGHT OF EDGE edge ID") # type: ignore
    def number(self, production):
        def evaluator(graph_id: str, edge: tuple[str, str]):
            graph = self._get_graph(graph_id)
            if not graph.has_edge(*edge):
                raise ValueError(f"Edge {edge} not in graph {graph_id}")

            return graph.get_edge_data(*edge).get("weight", 1)

        return ParseTreeNode(evaluator, production.ID, production.edge)

    @_("GET DISTANCE BETWEEN edge ID") # type: ignore
    def number(self, production):
        def evaluator(graph_id: str, edge: tuple[str, str]) -> int | float:
            graph = self._get_graph(graph_id)
            if edge[0] not in graph:
                raise ValueError(f"Node {edge[0]} not in graph {graph_id}")
            if edge[1] not in graph:
                raise ValueError(f"Node {edge[1]} not in graph {graph_id}")

            has_negative_weights = self._graph_has_negative_weights(graph)
            return nx.shortest_path_length(
                graph, edge[0], edge[1], "weight",
                "bellman-ford" if has_negative_weights else "dijkstra"
            )

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

