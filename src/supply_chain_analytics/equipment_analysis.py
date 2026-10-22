import marimo

__generated_with = "0.24.0"
app = marimo.App(width="full", app_title="Equipment Analysis")

with app.setup:
    from datetime import date

    import duckdb
    import polars as pl

    from inventory_analysis.equipment import dataprep


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Equipment Transaction Analysis
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load Equipment Transactions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Use Polars to read the data due to better `.xlsx` support than DuckDB.
    """)
    return


@app.cell
def _():
    (trans_file_element := dataprep.file_element())
    return (trans_file_element,)


@app.cell
def _(trans_file_element):
    ux_trans: pl.DataFrame | None = None
    ux_trans_filename: str | None = None

    ux_trans_filename, ux_trans = dataprep.file_element_to_df(
        trans_file_element
    )
    return (ux_trans,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data Quality and Pre-processing
    """)
    return


@app.cell
def _(ux_trans: pl.DataFrame | None):
    # Highlight if input file column structure has changed
    dataprep.has_expected_columns(ux_trans)
    return


@app.cell
def _(ux_trans: pl.DataFrame | None):
    dataprep.describe_raw_data(ux_trans)
    return


@app.cell
def _(ux_trans: pl.DataFrame | None):
    if ux_trans is not None:
        conn = duckdb.connect()
        conn.register("ux_trans", ux_trans)
    return


@app.cell
def _(mo, ux_trans: pl.DataFrame | None):
    if ux_trans is not None:
        today: date = date.today()
        min_trans_date: date = ux_trans["date_extracted"].min()
        max_trans_date: date = ux_trans["date_extracted"].max()
        sites: pl.Series = ux_trans["Site Code"].unique().sort()
        skus: pl.Series = ux_trans["Product Code"].unique().sort()

        # The dataset should not have dates beyond the current date.
        # Raise an exception if it does.
        if max_trans_date > today:
            raise ValueError(
                f"Dataset contains future transactions: "
                f"max={max_trans_date:%Y-%m-%d}, today={today:%Y-%m-%d}"
            )

        start_date_picker = mo.ui.date.from_series(
            ux_trans["date_extracted"],
            value=min_trans_date,
            label="Start Date",
        )

        end_date_picker = mo.ui.date.from_series(
            ux_trans["date_extracted"], value=max_trans_date, label="End Date"
        )

        site_picker = mo.ui.multiselect(
            options=sites, label="Site Code", value=None
        )

        sku_picker = mo.ui.multiselect(
            options=skus, label="Product Code", value=None
        )
    return end_date_picker, sku_picker, start_date_picker


@app.cell
def _(end_date_picker, mo, start_date_picker):
    mo.hstack(
        [
            start_date_picker,
            end_date_picker,
        ],
        justify="start",
    )
    return


@app.cell
def _(end_date_picker, mo, ux_trans: pl.DataFrame | None):
    _df = mo.sql(
        f"""
        -- Get total stock by site and SKU on a specific date
        SELECT
            "Site Code",
            "Product Code",
            SUM(Quantity)
        FROM
            ux_trans
        WHERE
            date_extracted <= '{end_date_picker.value.isoformat()}'
        GROUP BY
            "Site Code",
            "Product Code"
        ORDER BY
            "Site Code" ASC,
            "Product Code" ASC
        """
    )
    return


@app.cell
def _(end_date_picker, mo):
    _df = mo.sql(
        f"""
        -- Pivot Quantity by SKU and Site
        WITH
            ux_trans_dated AS
            (
            SELECT
            	"Site Code",
            	"Product Code",
            	"Quantity",
            	date_extracted
            FROM
            	ux_trans
            WHERE
        		date_extracted <= '{end_date_picker.value.isoformat()}'
            )

        PIVOT ux_trans_dated
        ON "Site Code"
        USING COALESCE(SUM(Quantity), 0)
        GROUP BY "Product Code"
        ORDER BY "Product Code"
        """
    )
    return


@app.cell
def _(sku_picker):
    sku_picker
    return


@app.cell
def _(ux_trans: pl.DataFrame | None):
    # Define running balance by sku and site
    ux_balances = ux_trans.with_columns(
        pl.col("Quantity")
        .cum_sum()
        .over(["Product Code", "Site Code"])
        .alias("running_balance")
    )

    ux_balances
    return


@app.cell
def _(end_date_picker, ux_trans: pl.DataFrame | None):
    # Daily delta by site and SKU.
    delta_daily = (
        ux_trans.filter(pl.col("date_extracted") <= end_date_picker.value)
        .group_by(["date_extracted", "Site Code", "Product Code"])
        .agg(pl.col("Quantity").sum().alias("qty"))
        .sort(by=["date_extracted", "Site Code", "Product Code"])
    )

    delta_daily
    return


@app.cell
def _(end_date_picker, ux_trans: pl.DataFrame | None):
    # Pivot Quantity by site and SKU on a specific date using polars.
    # This reveals equipment receipted or transferred without a site being selected.
    # Figure out if this can be revealed in the SQL version too.
    (
        ux_trans.filter(pl.col("date_extracted") <= end_date_picker.value)
        .pivot(
            index="Product Code",
            on="Site Code",
            values="Quantity",
            aggregate_function="sum",
            sort_columns=True,
        )
        .sort(by="Product Code")
    )
    return


if __name__ == "__main__":
    app.run()
