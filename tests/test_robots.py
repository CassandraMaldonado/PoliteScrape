 import httpx
 import pytest

 from politescrape.core.robots import RobotsCache


 @pytest.mark.asyncio
 async def test_robots_respects_disallow(monkeypatch):
   robots_txt = """
   User-agent: politescrape
   Disallow: /private
   """

   class FakeClient:
     def __init__(self, *args, **kwargs):
       pass

     async def __aenter__(self):
       return self

     async def __aexit__(self, exc_type, exc, tb):
       return False

     async def get(self, url):
       return httpx.Response(200, text=robots_txt)

   monkeypatch.setattr(httpx, "AsyncClient", FakeClient)
   cache = RobotsCache(user_agent="politescrape")

   assert not await cache.is_allowed("https://example.test/private")
   assert await cache.is_allowed("https://example.test/public")
