from markdown_it import MarkdownIt
from markdown_it.token import Token

from chunking.models import (
    CodeBlockData,
    DocumentNode,
    DocumentTree,
    EmptyData,
    HeadingData,
    NodeKind,
    TableData,
)


class MarkdownParser:
    def __init__(self):
        # linkify=False avoids optional linkify-it-py (tables/strikethrough still work)
        self.md = MarkdownIt("gfm-like", {"linkify": False})

    def parse(self, markdown: str) -> DocumentTree:
        tokens = self.md.parse(markdown)

        root = DocumentNode(
            kind=NodeKind.DOCUMENT,
            content="Document",
        )

        self.tree = DocumentTree(root=root.id)
        self.tree.add_node(root)
        self.heading_stack: list[tuple[int, str]] = [(0, root.id)]

        index = 0
        while index < len(tokens):
            index = self._dispatch(tokens, index, self._current_parent())

        return self.tree

    def _dispatch(
        self,
        tokens: list[Token],
        index: int,
        parent: DocumentNode,
    ) -> int:
        token = tokens[index]

        if token.type == "heading_open":
            return self._parse_heading(tokens, index)

        if token.type == "paragraph_open":
            return self._parse_paragraph(tokens, index, parent)

        if token.type == "fence":
            return self._parse_fence(tokens, index, parent)

        if token.type in {"bullet_list_open", "ordered_list_open"}:
            return self._parse_list(tokens, index, parent)

        if token.type == "blockquote_open":
            return self._parse_blockquote(tokens, index, parent)

        if token.type == "table_open":
            return self._parse_table(tokens, index, parent)

        if token.type == "hr":
            return self._parse_hr(tokens, index, parent)

        return index + 1

    def _current_parent(self) -> DocumentNode:
        return self.tree.get(self.heading_stack[-1][1])

    def _append_node(self, parent: DocumentNode, child: DocumentNode) -> None:
        self.tree.add_child(parent.id, child)

    def _parse_heading(self, tokens: list[Token], index: int) -> int:
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
        self.heading_stack.append((level, heading.id))

        return index + 3

    def _parse_paragraph(
        self,
        tokens: list[Token],
        index: int,
        parent: DocumentNode,
    ) -> int:
        inline_token = tokens[index + 1]

        paragraph = DocumentNode(
            kind=NodeKind.PARAGRAPH,
            content=inline_token.content,
            data=EmptyData(),
        )
        self._append_node(parent, paragraph)

        return index + 3

    def _parse_fence(
        self,
        tokens: list[Token],
        index: int,
        parent: DocumentNode,
    ) -> int:
        token = tokens[index]

        code = DocumentNode(
            kind=NodeKind.CODE_BLOCK,
            content=token.content,
            data=CodeBlockData(language=token.info.strip()),
        )
        self._append_node(parent, code)

        return index + 1

    def _parse_list(
        self,
        tokens: list[Token],
        index: int,
        parent: DocumentNode,
    ) -> int:
        open_token = tokens[index]
        close_type = (
            "bullet_list_close"
            if open_token.type == "bullet_list_open"
            else "ordered_list_close"
        )

        list_node = DocumentNode(
            kind=NodeKind.LIST,
            content="",
            data=EmptyData(),
        )
        self._append_node(parent, list_node)

        index += 1
        item_parts: list[str] = []

        while index < len(tokens) and tokens[index].type != close_type:
            if tokens[index].type == "list_item_open":
                index, item_text = self._parse_list_item(tokens, index + 1)
                item_parts.append(item_text)

                item_node = DocumentNode(
                    kind=NodeKind.LIST_ITEM,
                    content=item_text,
                    data=EmptyData(),
                )
                self._append_node(list_node, item_node)
            else:
                index += 1

        list_node.content = "\n".join(f"- {part}" for part in item_parts if part)
        return index + 1

    def _parse_list_item(
        self,
        tokens: list[Token],
        index: int,
    ) -> tuple[int, str]:
        parts: list[str] = []

        while index < len(tokens) and tokens[index].type != "list_item_close":
            token = tokens[index]

            if token.type == "paragraph_open":
                inline = tokens[index + 1]
                parts.append(inline.content)
                index += 3
                continue

            if token.type == "fence":
                language = token.info.strip()
                parts.append(f"```{language}\n{token.content.rstrip()}\n```")
                index += 1
                continue

            if token.type in {"bullet_list_open", "ordered_list_open"}:
                nested_parts: list[str] = []
                close_type = (
                    "bullet_list_close"
                    if token.type == "bullet_list_open"
                    else "ordered_list_close"
                )
                index += 1

                while index < len(tokens) and tokens[index].type != close_type:
                    if tokens[index].type == "list_item_open":
                        index, nested_text = self._parse_list_item(
                            tokens,
                            index + 1,
                        )
                        nested_parts.append(nested_text)
                    else:
                        index += 1

                parts.append("\n".join(f"  - {part}" for part in nested_parts))
                index += 1
                continue

            index += 1

        return index + 1, "\n".join(parts)

    def _parse_blockquote(
        self,
        tokens: list[Token],
        index: int,
        parent: DocumentNode,
    ) -> int:
        blockquote = DocumentNode(
            kind=NodeKind.BLOCKQUOTE,
            content="",
            data=EmptyData(),
        )
        self._append_node(parent, blockquote)

        index += 1
        parts: list[str] = []

        while index < len(tokens) and tokens[index].type != "blockquote_close":
            token = tokens[index]

            if token.type == "paragraph_open":
                inline = tokens[index + 1]
                parts.append(inline.content)
                index += 3
                continue

            index = self._dispatch(tokens, index, blockquote)

        blockquote.content = "\n\n".join(parts)
        return index + 1

    def _parse_table(
        self,
        tokens: list[Token],
        index: int,
        parent: DocumentNode,
    ) -> int:
        rows: list[list[str]] = []
        current_row: list[str] = []
        in_header = False
        columns = 0

        index += 1
        while index < len(tokens) and tokens[index].type != "table_close":
            token = tokens[index]

            if token.type == "thead_open":
                in_header = True
            elif token.type == "thead_close":
                in_header = False
            elif token.type == "tr_open":
                current_row = []
            elif token.type in {"th_open", "td_open"}:
                inline = tokens[index + 1]
                current_row.append(inline.content.strip())
                index += 3
                continue
            elif token.type == "tr_close" and current_row:
                rows.append(current_row)
                columns = max(columns, len(current_row))

            index += 1

        markdown_table = self._render_table(rows)
        table = DocumentNode(
            kind=NodeKind.TABLE,
            content=markdown_table,
            data=TableData(columns=columns, rows=len(rows)),
        )
        self._append_node(parent, table)

        return index + 1

    def _render_table(self, rows: list[list[str]]) -> str:
        if not rows:
            return ""

        width = max(len(row) for row in rows)
        normalized = [row + [""] * (width - len(row)) for row in rows]

        header = normalized[0]
        divider = ["---"] * width
        body = normalized[1:] if len(normalized) > 1 else []

        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(divider) + " |",
        ]
        lines.extend("| " + " | ".join(row) + " |" for row in body)

        return "\n".join(lines)

    def _parse_hr(
        self,
        tokens: list[Token],
        index: int,
        parent: DocumentNode,
    ) -> int:
        hr = DocumentNode(
            kind=NodeKind.HORIZONTAL_RULE,
            content="---",
            data=EmptyData(),
        )
        self._append_node(parent, hr)
        return index + 1
