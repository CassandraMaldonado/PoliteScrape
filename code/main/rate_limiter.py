# Async rate limiter with domain and global controls.
 from __future__ import annotations

 import asyncio
 import random
 import time
 from contextlib import asynccontextmanager
 from typing import Dict, Optional
 from urllib.parse import urlparse

# Using a simple bucket approach and small random delays to avoid request spikes.
 class RateLimiter:

   def __init__(
     self,
     global_concurrency: int = 5,
     per_domain_concurrency: int = 2,
     global_rps: Optional[float] = None,
     per_domain_rps: Optional[float] = None,
     jitter_ratio: float = 0.3,
   ) -> None:
     self.global_sem = asyncio.Semaphore(global_concurrency)
     self.per_domain_sem: Dict[str, asyncio.Semaphore] = {}
    self.per_domain_concurrency = per_domain_concurrency
     self.global_rps = global_rps
     self.per_domain_rps = per_domain_rps
     self.jitter_ratio = jitter_ratio
     self._last_global: float = 0.0
     self._last_domain: Dict[str, float] = {}
     self._lock = asyncio.Lock()

   def _domain(self, url: str) -> str:
     parsed = urlparse(url)
     return parsed.netloc or url

   async def _ensure_domain(self, domain: str) -> None:
     if domain not in self.per_domain_sem:
      self.per_domain_sem[domain] = asyncio.Semaphore(self.per_domain_concurrency)
       # Above sets minimal capacity; actual rate handled via sleeps.
       self._last_domain[domain] = 0.0

   async def _sleep_for_rate(self, last: float, rps: Optional[float]) -> None:
     if not rps:
       return
     min_interval = 1.0 / rps
     elapsed = time.monotonic() - last
     wait = max(0.0, min_interval - elapsed)
     jitter = random.uniform(0, min_interval * self.jitter_ratio) if wait > 0 else 0.0
     if wait + jitter > 0:
       await asyncio.sleep(wait + jitter)

# Async context to guard a request.
   @asynccontextmanager
   async def limit(self, url: str):
     domain = self._domain(url)
     async with self._lock:
       await self._ensure_domain(domain)
     await self.global_sem.acquire()
     await self.per_domain_sem[domain].acquire()
     try:
       await self._sleep_for_rate(self._last_global, self.global_rps)
       await self._sleep_for_rate(self._last_domain.get(domain, 0.0), self.per_domain_rps)
       yield
     finally:
       now = time.monotonic()
       self._last_global = now
       self._last_domain[domain] = now
       self.per_domain_sem[domain].release()
       self.global_sem.release()
