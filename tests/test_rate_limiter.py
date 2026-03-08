 import asyncio
 import time

 import pytest

 from politescrape.core.rate_limiter import RateLimiter


 @pytest.mark.asyncio
 async def test_rate_limiter_respects_rps():
   limiter = RateLimiter(
     global_concurrency=1,
     per_domain_concurrency=1,
     global_rps=2.0,  # 2 requests/sec -> 0.5s interval
     per_domain_rps=2.0,
     jitter_ratio=0.0,
   )

   async def do_request():
     async with limiter.limit("https://example.test"):
       return time.perf_counter()

   t0 = time.perf_counter()
   first = await do_request()
   second = await do_request()
   elapsed_between = second - first


   assert elapsed_between >= 0.45
   assert (time.perf_counter() - t0) >= 0.9
