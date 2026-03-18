# Crawl engine orchestrating fetch, robots, rate limiting, extraction and sinks.
 from __future__ import annotations

 import asyncio
 from dataclasses import dataclass
 from typing import List

 from politescrape.core.config import RunConfig
 from politescrape.core.fetcher import AsyncFetcher
 from politescrape.core.rate_limiter import RateLimiter
 from politescrape.core.robots import RobotsCache
 from politescrape.extract.extractor import CSSExtractor, build_model, parse_selectors
 from politescrape.storage.jsonl_sink import JsonlSink
 from politescrape.storage.sqlite_sink import MetadataStore
 from politescrape.utils.logging import get_logger

 logger = get_logger(component="crawler")


 @dataclass
 class CrawlStats:
   total: int = 0
   success: int = 0
   failed: int = 0
   skipped: int = 0


 class Crawler:
   """High-level orchestrator for polite scraping."""

   def __init__(self, config: RunConfig) -> None:
     self.config = config
     self.robots = RobotsCache(user_agent=config.user_agent)
     self.rate_limiter = RateLimiter(
       global_concurrency=config.global_concurrency,
       per_domain_concurrency=config.per_domain_concurrency,
       global_rps=config.requests_per_second,
       per_domain_rps=None,
     )
     self.fetcher = AsyncFetcher(
       user_agent=config.user_agent,
       timeout=config.timeout_seconds,
       retry_attempts=config.retry_max_attempts,
       cache_dir=config.cache_dir,
     )
     model = build_model("ExtractedItem", config.extract.schema)
     selectors = parse_selectors(config.extract.selectors)
     self.extractor = CSSExtractor(selectors=selectors, model=model)
     self.jsonl_sink = JsonlSink(config.output_jsonl_path)
     self.metadata = MetadataStore(config.checkpoint_db_path)
     self.stats = CrawlStats(total=len(config.input_urls))

   async def _handle_url(self, url: str) -> None:
     if self.metadata.is_completed(url):
       self.stats.skipped += 1
       return

     allowed = await self.robots.is_allowed(url)
     if not allowed:
       logger.info("blocked_by_robots", url=url)
       self.metadata.record(url, status="blocked", error="robots_disallow")
       self.stats.skipped += 1
       return

     crawl_delay = await self.robots.crawl_delay(url)
     if crawl_delay:
       await asyncio.sleep(crawl_delay)

     async with self.rate_limiter.limit(url):
       try:
         result = await self.fetcher.fetch(url, use_cache=bool(self.config.cache_dir))
         text = result.content.decode("utf-8", errors="ignore")
         item = self.extractor.extract(text)
         payload = item.model_dump()
         payload.update({"url": url, "fetched_at": result.fetched_at, "sha256": result.sha256})
         self.jsonl_sink.write(payload)
         self.metadata.record(url, status="success", fetched_at=result.fetched_at, sha256=result.sha256)
         self.stats.success += 1
       except Exception as exc:  # noqa: BLE001
         logger.error("fetch_failed", url=url, error=str(exc))
         self.metadata.record(url, status="failed", error=str(exc))
         self.stats.failed += 1

   async def run(self) -> CrawlStats:
     await asyncio.gather(*(self._handle_url(url) for url in self.config.input_urls))
     await self.fetcher.close()
     logger.info(
       "crawl_summary",
       total=self.stats.total,
       success=self.stats.success,
       failed=self.stats.failed,
       skipped=self.stats.skipped,
     )
     return self.stats
