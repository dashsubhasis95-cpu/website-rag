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

    def walk(self, node_id: str | None = None):
        """Depth-first traversal starting at *node_id* (defaults to root)."""
        start = node_id or self.root
        stack = [start]

        while stack:
            current_id = stack.pop()
            node = self.get(current_id)
            yield node

            for child_id in reversed(node.children):
                stack.append(child_id)


# ==========================================================
# Chunking Configuration
# ==========================================================

class ChunkStrategy(Enum):
    PROSE = "prose"
    CODE = "code"
    TABLE = "table"
    HEADING = "heading"
    STRUCTURE = "structure"


class ChunkLevel(Enum):
    PARENT = "parent"
    CHILD = "child"


@dataclass(slots=True, frozen=True)
class ChunkingConfig:
    max_tokens: int = 512
    min_tokens: int = 32
    overlap_tokens: int = 64
    encoding_name: str = "cl100k_base"
    include_heading_prefix: bool = True
    split_code_blocks: bool = False
    merge_small_chunks: bool = True
    prefix_heading_levels: int = 2
    enable_hierarchical: bool = True
    parent_max_tokens: int = 2048
    parent_overlap_tokens: int = 128
    enable_heading_chunks: bool = True
    split_oversized_code: bool = True
    split_oversized_tables: bool = True
    code_overlap_lines: int = 3
    table_rows_per_chunk: int = 8
    table_overlap_rows: int = 1


# ==========================================================
# Section (intermediate grouping unit)
# ==========================================================

@dataclass(slots=True)
class Section:
    heading_path: list[str]
    heading_level: int
    nodes: list[DocumentNode] = field(default_factory=list)
    part_index: int = 0
    is_continuation: bool = False


# ==========================================================
# Chunk Output
# ==========================================================

@dataclass(slots=True)
class ChunkMetadata:
    source_url: str = ""
    page_title: str = ""
    heading_path: list[str] = field(default_factory=list)
    heading_level: int = 0
    chunk_index: int = 0
    token_count: int = 0
    content_types: list[str] = field(default_factory=list)
    node_ids: list[str] = field(default_factory=list)
    char_count: int = 0
    is_continuation: bool = False
    chunk_level: ChunkLevel = ChunkLevel.CHILD
    parent_id: str | None = None
    child_ids: list[str] = field(default_factory=list)
    section_index: int = 0
    strategy: ChunkStrategy = ChunkStrategy.PROSE


@dataclass(slots=True)
class Chunk:
    id: str
    content: str
    metadata: ChunkMetadata

    @property
    def token_count(self) -> int:
        return self.metadata.token_count


@dataclass(slots=True)
class ChunkingResult:
    chunks: list[Chunk] = field(default_factory=list)
    source_url: str = ""
    page_title: str = ""
    total_tokens: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    @property
    def parent_chunks(self) -> list[Chunk]:
        return [
            chunk for chunk in self.chunks
            if chunk.metadata.chunk_level == ChunkLevel.PARENT
        ]

    @property
    def child_chunks(self) -> list[Chunk]:
        return [
            chunk for chunk in self.chunks
            if chunk.metadata.chunk_level == ChunkLevel.CHILD
        ]

    @property
    def parent_count(self) -> int:
        return len(self.parent_chunks)

    @property
    def child_count(self) -> int:
        return len(self.child_chunks)

    @property
    def heading_chunks(self) -> list[Chunk]:
        return [
            chunk for chunk in self.chunks
            if chunk.metadata.strategy == ChunkStrategy.HEADING
        ]

    def resolve_parent_context(self, child: Chunk) -> str | None:
        """Return full parent text for a retrieved child (includes continuations)."""
        if child.metadata.parent_id is None:
            return None

        root_id = child.metadata.parent_id
        parent_parts = [
            chunk for chunk in self.parent_chunks
            if chunk.id == root_id or chunk.metadata.parent_id == root_id
        ]

        if not parent_parts:
            return None

        parent_parts.sort(key=lambda chunk: chunk.metadata.chunk_index)
        return "\n\n".join(chunk.content for chunk in parent_parts)