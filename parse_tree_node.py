from typing import Any, Callable, Generic, TypeVar


T = TypeVar("T")


class ParseTreeNode(Generic[T]):
    def __init__(self, evaluator: Callable[..., T], *parameters: "ParseTreeNode | Any"):
        self.evaluator = evaluator
        self.parameters = parameters

    def evaluate(self) -> T:
        return self.evaluator(
            *(
                item.evaluate() if isinstance(item, ParseTreeNode) else item
                for item in self.parameters
            )
        )
