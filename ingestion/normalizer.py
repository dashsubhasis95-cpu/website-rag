from urllib.parse import urlsplit, urlunsplit

from ingestion.models import CrawledDocument, Link, PageLinks


class DocumentNormalizer:
    def normalize(self, document: CrawledDocument) -> CrawledDocument:
        normalized_url = self._normalize_url(document.url)

        normalized_links = self._normalize_links(document.links)

        return CrawledDocument(
            url=normalized_url,
            markdown=document.markdown,
            html=document.html,
            metadata=document.metadata,
            links=normalized_links,
            extra=document.extra,
        )

    def _normalize_url(self, url: str) -> str:
        url = url.strip()

        parsed = urlsplit(url)

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        path = parsed.path.rstrip("/")

        normalized = urlunsplit(
            (
                scheme,
                netloc,
                path,
                parsed.query,
                "",
            )
        )

        return normalized

    def _normalize_links(self, links: PageLinks) -> PageLinks:
        internal = [
            Link(
                href=self._normalize_url(link.href),
                text=link.text,
                title=link.title,
                base_domain=link.base_domain,
            )
            for link in links.internal
        ]

        external = [
            Link(
                href=self._normalize_url(link.href),
                text=link.text,
                title=link.title,
                base_domain=link.base_domain,
            )
            for link in links.external
        ]

        return PageLinks(
            internal=internal,
            external=external,
        )