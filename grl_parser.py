import codecs
from collections import defaultdict
from io import TextIOWrapper
import json
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
        ("right", "PRINT"),
        ("left", "LOGICAL_IMPLIES"),
        ("left", "LOGICAL_XOR"),
        ("left", "LOGICAL_OR"),
        ("left", "LOGICAL_AND"),
        ("right", "LOGICAL_NOT"),
        ("nonassoc", "COMPARATOR"),
        ("left", "PLUS", "MINUS"),
        ("left", "MULTIPLY", "DIVIDE"),
        ("left", "POWER"),
        ("right", "STR", "NUM", "BOOL"),
    ]

    def __init__(self):
        self.variables: dict[str, Any] = {}

    def _get_variable(self, variable_id: str) -> Any:
        if variable_id not in self.variables:
            raise ValueError(f"Variable {variable_id} doesn't exist")

        return self.variables[variable_id]

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

    def _get_new_graph_by_type(self, graph_type: str):
        match graph_type:
            case "GRAPH":
                return nx.Graph()
            case "DIGRAPH":
                return nx.DiGraph()
            case _:
                raise ValueError(f"Unknown graph type: {repr(graph_type)}")

    def _import_graph(self, graph_id: str, file: TextIOWrapper):
        graph_type = file.readline()
        graph = self._get_new_graph_by_type(graph_type[:-1])

        graph_json = json.load(file)
        for source in graph_json:
            graph.add_node(source)

            for dest_data in graph_json[source]:
                match dest_data:
                    case str() as dest:
                        graph.add_edge(source, dest)
                    case (dest, weight):
                        graph.add_edge(source, dest)
                        graph.edges[source, dest]["weight"] = weight

        self.variables[graph_id] = graph

    def _export_graph(self, graph: nx.Graph, file: TextIOWrapper):
        match graph:
            case nx.DiGraph():
                file.write("DIGRAPH\n")
            case nx.Graph():
                file.write("GRAPH\n")
            case _:
                raise ValueError(f"Unknown graph type: {type(graph)}")

        graph_json: defaultdict[str, list[str | tuple[str, int | float]]] = defaultdict(list)
        for source in graph.nodes:
            for dest in graph.neighbors(source):
                graph_json[source].append(
                    (dest, edge_data["weight"])
                    if "weight" in (edge_data := graph.get_edge_data(source, dest))
                    else dest
                )

        json.dump(graph_json, file)

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

    @_("DFS node ID") # type: ignore
    def double_iterator(self, production):
        return ParseTreeNode(
            lambda graph_id, start_node: [
                (str(source), str(dest))
                for source, dest in nx.dfs_edges(
                    self._get_graph(graph_id), start_node
                )
            ],
            production.ID, production.node
        )

    @_("BFS node ID") # type: ignore
    def double_iterator(self, production):
        return ParseTreeNode(
            lambda graph_id, start_node: [
                (str(source), str(dest))
                for source, dest in nx.bfs_edges(
                    self._get_graph(graph_id), start_node
                )
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

    @_("LENGTH single_iterator") # type: ignore
    def number(self, production):
        return ParseTreeNode(len, production.single_iterator)

    @_("LENGTH double_iterator") # type: ignore
    def number(self, production):
        return ParseTreeNode(len, production.double_iterator)

    @_("LENGTH triple_iterator") # type: ignore
    def number(self, production):
        return ParseTreeNode(len, production.triple_iterator)

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
        return ParseTreeNode(lambda x: print(str(x).upper()), production.boolean)

    @_("PRINT number") # type: ignore
    def statement(self, production):
        return ParseTreeNode(print, production.number)

    @_("PRINT string") # type: ignore
    def statement(self, production):
        return ParseTreeNode(print, production.string)

    @_("PRINT ID") # type: ignore
    def statement(self, production):
        return ParseTreeNode(print, self._get_graph(production.ID))

    @_("PRINT") # type: ignore
    def statement(self, production):
        return ParseTreeNode(print)

    @_("RUN string") # type: ignore
    def statement(self, production):
        def evaluator(file_path: str):
            with open(file_path) as file:
                self.parse(self.lexer.tokenize(file.read()))

        return ParseTreeNode(evaluator, production.string)

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
                self._import_graph(graph_id, file)

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

    @_( # type: ignore
        "SET ID string",
        "SET ID number",
        "SET ID boolean",
    )
    def statement(self, production):
        def evaluator(variable_id: str, value: str | int | float | bool):
            self.variables[variable_id] = value

        return ParseTreeNode(
            evaluator, production.ID, production[2]
        )

    @_("SET ID ID") # type: ignore
    def statement(self, production):
        def evaluator(target_id: str, source_id: str):
            self.variables[target_id] = self._get_variable(source_id)

        return ParseTreeNode(
            evaluator, production.ID0, production.ID1
        )

    # ----- ENTITIES -----

    @_("GRAPH_TYPE") # type: ignore
    def entity(self, production):
        return ParseTreeNode(self._get_new_graph_by_type, production.GRAPH_TYPE)

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

    @_("HAS NODE node ID") # type: ignore
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

    # ----- EXPRESSIONS -----

    @_( # type: ignore
        "string COMPARATOR string",
        "string COMPARATOR number",
        "string COMPARATOR boolean",
        "number COMPARATOR string",
        "number COMPARATOR number",
        "number COMPARATOR boolean",
        "boolean COMPARATOR string",
        "boolean COMPARATOR number",
        "boolean COMPARATOR boolean"
    )
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
            production[0], production.COMPARATOR, production[2]
        )

    @_("ID COMPARATOR ID") # type: ignore
    def boolean(self, production):
        def evaluator(left_id: str, comparator: str, right_id: str):
            left_variable = self._get_variable(left_id)
            right_variable = self._get_variable(right_id)

            match comparator:
                case "==":
                    return left_variable == right_variable
                case "!=":
                    return left_variable != right_variable
                case "<":
                    return left_variable < right_variable
                case "<=":
                    return left_variable <= right_variable
                case ">":
                    return left_variable > right_variable
                case ">=":
                    return left_variable >= right_variable

        return ParseTreeNode(
            evaluator,
            production[0], production.COMPARATOR, production[2]
        )

    @_("LOGICAL_NOT boolean") # type: ignore
    def boolean(self, production):
        return ParseTreeNode(lambda x: not x, production.boolean)

    @_("boolean LOGICAL_AND boolean") # type: ignore
    def boolean(self, production):
        return ParseTreeNode[bool](lambda x, y: x and y, production.boolean0, production.boolean1)

    @_("boolean LOGICAL_OR boolean") # type: ignore
    def boolean(self, production):
        return ParseTreeNode[bool](lambda x, y: x or y, production.boolean0, production.boolean1)

    @_("boolean LOGICAL_XOR boolean") # type: ignore
    def boolean(self, production):
        return ParseTreeNode[bool](
            lambda x, y: (x and (not y)) or ((not x) and y),
            production.boolean0, production.boolean1
        )

    @_("boolean LOGICAL_IMPLIES boolean") # type: ignore
    def boolean(self, production):
        return ParseTreeNode[bool](
            lambda x, y: (not x) or y,
            production.boolean0, production.boolean1
        )

    @_( # type: ignore
        "string PLUS string",
        "string PLUS number",
        "string PLUS boolean",
        "number PLUS string",
        "boolean PLUS string",
    )
    def string(self, production):
        def evaluator(left: str | int | float | bool, right: str | int | float | bool):
            if isinstance(left, bool):
                left = str(left).upper()
            if isinstance(right, bool):
                right = str(right).upper()

            return str(left) + str(right)

        return ParseTreeNode[str](evaluator, production[0], production[2])

    @_("number PLUS number") # type: ignore
    def number(self, production):
        return ParseTreeNode[int | float](lambda x, y: x + y, production.number0, production.number1)

    @_("number MINUS number") # type: ignore
    def number(self, production):
        return ParseTreeNode[int | float](lambda x, y: x - y, production.number0, production.number1)

    @_("number MULTIPLY number") # type: ignore
    def number(self, production):
        return ParseTreeNode[int | float](lambda x, y: x * y, production.number0, production.number1)

    @_("number DIVIDE number") # type: ignore
    def number(self, production):
        return ParseTreeNode[int | float](lambda x, y: x / y, production.number0, production.number1)

    @_("number POWER number") # type: ignore
    def number(self, production):
        return ParseTreeNode[int | float](lambda x, y: x ** y, production.number0, production.number1)

    @_("LEFT_PARENT number RIGHT_PARENT") # type: ignore
    def number(self, production):
        return ParseTreeNode[int | float](lambda x: x, production.number)

    @_("LEFT_PARENT boolean RIGHT_PARENT") # type: ignore
    def boolean(self, production):
        return ParseTreeNode[bool](lambda x: x, production.boolean)

    @_("LEFT_PARENT string RIGHT_PARENT") # type: ignore
    def string(self, production):
        return ParseTreeNode[bool](lambda x: x, production.string)

    # ----- TYPE CASTING -----

    @_("LEFT_PARENT STR string RIGHT_PARENT") # type: ignore
    def string(self, production):
        return ParseTreeNode(lambda x: x, production.string)

    @_("LEFT_PARENT STR number RIGHT_PARENT") # type: ignore
    def string(self, production):
        return ParseTreeNode(str, production.number)

    @_("LEFT_PARENT STR boolean RIGHT_PARENT") # type: ignore
    def string(self, production):
        return ParseTreeNode(lambda x: str(x).upper(), production.boolean)

    @_("LEFT_PARENT NUM string RIGHT_PARENT") # type: ignore
    def number(self, production):
        return ParseTreeNode(float, production.boolean)

    @_("LEFT_PARENT NUM number RIGHT_PARENT") # type: ignore
    def number(self, production):
        return ParseTreeNode(lambda x: x, production.number)

    @_("LEFT_PARENT NUM boolean RIGHT_PARENT") # type: ignore
    def number(self, production):
        return ParseTreeNode(int, production.boolean)

    @_("LEFT_PARENT BOOL string RIGHT_PARENT") # type: ignore
    def boolean(self, production):
        return ParseTreeNode(bool, production.number)

    @_("LEFT_PARENT BOOL number RIGHT_PARENT") # type: ignore
    def boolean(self, production):
        return ParseTreeNode(bool, production.number)

    @_("LEFT_PARENT BOOL boolean RIGHT_PARENT") # type: ignore
    def boolean(self, production):
        return ParseTreeNode(lambda x: x, production.boolean)

    @_("LEFT_PARENT STR ID RIGHT_PARENT") # type: ignore
    def string(self, production):
        return ParseTreeNode(
            lambda x: str(self._get_variable(x)),
            production.ID
        )

    @_("LEFT_PARENT NUM ID RIGHT_PARENT") # type: ignore
    def number(self, production):
        def evaluator(variable_id: str):
            variable = self._get_variable(variable_id)
            if isinstance(variable, (int, float)):
                return variable

            return float(variable)

        return ParseTreeNode(evaluator, production.ID)

    @_("LEFT_PARENT BOOL ID RIGHT_PARENT") # type: ignore
    def boolean(self, production):
        return ParseTreeNode(
            lambda x: bool(self._get_variable(x)),
            production.ID
        )

    # ----- LITERALS AND VARIABLES -----

    @_("node node") # type: ignore
    def edge(self, production):
        return ParseTreeNode[tuple[str, str]](
            lambda x, y: (x, y), production.node0, production.node1
        )

    @_("string") # type: ignore
    def node(self, production):
        return ParseTreeNode[str](lambda x: x, production.string)

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
        return ParseTreeNode[str](
            lambda x: codecs.getdecoder("unicode_escape")(x[1:-1])[0],
            production.STRING
        )
