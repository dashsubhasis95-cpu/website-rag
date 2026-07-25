from markdown_it import MarkdownIt
from markdown_it.token import Token

from chunking.models import (
    CodeBlockData,
    DocumentNode,
    DocumentTree,
    EmptyData,
    HeadingData,
    NodeKind,
)


class MarkdownParser:
    def __init__(self):
        self.md = MarkdownIt()

    def parse(self, markdown: str) -> DocumentTree:
        tokens = self.md.parse(markdown)

        root = DocumentNode(
            kind=NodeKind.DOCUMENT,
            content="Document",
        )

        self.tree = DocumentTree(root=root.id)
        self.tree.add_node(root)

        #
        # heading_stack stores tuples:
        #
        # (heading_level, node_id)
        #
        self.heading_stack = [(0, root.id)]

        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "heading_open":
                i = self._parse_heading(tokens, i)

            elif token.type == "paragraph_open":
                i = self._parse_paragraph(tokens, i)

            elif token.type == "fence":
                i = self._parse_fence(tokens, i)

            else:
                i += 1

        return self.tree

    # ----------------------------------------------------
    # Helpers
    # ----------------------------------------------------

    def _current_parent(self) -> DocumentNode:
        return self.tree.get(self.heading_stack[-1][1])

    def _append_node(
        self,
        parent: DocumentNode,
        child: DocumentNode,
    ):
        self.tree.add_child(parent.id, child)

    # ----------------------------------------------------
    # Heading
    # ----------------------------------------------------

    def _parse_heading(
        self,
        tokens: list[Token],
        index: int,
    ) -> int:

        open_token = tokens[index]

        inline_token = tokens[index + 1]

        level = int(open_token.tag[1])

        while self.heading_stack[-1][0] >= level:
            self.heading_stack.pop()

        parent = self.tree.get(self.heading_stack[-1][1])

        heading = DocumentNode(
            kind=NodeKind.HEADING,
            content=inline_token.content,
            data=HeadingData(level=level),
        )

        self._append_node(parent, heading)

        self.heading_stack.append(
            (
                level,
                heading.id,
            )
        )

        #
        # Skip:
        #
        # heading_open
        # inline
        # heading_close
        #
        return index + 3

    # ----------------------------------------------------
    # Paragraph
    # ----------------------------------------------------

    def _parse_paragraph(
        self,
        tokens: list[Token],
        index: int,
    ) -> int:

        inline_token = tokens[index + 1]

        paragraph = DocumentNode(
            kind=NodeKind.PARAGRAPH,
            content=inline_token.content,
            data=EmptyData(),
        )

        parent = self._current_parent()

        self._append_node(
            parent,
            paragraph,
        )

        return index + 3

    # ----------------------------------------------------
    # Code Block
    # ----------------------------------------------------

    def _parse_fence(
        self,
        tokens: list[Token],
        index: int,
    ) -> int:

        token = tokens[index]

        code = DocumentNode(
            kind=NodeKind.CODE_BLOCK,
            content=token.content,
            data=CodeBlockData(
                language=token.info.strip(),
            ),
        )

        parent = self._current_parent()

        self._append_node(
            parent,
            code,
        )

        return index + 1