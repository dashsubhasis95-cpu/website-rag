from urllib.parse import urlparse

from ingestion.bfs_crawler import BFSCrawler
from ingestion.crawler import WebsiteCrawler
from ingestion.extractor import CrawlResultExtractor
from ingestion.link_filter import LinkFilter
from ingestion.normalizer import DocumentNormalizer


class IngestionPipeline:
    def __init__(self):
        self.crawler = WebsiteCrawler()
        self.extractor = CrawlResultExtractor()
        self.normalizer = DocumentNormalizer()

    async def run(
        self,
        url: str,
        max_pages: int = 20,
        max_depth: int = 2,
    ):
        allowed_domain = urlparse(url).netloc.lower()

        link_filter = LinkFilter(
            allowed_domains={allowed_domain},
        )

        bfs_crawler = BFSCrawler(
            crawler=self.crawler,
            extractor=self.extractor,
            normalizer=self.normalizer,
            link_filter=link_filter,
        )

        return await bfs_crawler.crawl(
            start_url=url,
            max_pages=max_pages,
            max_depth=max_depth,
        )