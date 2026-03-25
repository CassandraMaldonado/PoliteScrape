# Retrieval and eval.
 from __future__ import annotations

 import asyncio
 from typing import Dict, Optional
 from urllib.parse import urlparse, urljoin
 from urllib.robotparser import RobotFileParser

 import httpx

 from politescrape.utils.logging import get_logger

 logger = get_logger(component="robots")

# Fetch and cache robots.txt per domain.
 class RobotsCache:

   def __init__(self, user_agent: str, timeout: float = 5.0) -> None:
     self.user_agent = user_agent
     self.timeout = timeout
     self.cache: Dict[str, RobotFileParser] = {}
     self._locks: Dict[str, asyncio.Lock] = {}

   def _domain(self, url: str) -> str:
     return urlparse(url).netloc

   def _robots_url(self, url: str) -> str:
     parsed = urlparse(url)
     return urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")

   async def _fetch_robots(self, robots_url: str) -> RobotFileParser:
     rp = RobotFileParser()
     try:
       async with httpx.AsyncClient(timeout=self.timeout) as client:
         response = await client.get(robots_url)
         if response.status_code == 200:
           rp.parse(response.text.splitlines())
         else:
           logger.info("robots_not_found", url=robots_url, status=response.status_code)
           rp.parse("")  # treat as empty allow-all
     except Exception as exc:  # noqa: BLE001
       logger.warning("robots_fetch_error", url=robots_url, error=str(exc))
       rp.parse("")  # default to allow in absence; caller should keep low rate
     return rp

   async def _get_parser(self, url: str) -> RobotFileParser:
     domain = self._domain(url)
     if domain in self.cache:
       return self.cache[domain]

     lock = self._locks.setdefault(domain, asyncio.Lock())
     async with lock:
       if domain in self.cache:
         return self.cache[domain]
       robots_url = self._robots_url(url)
       parser = await self._fetch_robots(robots_url)
       self.cache[domain] = parser
       return parser

    
# Return whether URL is allowed for configured user agent.
   async def is_allowed(self, url: str) -> bool:
     parser = await self._get_parser(url)
     return parser.can_fetch(self.user_agent, url)

  #      """Return crawl-delay if provided by robots.txt."""
   async def crawl_delay(self, url: str) -> Optional[float]:
     parser = await self._get_parser(url)
     delay = parser.crawl_delay(self.user_agent)
     return float(delay) if delay is not None else None
