# Async HTTP fetching with retries and backoff.
 from __future__ import annotations

 import base64
 import json
 import os
 from dataclasses import dataclass
 from pathlib import Path
 from typing import Dict, Optional

 import httpx
 from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

 from politescrape.utils.hashing import sha256_hex
 from politescrape.utils.logging import get_logger
 from politescrape.utils.time import utc_now

 logger = get_logger(component="fetcher")


 @dataclass
 class FetchResult:
   url: str
   status_code: int
   headers: Dict[str, str]
   content: bytes
   from_cache: bool
   sha256: str
   fetched_at: str


 class DiskCache:

   def __init__(self, cache_dir: Optional[str]) -> None:
     self.cache_dir = Path(cache_dir) if cache_dir else None
     if self.cache_dir:
       self.cache_dir.mkdir(parents=True, exist_ok=True)

   def _path(self, url: str) -> Optional[Path]:
     if not self.cache_dir:
       return None
     return self.cache_dir / f"{sha256_hex(url)}.json"

   def read(self, url: str) -> Optional[FetchResult]:
     path = self._path(url)
     if not path or not path.exists():
       return None
     try:
       data = json.loads(path.read_text())
       content = base64.b64decode(data["content_b64"])
       return FetchResult(
         url=url,
         status_code=data["status_code"],
         headers=data.get("headers", {}),
         content=content,
         from_cache=True,
         sha256=sha256_hex(content),
         fetched_at=data.get("fetched_at", utc_now().isoformat()),
       )
     except Exception as exc:  # noqa: BLE001
       logger.warning("cache_read_failed", path=str(path), error=str(exc))
       return None

   def write(self, result: FetchResult) -> None:
     path = self._path(result.url)
     if not path:
       return
     try:
       payload = {
         "status_code": result.status_code,
         "headers": result.headers,
         "content_b64": base64.b64encode(result.content).decode("utf-8"),
         "fetched_at": result.fetched_at,
       }
       path.write_text(json.dumps(payload))
     except Exception as exc:  # noqa: BLE001
       logger.warning("cache_write_failed", path=str(path), error=str(exc))


 class AsyncFetcher:
   """HTTP client with retry/backoff and caching."""

   def __init__(
     self,
     user_agent: str,
     timeout: float = 10.0,
     retry_attempts: int = 3,
     backoff_base: float = 0.5,
     cache_dir: Optional[str] = None,
   ) -> None:
     self.user_agent = user_agent
     self.timeout = timeout
     self.retry_attempts = retry_attempts
     self.backoff_base = backoff_base
     self.cache = DiskCache(cache_dir)
     self._client = httpx.AsyncClient(
       timeout=timeout,
       headers={"User-Agent": user_agent},
       follow_redirects=True,
     )

   async def close(self) -> None:
     await self._client.aclose()

   async def fetch(self, url: str, use_cache: bool = True) -> FetchResult:
     if use_cache:
       cached = self.cache.read(url)
       if cached:
         return cached

     async for attempt in AsyncRetrying(
       stop=stop_after_attempt(self.retry_attempts),
       retry=retry_if_exception_type(httpx.HTTPError),
       wait=wait_exponential_jitter(initial=self.backoff_base, max=self.backoff_base * 8),
     ):
       with attempt:
         response = await self._client.get(url)
         content = response.content
         result = FetchResult(
           url=url,
           status_code=response.status_code,
           headers=dict(response.headers),
           content=content,
           from_cache=False,
           sha256=sha256_hex(content),
           fetched_at=utc_now().isoformat(),
         )
         if use_cache:
           self.cache.write(result)
         return result

     raise RuntimeError(f"Unable to fetch {url}")
