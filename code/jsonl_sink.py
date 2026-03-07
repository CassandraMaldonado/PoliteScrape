 """Append-only JSONL sink."""
 from __future__ import annotations

 import json
 from pathlib import Path
 from typing import Any, Dict


 class JsonlSink:
   """Append objects as JSON lines."""

   def __init__(self, path: str) -> None:
     self.path = Path(path)
     self.path.parent.mkdir(parents=True, exist_ok=True)

   def write(self, item: Dict[str, Any]) -> None:
     with self.path.open("a", encoding="utf-8") as fh:
       fh.write(json.dumps(item, ensure_ascii=False) + "\n")
