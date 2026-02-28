 """Typer CLI entrypoint."""
 from __future__ import annotations

 import asyncio
 from pathlib import Path
 from typing import Optional

 import typer
 import yaml

 from politescrape.core.config import RunConfig
 from politescrape.core.crawler import Crawler
 from politescrape.utils.logging import configure_logging, get_logger

 app = typer.Typer(help="PoliteScrape - polite-by-default web scraping framework.")

 logger = get_logger(component="cli")


 def load_config(path: Path) -> RunConfig:
   data = yaml.safe_load(path.read_text())
   return RunConfig(**data)


 def render_summary(stats, output_path: str) -> None:
   headers = ["total", "success", "failed", "skipped", "output"]
   values = [str(stats.total), str(stats.success), str(stats.failed), str(stats.skipped), output_path]
   widths = [max(len(h), len(v)) for h, v in zip(headers, values)]
   sep = "+".join("-" * (w + 2) for w in widths)
   row = lambda cells: "|".join(f" {c.ljust(w)} " for c, w in zip(cells, widths))  # noqa: E731
   print(sep)
   print(row(headers))
   print(sep)
   print(row(values))
   print(sep)


 @app.command()
 def run(config_path: Path, log_level: str = typer.Option("INFO", help="Log level (INFO/DEBUG)")) -> None:
   """Run a crawl using a YAML config."""
   configure_logging(log_level)
   config = load_config(config_path)
   crawler = Crawler(config)
   stats = asyncio.run(crawler.run())
   render_summary(stats, config.output_jsonl_path)
   logger.info("completed", output=config.output_jsonl_path)


 if __name__ == "__main__":
   app()
