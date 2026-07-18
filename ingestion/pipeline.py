from ingestion.crawler import WebsiteCrawler
from ingestion.extractor import CrawlResultExtractor


class IngestionPipeline:

    def __init__(self):
        self.crawler = WebsiteCrawler()
        self.extractor = CrawlResultExtractor()

    async def run(self, url: str):
        crawl_result = await self.crawler.crawl(url)
        print(crawl_result.metadata)
        print(crawl_result.links)


        document = self.extractor.extract(crawl_result)

        return document