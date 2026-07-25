from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


# ==========================================================
# Node Types
# ==========================================================

class NodeKind(Enum):
    # Block Nodes
    DOCUMENT = "document"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    TABLE = "table"
    LIST = "list"
    LIST_ITEM = "list_item"
    BLOCKQUOTE = "blockquote"
    HORIZONTAL_RULE = "horizontal_rule"

    # Inline Nodes
    TEXT = "text"
    LINK = "link"
    IMAGE = "image"
    INLINE_CODE = "inline_code"
    EMPHASIS = "emphasis"
    STRONG = "strong"


# ==========================================================
# Node Payloads
# ==========================================================

@dataclass(slots=True, frozen=True)
class EmptyData:
    """Default payload for nodes that don't require extra data."""
    pass


@dataclass(slots=True, frozen=True)
class HeadingData:
    level: int


@dataclass(slots=True, frozen=True)
class CodeBlockData:
    language: str = ""


@dataclass(slots=True, frozen=True)
class LinkData:
    url: str
    title: str = ""


@dataclass(slots=True, frozen=True)
class ImageData:
    url: str
    alt: str = ""


@dataclass(slots=True, frozen=True)
class TableData:
    columns: int = 0
    rows: int = 0


# ==========================================================
# Document Node
# ==========================================================

@dataclass(slots=True)
class DocumentNode:
    id: str = field(default_factory=lambda: str(uuid4()))

    kind: NodeKind = NodeKind.PARAGRAPH

    content: str = ""

    data: Any = field(default_factory=EmptyData)

    parent: str | None = None

    children: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def is_block(self) -> bool:
        return self.kind in {
            NodeKind.DOCUMENT,
            NodeKind.HEADING,
            NodeKind.PARAGRAPH,
            NodeKind.CODE_BLOCK,
            NodeKind.TABLE,
            NodeKind.LIST,
            NodeKind.LIST_ITEM,
            NodeKind.BLOCKQUOTE,
            NodeKind.HORIZONTAL_RULE,
        }

    @property
    def is_inline(self) -> bool:
        return self.kind in {
            NodeKind.TEXT,
            NodeKind.LINK,
            NodeKind.IMAGE,
            NodeKind.INLINE_CODE,
            NodeKind.EMPHASIS,
            NodeKind.STRONG,
        }

    def add_child(self, child: "DocumentNode") -> None:
        child.parent = self.id
        self.children.append(child.id)


# ==========================================================
# Document Tree
# ==========================================================

@dataclass(slots=True)
class DocumentTree:
    root: str

    nodes: dict[str, DocumentNode] = field(default_factory=dict)

    def add_node(self, node: DocumentNode) -> None:
        self.nodes[node.id] = node

    def get(self, node_id: str) -> DocumentNode:
        return self.nodes[node_id]

    def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes

    def add_child(
        self,
        parent_id: str,
        child: DocumentNode,
    ) -> None:
        parent = self.get(parent_id)
        parent.add_child(child)
        self.add_node(child)

    @property
    def root_node(self) -> DocumentNode:
        return self.get(self.root)

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self):
        return iter(self.nodes.values())