 """Hashing utilities."""
 from __future__ import annotations

 import hashlib
 from typing import Union


 def sha256_hex(data: Union[str, bytes]) -> str:
   """Return SHA-256 hex digest of string or bytes."""
   if isinstance(data, str):
     data = data.encode("utf-8")
   return hashlib.sha256(data).hexdigest()
