"""Factory to return a DuckDBPyConnection."""

import logging

# Get a logger
logger: logging.Logger = logging.getLogger(__name__)


class DuckDBFactory:
    """DuckDB Factory to create a DuckDBPyConnection."""
