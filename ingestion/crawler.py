from crawl4ai import AsyncWebCrawler


class WebsiteCrawler:
    def __init__(self):
        self.crawler = AsyncWebCrawler()

    async def __aenter__(self):
        await self.crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.crawler.__aexit__(exc_type, exc_val, exc_tb)

    async def crawl(self, url: str):
        return await self.crawler.arun(url=url)
