 import asyncio
 import json
 import threading
 from functools import partial
 from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
 from pathlib import Path

 import pytest

 from politescrape.core.config import ExtractConfig, RunConfig
 from politescrape.core.crawler import Crawler


 @pytest.mark.asyncio
 async def test_crawler_runs_against_local_fixtures(tmp_path: Path):
   fixtures_dir = Path(__file__).parent / "fixtures"

   handler = partial(SimpleHTTPRequestHandler, directory=str(fixtures_dir))
   server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
   host, port = server.server_address

   thread = threading.Thread(target=server.serve_forever, daemon=True)
   thread.start()

   urls = [
     f"http://{host}:{port}/page1.html",
     f"http://{host}:{port}/page2.html",
   ]

   config = RunConfig(
     input_urls=urls,
     output_jsonl_path=str(tmp_path / "out.jsonl"),
     user_agent="politescrape-test",
     global_concurrency=2,
     per_domain_concurrency=2,
     requests_per_second=5.0,
     timeout_seconds=5.0,
     retry_max_attempts=2,
     cache_dir=str(tmp_path / "cache"),
     checkpoint_db_path=str(tmp_path / "checkpoints.db"),
     extract=ExtractConfig(
       selectors={
         "title": "h1.title",
         "price": "div.price",
         "link": {"selector": "a.link", "attr": "href"},
       },
       schema={"title": "str", "price": "str", "link": "str"},
     ),
   )

   crawler = Crawler(config)
   stats = await crawler.run()
   server.shutdown()

   assert stats.success == 2
   lines = (tmp_path / "out.jsonl").read_text().splitlines()
   assert len(lines) == 2
   items = [json.loads(line) for line in lines]
   titles = {item["title"] for item in items}
   assert titles == {"Widget Alpha", "Widget Beta"}
