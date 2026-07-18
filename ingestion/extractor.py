from ingestion.models import (
    CrawledDocument,
    Link,
    PageLinks,
    PageMetadata,
)


class CrawlResultExtractor:

    def extract(self, result) -> CrawledDocument:
        metadata = self._extract_metadata(result.metadata or {})
        links = self._extract_links(result.links or {})

        return CrawledDocument(
            url=result.url,
            markdown=result.markdown,
            html=result.html,
            metadata=metadata,
            links=links,
            extra={},
        )

    def _extract_metadata(self, metadata: dict) -> PageMetadata:
        return PageMetadata(
            title=metadata.get("title", ""),
            raw=metadata,
        )

    def _extract_links(self, links: dict) -> PageLinks:
        internal_links = [
            self._build_link(link)
            for link in links.get("internal", [])
        ]

        external_links = [
            self._build_link(link)
            for link in links.get("external", [])
        ]

        return PageLinks(
            internal=internal_links,
            external=external_links,
        )

    def _build_link(self, link: dict) -> Link:
        return Link(
            href=link.get("href", ""),
            text=link.get("text", ""),
            title=link.get("title", ""),
            base_domain=link.get("base_domain", ""),
        )