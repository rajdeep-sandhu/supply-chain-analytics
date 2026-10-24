"""Q Status Analytics notebook."""

# pyrefly: ignore-errors[implicit-any-parameter]
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", app_title="Q Status Analytics")

with app.setup:
    import marimo as mo
    import polars as pl

    from analytics.config import AppConfig


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Q Status Analytics
    """)
    return


@app.cell
def _():
    # App setup
    config = AppConfig()
    return (config,)


@app.cell
def _(config):
    def load_q_status_tables() -> dict[str, pl.DataFrame]:
        """Load Q Status tables from the 6AM Snapshot Dasboard workbook."""
        q_status_worksheets: list[str] = [
            "consol_stock_6AM",
            "q_stat_trend",
            "tblLocations",
        ]

        df_dict = pl.read_excel(
            source=config.dashboard_6am_snapshot_workbook,
            sheet_name=q_status_worksheets,
        )

        return df_dict

    return (load_q_status_tables,)


@app.cell
def _(load_q_status_tables):
    q_status_tables: dict[str, pl.DataFrame] = load_q_status_tables()
    mo.ui.tabs(tabs=q_status_tables, label="Q Status Tables", lazy=True)
    return


if __name__ == "__main__":
    app.run()
