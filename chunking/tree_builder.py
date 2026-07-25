from chunking.models import (
    DocumentNode,
    DocumentTree,
    NodeKind,
)


class DocumentTreeBuilder:
    def __init__(self):
        root = DocumentNode(
            kind=NodeKind.DOCUMENT,
            content="Document",
        )

        self.tree = DocumentTree(
            root=root.id,
        )

        self.tree.add_node(root)

    @property
    def root(self) -> DocumentNode:
        return self.tree.get(self.tree.root)

    def create_node(
        self,
        kind: NodeKind,
        content: str = "",
        data=None,
    ) -> DocumentNode:

        return DocumentNode(
            kind=kind,
            content=content,
            data=data,
        )

    def append_child(
        self,
        parent: DocumentNode,
        child: DocumentNode,
    ) -> None:

        self.tree.add_child(
            parent.id,
            child,
        )

    def build(self) -> DocumentTree:
        return self.tree