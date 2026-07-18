from crawl4ai import AsyncWebCrawler


class WebsiteCrawler:
    def __init__(self):
        self.crawler = AsyncWebCrawler()

    async def crawl(self, url: str):
        async with self.crawler:
            result = await self.crawler.arun(url=url)
            return result
   
        

