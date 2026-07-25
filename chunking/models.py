from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class NodeType(Enum):
    DOCUMENT = "document"

    HEADING = "heading"

    PARAGRAPH = "paragraph"

    CODE_BLOCK = "code_block"

    TABLE = "table"

    LIST = "list"

    LIST_ITEM = "list_item"

    BLOCKQUOTE = "blockquote"

    HORIZONTAL_RULE = "horizontal_rule"

    IMAGE = "image"

    HTML = "html"

    TEXT = "text"


@dataclass(slots=True)
class DocumentNode:
    id: str = field(default_factory=lambda: str(uuid4()))

    node_type: NodeType = NodeType.PARAGRAPH

    content: str = ""

    depth: int = 0

    parent: str | None = None

    children: list[str] = field(default_factory=list)

    attributes: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def is_heading(self) -> bool:
        return self.node_type == NodeType.HEADING

    @property
    def is_paragraph(self) -> bool:
        return self.node_type == NodeType.PARAGRAPH

    @property
    def is_code(self) -> bool:
        return self.node_type == NodeType.CODE_BLOCK

    @property
    def is_table(self) -> bool:
        return self.node_type == NodeType.TABLE

    @property
    def is_list(self) -> bool:
        return self.node_type == NodeType.LIST

    @property
    def is_list_item(self) -> bool:
        return self.node_type == NodeType.LIST_ITEM

    def add_child(self, child: "DocumentNode") -> None:
        child.parent = self.id
        child.depth = self.depth + 1
        self.children.append(child.id)


@dataclass(slots=True)
class DocumentTree:
    root: str

    nodes: dict[str, DocumentNode] = field(default_factory=dict)

    def add_node(self, node: DocumentNode) -> None:
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> DocumentNode:
        return self.nodes[node_id]

    def add_child(
        self,
        parent_id: str,
        child: DocumentNode,
    ) -> None:
        parent = self.get_node(parent_id)

        parent.add_child(child)

        self.add_node(child)

    def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes

    def root_node(self) -> DocumentNode:
        return self.get_node(self.root)

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())