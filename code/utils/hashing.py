 from __future__ import annotations

 import hashlib
 from typing import Union

# Returns SHA-256 hex digest of string or bytes.
 def sha256_hex(data: Union[str, bytes]) -> str:
   if isinstance(data, str):
     data = data.encode("utf-8")
   return hashlib.sha256(data).hexdigest()
