import asyncio

from ingestion.pipeline import IngestionPipeline


async def main():
    pipeline = IngestionPipeline()

    documents = await pipeline.run(
        "https://docs.langchain.com"
    )

    print(f"Crawled {len(documents)} pages")

    for doc in documents:
        print(doc.url)


if __name__ == "__main__":
    asyncio.run(main())