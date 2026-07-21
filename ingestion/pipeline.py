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

        link_filter = LinkFilter(
            allowed_domains={"docs.langchain.com"}
        )

        self.crawler = BFSCrawler(
            crawler,
            extractor,
            normalizer,
            link_filter,
        )

    async def run(self, url: str):
        return await self.crawler.crawl(
            url,
            max_pages=20,
        )