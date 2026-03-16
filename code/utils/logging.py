 from __future__ import annotations

 import logging
 import sys
 from typing import Any

 import structlog

# Configure structlog with the JSON output.
 def configure_logging(level: str = "INFO") -> None:
   logging.basicConfig(
     level=getattr(logging, level.upper(), logging.INFO),
     format="%(message)s",
     stream=sys.stdout,
   )

   structlog.configure(
     processors=[
       structlog.processors.TimeStamper(fmt="iso"),
       structlog.processors.add_log_level,
       structlog.processors.StackInfoRenderer(),
       structlog.processors.format_exc_info,
       structlog.processors.JSONRenderer(),
     ],
     wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper(), logging.INFO)),
     context_class=dict,
     logger_factory=structlog.PrintLoggerFactory(),
   )

# Returns a structlog logger.
 def get_logger(**kwargs: Any) -> structlog.stdlib.BoundLogger:
   return structlog.get_logger().bind(**kwargs)
