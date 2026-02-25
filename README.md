 # PoliteScrape

 Polite async web scraping framework and CLI. Focused on robots.txt awareness, per-domain throttling, retries/backoff, and resumable checkpoints.

 ## Features
 - Robots.txt fetch + cache; respects Disallow and crawl-delay (defaults to allow with low rate when robots is missing).
 - Per-domain and global concurrency/RPS with jittered sleeps.
 - Async httpx fetcher with timeouts, retry + exponential backoff (tenacity), optional disk cache.
 - CSS selector extraction validated via generated Pydantic model.
 - Storage: append-only JSONL for items, SQLite for metadata + checkpoints (skips completed URLs on rerun).
 - Typer CLI plus library API; structured logging via structlog.
 - Tests (unit + integration with local fixtures), linting (ruff), formatting (black), typing (mypy), CI workflow.

 ## Quickstart
 ```bash
 python -m venv .venv && source .venv/bin/activate
 pip install -e ".[dev]"

 # Serve the example HTML locally
 cd examples && python -m http.server 8000
 # In another shell
 politescrape run examples/config.yaml
 ```

 Output lands in `output/example.jsonl`; checkpoints in `.politescrape/checkpoints.db`.

 ## Config example
 ```yaml
 input_urls:
   - "http://127.0.0.1:8000/sample.html"
 output_jsonl_path: "./output/example.jsonl"
 user_agent: "politescrape-example"
 global_concurrency: 2
 per_domain_concurrency: 2
 requests_per_second: 2.0
 timeout_seconds: 5.0
 retry_max_attempts: 2
 cache_dir: "./.cache"
 checkpoint_db_path: "./.politescrape/checkpoints.db"
 extract:
   schema:
     title: "str"
     price: "str"
     link: "str"
   selectors:
     title: "h1.title"
     price: "div.price"
     link:
       selector: "a.link"
       attr: "href"
 ```

 Run: `politescrape run examples/config.yaml`.

 ## Architecture (Mermaid)
 ```mermaid
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
 ```

 ## Ethical scraping
 - Respect robots.txt: requests are checked and cached per domain; crawl-delay honored when provided.
 - Default to conservative behavior: if robots cannot be fetched, requests proceed with the configured throttling; consider lowering RPS in such cases.
 - Identify yourself: configure a descriptive `user_agent` with contact info.
 - Avoid unnecessary load: use caching, retries with backoff, and checkpoints to prevent duplicate hits.
 - Keep fixtures local: examples/tests never hit real commercial sites.

 ## Library usage
 ```python
 import asyncio
 from politescrape.core.config import ExtractConfig, RunConfig
 from politescrape.core.crawler import Crawler

 config = RunConfig(
   input_urls=["http://127.0.0.1:8000/sample.html"],
   output_jsonl_path="./output/example.jsonl",
   extract=ExtractConfig(
     schema={"title": "str"},
     selectors={"title": "h1.title"},
   ),
 )

 asyncio.run(Crawler(config).run())
 ```

 ## Development
 - Lint: `ruff check .`
 - Format: `black .`
 - Type-check: `mypy politescrape`
 - Tests: `pytest`
