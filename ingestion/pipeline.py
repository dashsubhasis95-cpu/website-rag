from urllib.parse import urlparse

from ingestion.bfs_crawler import BFSCrawler
from ingestion.crawler import WebsiteCrawler
from ingestion.extractor import CrawlResultExtractor
from ingestion.link_filter import LinkFilter
from ingestion.normalizer import DocumentNormalizer


class IngestionPipeline:
    def __init__(self):
        crawler = WebsiteCrawler()
        extractor = CrawlResultExtractor()
        normalizer = DocumentNormalizer()

        allowed_domain = urlparse("https://docs.langchain.com").netloc

        link_filter = LinkFilter(
            allowed_domains={allowed_domain},
        )

        self.crawler = BFSCrawler(
            crawler,
            extractor,
            normalizer,
            link_filter,
        )

    async def run(self, url: str):
        return await self.crawler.crawl(
            start_url=url,
            max_pages=20,
            max_depth=2,
        )