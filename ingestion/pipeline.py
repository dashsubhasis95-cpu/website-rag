from ingestion.crawler import WebsiteCrawler
from ingestion.extractor import CrawlResultExtractor
from ingestion.normalizer import DocumentNormalizer


class IngestionPipeline:

    def __init__(self):
        self.crawler = WebsiteCrawler()
        self.extractor = CrawlResultExtractor()
        self.normalizer = DocumentNormalizer()

    async def run(self, url: str):
        crawl_result = await self.crawler.crawl(url)

        document = self.extractor.extract(crawl_result)

        document = self.normalizer.normalize(document)

        return document