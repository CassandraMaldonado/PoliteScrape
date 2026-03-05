 from __future__ import annotations

 from dataclasses import dataclass
 from typing import Any, Dict, Mapping, Optional, Tuple, Type

 from bs4 import BeautifulSoup
 from pydantic import BaseModel, create_model


 @dataclass
 class Selector:
   field: str
   selector: str
   attr: Optional[str] = None


 def build_model(name: str, schema_def: Mapping[str, str]) -> Type[BaseModel]:
   type_map = {
     "str": (str, ...),
     "int": (int, ...),
     "float": (float, ...),
     "bool": (bool, ...),
   }
   fields: Dict[str, Tuple[Any, Any]] = {}
   for field, type_str in schema_def.items():
     fields[field] = type_map.get(type_str, (str, ...))
   return create_model(name, **fields)  # type: ignore[arg-type]


 def parse_selectors(raw: Mapping[str, Any]) -> Dict[str, Selector]:
   selectors: Dict[str, Selector] = {}
   for field, spec in raw.items():
     if isinstance(spec, str):
       selectors[field] = Selector(field=field, selector=spec)
     elif isinstance(spec, Mapping):
       selectors[field] = Selector(
         field=field,
         selector=str(spec.get("selector")),
         attr=spec.get("attr"),
       )
     else:
       raise ValueError(f"Unsupported selector config for {field}: {spec}")
   return selectors


 class CSSExtractor:

   def __init__(self, selectors: Dict[str, Selector], model: Type[BaseModel]) -> None:
     self.selectors = selectors
     self.model = model

   def extract(self, html: str) -> BaseModel:
     soup = BeautifulSoup(html, "html.parser")
     data: Dict[str, Any] = {}
     for field, selector in self.selectors.items():
       node = soup.select_one(selector.selector)
       if not node:
         data[field] = None
         continue
       if selector.attr:
         data[field] = node.get(selector.attr)
       else:
         data[field] = node.get_text(strip=True)
     return self.model(**data)
