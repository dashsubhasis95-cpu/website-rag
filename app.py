import asyncio

from ingestion.pipeline import IngestionPipeline


async def main():
    pipeline = IngestionPipeline()

    document = await pipeline.run(
        "https://docs.langchain.com"
    )
    print(document.url)
    print(document.metadata.title)

    print()

    print(document.links.internal[0])

    print()

    print(document.markdown[:500])


if __name__ == "__main__":
    asyncio.run(main())