from dataclasses import dataclass, field
from typing import Any


@dataclass
class Link:
    href: str
    text: str
    title: str
    base_domain: str


@dataclass
class PageLinks:
    internal: list[Link] = field(default_factory=list)
    external: list[Link] = field(default_factory=list)


@dataclass
class PageMetadata:
    title: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class CrawledDocument:
    url: str
    markdown: str
    html: str

    metadata: PageMetadata
    links: PageLinks

    extra: dict[str, Any] = field(default_factory=dict)