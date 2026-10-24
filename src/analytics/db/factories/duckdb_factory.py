"""Factory to return a DuckDBPyConnection."""

import logging

# Get a logger
logger: logging.Logger = logging.getLogger(__name__)


class DuckDBFactory:
    """DuckDB Factory to create a DuckDBPyConnection."""

    def __init__(self, database: str = ":memory:") -> None:
        """DuckDBFactory constructor.

        Args:
            database (str): DuckDB database filename. Defaults to ":memory:".
        """
        self._database: str = database
