 """Pydantic configuration models for runs."""
 from __future__ import annotations

 from pathlib import Path
 from typing import List, Optional, Union

 from pydantic import BaseModel, Field, model_validator


 class ExtractConfig(BaseModel):
   selectors: dict[str, Union[str, dict]] = Field(
     ..., description="CSS selectors mapping fields to selectors."
   )
   schema: dict[str, str] = Field(
     ..., description="Field -> python type string (str, int, float, bool)."
   )


 class RunConfig(BaseModel):
   input_urls: List[str] = Field(default_factory=list)
   input_urls_path: Optional[str] = Field(
     None, description="Optional path to file containing one URL per line."
   )
   output_jsonl_path: str
   user_agent: str = Field(default="politescrape/0.1.0")
   global_concurrency: int = 5
   per_domain_concurrency: int = 2
   requests_per_second: Optional[float] = Field(
     None, description="Global RPS limit; per-domain inferred from robots or same as global."
   )
   timeout_seconds: float = 10.0
   retry_max_attempts: int = 3
   cache_dir: Optional[str] = None
   checkpoint_db_path: str = "./.politescrape/checkpoints.db"
   extract: ExtractConfig

   @model_validator(mode="after")
   def populate_urls(cls, values: "RunConfig") -> "RunConfig":
     if not values.input_urls and values.input_urls_path:
       path = Path(values.input_urls_path)
       values.input_urls = [line.strip() for line in path.read_text().splitlines() if line.strip()]
     if not values.input_urls:
       raise ValueError("No input URLs provided.")
     return values
