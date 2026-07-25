from collections import deque

from ingestion.crawler import WebsiteCrawler
from ingestion.extractor import CrawlResultExtractor
from ingestion.link_filter import LinkFilter
from ingestion.normalizer import DocumentNormalizer


class BFSCrawler:
    def __init__(
        self,
        crawler: WebsiteCrawler,
        extractor: CrawlResultExtractor,
        normalizer: DocumentNormalizer,
        link_filter: LinkFilter,
    ):
        self.crawler = crawler
        self.extractor = extractor
        self.normalizer = normalizer
        self.link_filter = link_filter

    async def crawl(
        self,
        start_url: str,
        max_pages: int = 20,
        max_depth: int = 2,
    ):
        queue = deque([(start_url, 0)])
        queued = {start_url}
        visited = set()
        documents = []

        async with self.crawler:

            while queue and len(documents) < max_pages:

                url, depth = queue.popleft()

                if url in visited:
                    continue

                visited.add(url)

                try:
                    crawl_result = await self.crawler.crawl(url)

                    document = self.extractor.extract(crawl_result)
                    document = self.normalizer.normalize(document)

                    documents.append(document)

                    # Stop expanding if max depth is reached
                    if depth >= max_depth:
                        continue

                    for link in document.links.internal:

                        if not self.link_filter.is_allowed(link):
                            continue

                        if (
                            link.href not in visited
                            and link.href not in queued
                        ):
                            queue.append((link.href, depth + 1))
                            queued.add(link.href)

                except Exception as e:
                    print(f"Failed to crawl {url}: {e}")

        return documents