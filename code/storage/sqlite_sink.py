 from __future__ import annotations

 import sqlite3
 from pathlib import Path
 from typing import Optional

# Fetch metadata and completion checkpoints.
 class MetadataStore:

   def __init__(self, db_path: str) -> None:
     self.db_path = Path(db_path)
     self.db_path.parent.mkdir(parents=True, exist_ok=True)
     self._ensure_schema()

   def _connect(self) -> sqlite3.Connection:
     return sqlite3.connect(self.db_path)

   def _ensure_schema(self) -> None:
     with self._connect() as conn:
       conn.execute(
         """
         CREATE TABLE IF NOT EXISTS fetch_metadata (
           url TEXT PRIMARY KEY,
           status TEXT,
           fetched_at TEXT,
           sha256 TEXT,
           error TEXT
         )
         """
       )
       conn.commit()

   def is_completed(self, url: str) -> bool:
     with self._connect() as conn:
       row = conn.execute("SELECT status FROM fetch_metadata WHERE url = ?", (url,)).fetchone()
       return bool(row and row[0] == "success")

   def record(
     self,
     url: str,
     status: str,
     fetched_at: Optional[str] = None,
     sha256: Optional[str] = None,
     error: Optional[str] = None,
   ) -> None:
     with self._connect() as conn:
       conn.execute(
         """
         INSERT INTO fetch_metadata (url, status, fetched_at, sha256, error)
         VALUES (?, ?, ?, ?, ?)
         ON CONFLICT(url) DO UPDATE SET
           status=excluded.status,
           fetched_at=excluded.fetched_at,
           sha256=excluded.sha256,
           error=excluded.error
         """,
         (url, status, fetched_at, sha256, error),
       )
       conn.commit()
