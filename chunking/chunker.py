from __future__ import annotations

from chunking.heading_chunks import HeadingChunkBuilder
from chunking.hierarchy import HierarchicalChunkBuilder
from chunking.metadata import MetadataEnricher, NodeRenderer
from chunking.models import (
    Chunk,
    ChunkingConfig,
    ChunkingResult,
    ChunkLevel,
    ChunkStrategy,
    DocumentNode,
    DocumentTree,
    NodeKind,
    Section,
)
from chunking.parser import MarkdownParser
from chunking.splitter import TokenCounter, TokenSplitter
from chunking.type_splitters import ContentTypeSplitter
from chunking.validator import ChunkValidator
from ingestion.models import CrawledDocument, PageLinks, PageMetadata


class StructureAwareChunker:
    """
    Production chunker that:
    1. Parses markdown into a heading-aware document tree
    2. Groups content into semantic sections
    3. Splits oversized sections on token boundaries with overlap
    4. Enriches chunks with breadcrumbs, source metadata, and stable IDs
    5. Validates and merges undersized chunks
    """

    _SPLITTABLE_KINDS = {
        NodeKind.PARAGRAPH,
        NodeKind.LIST,
        NodeKind.LIST_ITEM,
        NodeKind.BLOCKQUOTE,
    }

    _ATOMIC_KINDS = {
        NodeKind.HORIZONTAL_RULE,
    }

    def __init__(self, config: ChunkingConfig | None = None):
        self.config = config or ChunkingConfig()
        self.parser = MarkdownParser()
        self.renderer = NodeRenderer()
        self.enricher = MetadataEnricher(self.renderer)
        self.splitter = TokenSplitter(self.config)
        self.content_splitter = ContentTypeSplitter(self.config)
        self.counter = TokenCounter(self.config.encoding_name)
        self.validator = ChunkValidator(self.config)
        self.hierarchy = HierarchicalChunkBuilder(
            config=self.config,
            renderer=self.renderer,
            enricher=self.enricher,
            counter=self.counter,
        )
        self.heading_builder = HeadingChunkBuilder(
            config=self.config,
            enricher=self.enricher,
            counter=self.counter,
        )

    def chunk_document(self, document: CrawledDocument) -> ChunkingResult:
        tree = self.parser.parse(document.markdown)
        sections = self._extract_sections(tree)

        heading_chunks = self.heading_builder.build(
            tree,
            source_url=document.url,
            page_title=document.metadata.title,
            start_index=0,
        )

        if self.config.enable_hierarchical:
            content_chunks = self._sections_to_hierarchical_chunks(
                sections=sections,
                source_url=document.url,
                page_title=document.metadata.title,
                start_index=len(heading_chunks),
            )
        else:
            content_chunks = self._sections_to_chunks(
                sections=sections,
                source_url=document.url,
                page_title=document.metadata.title,
                start_index=len(heading_chunks),
            )

        chunks = heading_chunks + content_chunks

        validated, warnings = self.validator.validate(chunks)
        total_tokens = sum(chunk.metadata.token_count for chunk in validated)

        return ChunkingResult(
            chunks=validated,
            source_url=document.url,
            page_title=document.metadata.title,
            total_tokens=total_tokens,
            warnings=warnings,
        )

    def chunk_documents(
        self,
        documents: list[CrawledDocument],
    ) -> list[ChunkingResult]:
        return [self.chunk_document(document) for document in documents]

    def chunk_markdown(
        self,
        markdown: str,
        *,
        source_url: str = "",
        page_title: str = "",
    ) -> ChunkingResult:
        document = CrawledDocument(
            url=source_url,
            markdown=markdown,
            html="",
            metadata=PageMetadata(title=page_title),
            links=PageLinks(),
        )
        return self.chunk_document(document)

    def _extract_sections(self, tree: DocumentTree) -> list[Section]:
        sections: list[Section] = []
        self._walk_for_sections(
            tree=tree,
            node_id=tree.root,
            heading_path=[],
            heading_level=0,
            sections=sections,
        )
        return sections

    def _walk_for_sections(
        self,
        *,
        tree: DocumentTree,
        node_id: str,
        heading_path: list[str],
        heading_level: int,
        sections: list[Section],
    ) -> None:
        node = tree.get(node_id)
        current_path = heading_path
        current_level = heading_level

        if node.kind == NodeKind.HEADING:
            current_path = heading_path + [node.content.strip()]
            current_level = node.data.level

        content_nodes: list[DocumentNode] = []
        subsection_ids: list[str] = []

        for child_id in node.children:
            child = tree.get(child_id)
            if child.kind == NodeKind.HEADING:
                subsection_ids.append(child_id)
            else:
                content_nodes.append(child)

        if content_nodes:
            sections.append(
                Section(
                    heading_path=current_path,
                    heading_level=current_level,
                    nodes=content_nodes,
                )
            )

        for subsection_id in subsection_ids:
            self._walk_for_sections(
                tree=tree,
                node_id=subsection_id,
                heading_path=current_path,
                heading_level=current_level,
                sections=sections,
            )

    def _sections_to_hierarchical_chunks(
        self,
        *,
        sections: list[Section],
        source_url: str,
        page_title: str,
        start_index: int = 0,
    ) -> list[Chunk]:
        all_chunks: list[Chunk] = []
        parent_index = start_index
        child_index = start_index

        for section_index, section in enumerate(sections):
            section_parts = self.hierarchy.split_section_into_parts(section)

            for part in section_parts:
                parents = self.hierarchy.build_parent_chunks(
                    section=part,
                    source_url=source_url,
                    page_title=page_title,
                    chunk_index=parent_index,
                    section_index=section_index,
                    prefix_fn=self._maybe_prefix,
                )
                if not parents:
                    continue

                children = self._chunk_section(
                    section=part,
                    source_url=source_url,
                    page_title=page_title,
                    start_index=child_index,
                    chunk_level=ChunkLevel.CHILD,
                    section_index=section_index,
                )

                self.hierarchy.link_parents_to_children(parents, children)

                all_chunks.extend(parents)
                all_chunks.extend(children)

                parent_index += len(parents)
                child_index += len(children)

        return all_chunks

    def _sections_to_chunks(
        self,
        *,
        sections: list[Section],
        source_url: str,
        page_title: str,
        start_index: int = 0,
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        chunk_index = start_index

        for section in sections:
            section_chunks = self._chunk_section(
                section=section,
                source_url=source_url,
                page_title=page_title,
                start_index=chunk_index,
            )
            chunks.extend(section_chunks)
            chunk_index += len(section_chunks)

        return chunks

    def _chunk_section(
        self,
        *,
        section: Section,
        source_url: str,
        page_title: str,
        start_index: int,
        chunk_level: ChunkLevel = ChunkLevel.CHILD,
        section_index: int = 0,
    ) -> list[Chunk]:
        units = self._section_to_units(section)
        if not units:
            return []

        chunks: list[Chunk] = []
        buffer_nodes: list[DocumentNode] = []
        buffer_text_parts: list[str] = []
        buffer_tokens = 0
        local_index = 0

        def flush_buffer(is_continuation: bool = False) -> None:
            nonlocal buffer_nodes, buffer_text_parts, buffer_tokens, local_index

            if not buffer_text_parts:
                return

            content = "\n\n".join(buffer_text_parts)
            content = self._maybe_prefix(content, section.heading_path)

            chunk = self.enricher.build_chunk(
                content=content,
                section=Section(
                    heading_path=section.heading_path,
                    heading_level=section.heading_level,
                    nodes=list(buffer_nodes),
                ),
                source_url=source_url,
                page_title=page_title,
                chunk_index=start_index + local_index,
                token_count=self.counter.count(content),
                is_continuation=is_continuation,
                chunk_level=chunk_level,
                section_index=section_index,
                strategy=self._strategy_for_nodes(buffer_nodes),
            )
            chunks.append(chunk)
            local_index += 1

            buffer_nodes = []
            buffer_text_parts = []
            buffer_tokens = 0

        for unit_nodes, unit_text, unit_tokens, is_atomic, strategy, node in units:
            if self._uses_dedicated_splitter(node):
                flush_buffer()
                split_parts = self.content_splitter.split_node(node, unit_text)
                for part_index, part in enumerate(split_parts):
                    part = self._maybe_prefix(part, section.heading_path)
                    chunks.append(
                        self._build_section_chunk(
                            content=part,
                            section=section,
                            nodes=unit_nodes,
                            source_url=source_url,
                            page_title=page_title,
                            chunk_index=start_index + local_index,
                            is_continuation=part_index > 0,
                            chunk_level=chunk_level,
                            section_index=section_index,
                            strategy=strategy,
                        )
                    )
                    local_index += 1
                continue

            if is_atomic and unit_tokens > self.config.max_tokens:
                flush_buffer()
                split_parts = self.content_splitter.split_node(node, unit_text)
                for part_index, part in enumerate(split_parts):
                    part = self._maybe_prefix(part, section.heading_path)
                    chunks.append(
                        self._build_section_chunk(
                            content=part,
                            section=section,
                            nodes=unit_nodes,
                            source_url=source_url,
                            page_title=page_title,
                            chunk_index=start_index + local_index,
                            is_continuation=part_index > 0,
                            chunk_level=chunk_level,
                            section_index=section_index,
                            strategy=strategy,
                        )
                    )
                    local_index += 1
                continue

            if buffer_tokens + unit_tokens > self.config.max_tokens and buffer_text_parts:
                flush_buffer()

            if unit_tokens > self.config.max_tokens:
                split_parts = self.content_splitter.split_node(node, unit_text)
                for part_index, part in enumerate(split_parts):
                    part = self._maybe_prefix(part, section.heading_path)
                    chunks.append(
                        self._build_section_chunk(
                            content=part,
                            section=section,
                            nodes=unit_nodes,
                            source_url=source_url,
                            page_title=page_title,
                            chunk_index=start_index + local_index,
                            is_continuation=part_index > 0,
                            chunk_level=chunk_level,
                            section_index=section_index,
                            strategy=strategy,
                        )
                    )
                    local_index += 1
                continue

            buffer_nodes.extend(unit_nodes)
            buffer_text_parts.append(unit_text)
            buffer_tokens += unit_tokens

        flush_buffer()
        return chunks

    def _build_section_chunk(
        self,
        *,
        content: str,
        section: Section,
        nodes: list[DocumentNode],
        source_url: str,
        page_title: str,
        chunk_index: int,
        is_continuation: bool,
        chunk_level: ChunkLevel,
        section_index: int,
        strategy: ChunkStrategy,
    ) -> Chunk:
        return self.enricher.build_chunk(
            content=content,
            section=Section(
                heading_path=section.heading_path,
                heading_level=section.heading_level,
                nodes=nodes,
            ),
            source_url=source_url,
            page_title=page_title,
            chunk_index=chunk_index,
            token_count=self.counter.count(content),
            is_continuation=is_continuation,
            chunk_level=chunk_level,
            section_index=section_index,
            strategy=strategy,
        )

    def _uses_dedicated_splitter(self, node: DocumentNode) -> bool:
        if node.kind == NodeKind.CODE_BLOCK and self.config.split_oversized_code:
            return True
        if node.kind == NodeKind.TABLE and self.config.split_oversized_tables:
            return True
        return False

    def _section_to_units(
        self,
        section: Section,
    ) -> list[tuple[list[DocumentNode], str, int, bool, ChunkStrategy, DocumentNode]]:
        units: list[tuple[list[DocumentNode], str, int, bool, ChunkStrategy, DocumentNode]] = []

        for node in section.nodes:
            text = self.renderer.render(node)
            if not text.strip():
                continue

            tokens = self.counter.count(text)
            strategy = self._strategy_for_node(node)
            is_atomic = self._is_atomic_node(node)
            units.append(([node], text, tokens, is_atomic, strategy, node))

        return units

    def _strategy_for_node(self, node: DocumentNode) -> ChunkStrategy:
        if node.kind == NodeKind.CODE_BLOCK:
            return ChunkStrategy.CODE
        if node.kind == NodeKind.TABLE:
            return ChunkStrategy.TABLE
        return ChunkStrategy.PROSE

    def _strategy_for_nodes(self, nodes: list[DocumentNode]) -> ChunkStrategy:
        if not nodes:
            return ChunkStrategy.PROSE

        strategies = {self._strategy_for_node(node) for node in nodes}
        if len(strategies) == 1:
            return strategies.pop()

        return ChunkStrategy.PROSE

    def _is_atomic_node(self, node: DocumentNode) -> bool:
        if node.kind == NodeKind.CODE_BLOCK:
            return not self.config.split_oversized_code
        if node.kind == NodeKind.TABLE:
            return not self.config.split_oversized_tables
        return node.kind in self._ATOMIC_KINDS

    def _maybe_prefix(self, content: str, heading_path: list[str]) -> str:
        if not self.config.include_heading_prefix:
            return content

        return self.enricher.prefix_content(
            content,
            heading_path,
            self.config.prefix_heading_levels,
        )
