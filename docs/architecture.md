 # PoliteScrape Architecture


flowchart TD

    subgraph Interface
        CLI[Typer CLI]
        Config[RunConfig (Pydantic)]
        CLI --> Config
    end

    subgraph Core Crawler
        Crawler
        Robots[RobotsCache]
        RateLimiter
        Fetcher[AsyncFetcher (httpx + tenacity)]
        Extractor[CSSExtractor + Pydantic Models]

        Crawler --> Robots
        Crawler --> RateLimiter
        Crawler --> Fetcher
        Crawler --> Extractor
    end

    subgraph Storage
        Cache[Disk Cache]
        Jsonl[JSONL Sink]
        Meta[SQLite Checkpoints]

        Fetcher --> Cache
        Crawler --> Jsonl
        Crawler --> Meta
    end

    Config --> Crawler


 ## Components
 - **CLI**: Loads YAML config, initializes crawler.
 - **Crawler**: Orchestrates robots checks, rate limiting, fetch, extraction, persistence, and stats.
 - **RobotsCache**: Fetches and caches robots.txt, exposes `is_allowed` and `crawl_delay`.
 - **RateLimiter**: Per-domain/global semaphores plus RPS sleep with jitter.
 - **AsyncFetcher**: httpx AsyncClient with retries/backoff (tenacity) and optional disk cache.
 - **CSSExtractor**: BeautifulSoup CSS selectors to dict, validated by a generated Pydantic model.
 - **Storage**: JSONL sink for items; SQLite for metadata/checkpoints.
 - **Utils**: Structured logging (structlog), hashing, time helpers.
