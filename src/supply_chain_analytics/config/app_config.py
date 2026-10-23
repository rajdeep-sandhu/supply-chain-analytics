"""App config data."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

# Get a logger
logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    """App config data."""

    project_root_dir: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[3]
    )
