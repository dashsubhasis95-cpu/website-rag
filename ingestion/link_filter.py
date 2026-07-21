from urllib.parse import urlparse

from ingestion.models import Link


class LinkFilter:
    UNSUPPORTED_EXTENSIONS = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".zip",
        ".exe",
    }

    def __init__(
        self,
        allowed_domains: set[str],
        allow_external: bool = False,
    ):
        self.allowed_domains = allowed_domains
        self.allow_external = allow_external

    def is_allowed(self, link: Link) -> bool:
        href = link.href

        if not self._is_valid(href):
            return False

        if not self._is_http(href):
            return False

        if self._has_unsupported_extension(href):
            return False

        if not self.allow_external and not self._is_same_domain(href):
            return False

        return True

    def _is_valid(self, href: str) -> bool:
        return bool(href)

    def _is_http(self, href: str) -> bool:
        scheme = urlparse(href).scheme
        return scheme in {"http", "https"}

    def _has_unsupported_extension(self, href: str) -> bool:
        path = urlparse(href).path.lower()

        return any(
            path.endswith(extension)
            for extension in self.UNSUPPORTED_EXTENSIONS
        )

    def _is_same_domain(self, href: str) -> bool:
        domain = urlparse(href).netloc.lower()

        return domain in self.allowed_domains