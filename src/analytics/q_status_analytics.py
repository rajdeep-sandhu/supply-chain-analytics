"""Q Status Analytics notebook."""

# pyrefly: ignore-errors[implicit-any-parameter]

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", app_title="Q Status Analytics")

with app.setup:
    import marimo as mo
    import polars as pl
    from duckdb import DuckDBPyConnection

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

        q_stat_trend_schema: pl.Schema = pl.Schema(
            {
                "DATE": pl.Date,
                "SITE": pl.String,
                "A": pl.Int64,
                "A1": pl.Int64,
                "Q": pl.Int64,
                "Q1": pl.Int64,
                "Q2": pl.Int64,
                "Q3": pl.Int64,
                "Q4": pl.Int64,
                "Q5": pl.Int64,
                "Q6": pl.Int64,
            }
        )

        df_dict["q_stat_trend"] = df_dict["q_stat_trend"].cast(
            dtypes=q_stat_trend_schema, strict=True
        )

        return df_dict

    return (load_q_status_tables,)


@app.cell
def _(load_q_status_tables):
    q_status_tables: dict[str, pl.DataFrame] = load_q_status_tables()
    mo.ui.tabs(tabs=q_status_tables, label="Q Status Tables", lazy=True)
    return (q_status_tables,)


@app.cell
def _(q_status_tables: dict[str, pl.DataFrame]):
    q_stat_trend: pl.DataFrame = q_status_tables["q_stat_trend"]
    return (q_stat_trend,)


@app.function
def get_status_columns(df: pl.DataFrame) -> str:
    """Return the q_stat_trend status columns."""
    status_columns: list[str] = [
        column for column in df.columns if column not in ["DATE", "SITE"]
    ]
    status_columns_str: str = ", ".join(f"'{column}'" for column in status_columns)

    return status_columns_str


@app.cell
def _(q_stat_trend: pl.DataFrame):
    status_columns: str = get_status_columns(df=q_stat_trend)
    return (status_columns,)


@app.cell
def _(q_stat_trend: pl.DataFrame, status_columns: str):
    q_stat_trend_long = mo.sql(
        f"""
        FROM q_stat_trend
        UNPIVOT INCLUDE NULLS (
            ITEMS
            FOR Q_STATUS IN ({status_columns})
        );
        """
    )
    return


if __name__ == "__main__":
    app.run()
