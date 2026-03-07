 from __future__ import annotations

 from datetime import datetime, timezone


 def utc_now() -> datetime:
   """Return an aware UTC datetime."""
   return datetime.now(timezone.utc)


 def iso_now() -> str:
   """Return ISO formatted UTC timestamp."""
   return utc_now().isoformat()
