import asyncio

from ingestion.pipeline import IngestionPipeline


async def main():
    pipeline = IngestionPipeline()

    documents = await pipeline.run(
        "https://docs.langchain.com",
        max_pages=10,
        max_depth=2,
    )

    print(f"Crawled {len(documents)} pages")

    for document in documents:
        print(document.url)


if __name__ == "__main__":
    asyncio.run(main())