"""Factory to return a DuckDBPyConnection."""

import logging
from pathlib import Path

import duckdb

# Get a logger
logger: logging.Logger = logging.getLogger(__name__)


class DuckDBFactory:
    """DuckDB Factory to create a DuckDBPyConnection."""

    def __init__(self, database: Path | str = ":memory:") -> None:
        """DuckDBFactory constructor.

        Args:
            database (Path | str): DuckDB database filename. Defaults to ":memory:".
        """
        self._database: Path | str = database

    def create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create and return a DuckDBPyonnection."""
        conn: duckdb.DuckDBPyConnection = duckdb.connect(self._database)
        logger.info("Created DuckDB connection %s", conn)

        return conn
