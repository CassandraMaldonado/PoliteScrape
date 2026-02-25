 # PoliteScrape Architecture


 flowchart TD
   CLI[Typer CLI] --> Config[RunConfig (pydantic)]
   Config --> Crawler
   Crawler --> Robots[RobotsCache]
   Crawler --> RateLimiter
   Crawler --> Fetcher[AsyncFetcher/httpx+tenacity]
   Fetcher --> Cache[Disk cache]
   Crawler --> Extractor[CSSExtractor + Pydantic]
   Crawler --> Jsonl[JSONL sink]
   Crawler --> Meta[SQLite checkpoints]


 ## Components
 - **CLI**: Loads YAML config, initializes crawler.
 - **Crawler**: Orchestrates robots checks, rate limiting, fetch, extraction, persistence, and stats.
 - **RobotsCache**: Fetches and caches robots.txt, exposes `is_allowed` and `crawl_delay`.
 - **RateLimiter**: Per-domain/global semaphores plus RPS sleep with jitter.
 - **AsyncFetcher**: httpx AsyncClient with retries/backoff (tenacity) and optional disk cache.
 - **CSSExtractor**: BeautifulSoup CSS selectors to dict, validated by a generated Pydantic model.
 - **Storage**: JSONL sink for items; SQLite for metadata/checkpoints.
 - **Utils**: Structured logging (structlog), hashing, time helpers.
