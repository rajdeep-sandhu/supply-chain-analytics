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

    @property
    def dev_data_dir(self) -> Path:
        """Return dev_data dir path from project root."""
        return self.project_root_dir / "src/analytics/dev_data"

    @property
    def snapshot_6am_dashboard_workbook(self) -> Path:
        """Return seed data workbook path for sample data seeding."""
        return self.dev_data_dir / "6AM Snapshot Dashboard.xlsx"
