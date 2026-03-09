 from __future__ import annotations

 from datetime import datetime, timezone

   """Return an aware UTC datetime."""
 def utc_now() -> datetime:
   return datetime.now(timezone.utc)


 def iso_now() -> str:
   """Return ISO formatted UTC timestamp."""
   return utc_now().isoformat()
