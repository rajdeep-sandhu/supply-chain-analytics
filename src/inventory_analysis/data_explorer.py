# /// script
# dependencies = [
#     "altair==6.2.2",
#     "dash==4.4.1",
#     "duckdb==2.0.0",
#     "fastexcel==0.21.0",
#     "marimo",
#     "pandas==3.0.5",
#     "plotly[express]==7.0.0",
#     "polars==1.43.2",
#     "pyarrow==26.0.0",
#     "sqlglot==30.24.0",
# ]
# requires-python = ">=3.14"
# ///

import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", app_title="Data Explorer")

with app.setup:
    from io import BytesIO

    import polars as pl
    import duckdb
    import pyarrow
    import datetime as dt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Data Explorer
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This contains initial data exploration of 3PE and job data, to inform further app design.
    """)
    return


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    NOTEBOOK_LOCATION = mo.notebook_location()
    return


@app.cell
def _(mo):
    def get_ui_file_element():
        """Return a file element for Equipment Transaction Data"""
        element = mo.ui.file(
            label="Upload Data File",
            filetypes=[".xlsx"],
            multiple=False,
        )

        return element

    return (get_ui_file_element,)


@app.function
def ui_file_element_to_stream(ui_file_element) -> dict:
    """
    Returns the filename and a BytesIO stream from a mo.ui.file element.

    params:
    ui_file_element: mo.ui.file element.
    """

    # Get first result for single file upload
    result = ui_file_element.value[0]
    filename: str = result.name
    content: bytes = result.contents
    file_stream = BytesIO(content)

    return {"filename": filename, "file_stream": file_stream}


@app.cell
def _(mo):
    def ui_file_element_to_df(
        ui_file_element,
    ) -> tuple[str | None, dict[str, pl.DataFrame] | None]:
        """
        Return filename and dict of DataFrames from mo.ui.file element
        """
        upload_result: dict | None = None
        filename: str | None = None
        df_dict: dict[str, pl.DataFrame] | None = None

        if ui_file_element.value:
            upload_result = ui_file_element_to_stream(ui_file_element)
            filename = upload_result["filename"]
            file_stream = upload_result["file_stream"]
            df_dict = pl.read_excel(source=file_stream, sheet_id=0)

        message: str = (
            f"File: `{filename}` uploaded."
            if filename
            else "No file uploaded."
        )
        mo.output.replace(mo.md(message))

        return filename, df_dict

    return (ui_file_element_to_df,)


@app.cell
def _(get_ui_file_element):
    (ui_file_element := get_ui_file_element())
    return (ui_file_element,)


@app.cell
def _(ui_file_element):
    ui_file_element.value
    return


@app.cell
def _(mo, ui_file_element, ui_file_element_to_df):
    with mo.persistent_cache("uploaded_file"):
        data_filename, df_dict = ui_file_element_to_df(ui_file_element)
        df_selector = mo.ui.dropdown(df_dict) if df_dict else None
    return data_filename, df_dict, df_selector


@app.cell
def _(data_filename, df_selector, mo):
    if df_selector is not None:
        mo.output.replace(mo.vstack([data_filename, df_selector]))
    else:
        mo.output.replace(mo.callout("No file uploaded.", kind="warn"))
    return


@app.cell
def _(df_selector):
    df = None
    if df_selector is not None:
        df = df_selector.value

    df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3PE Scratchpad
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    - Sample code for 3PE transactions. Assumes that the 3PE tansactions file has been uploaded.
    """)
    return


@app.cell
def _(df_dict):
    ux_trans: pl.DataFrame = df_dict["3PE Transactions"]
    ux_trans = ux_trans.sort(by="ID")
    ux_trans
    return (ux_trans,)


@app.cell
def _(ux_trans: pl.DataFrame):
    conn = duckdb.connect()
    conn.register("ux_trans", ux_trans)
    return (conn,)


@app.cell
def _(date, mo, ux_trans: pl.DataFrame):
    today: date = dt.date.today()
    min_trans_date: dt.date = ux_trans["date_extracted"].min()
    max_trans_date: dt.date = ux_trans["date_extracted"].max()
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
        ux_trans["date_extracted"], value=min_trans_date, label="Start Date"
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
    mo.hstack([start_date_picker, end_date_picker])
    return


@app.cell
def _(end_date_picker):
    end_date_picker.value.isoformat()
    return


@app.cell
def _(conn, end_date_picker, mo, ux_trans: pl.DataFrame):
    _df = mo.sql(
        f"""
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
        """,
        engine=conn
    )
    return


@app.cell
def _(conn, mo):
    _df = mo.sql(
        f"""
        PIVOT ux_trans
        ON "Site Code"
        USING SUM(Quantity)
        GROUP BY "Product Code"
        ORDER BY "Product Code"
        """,
        engine=conn
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    - `PIVOT` might not be the besst way. It hard codes sites, fails if a site has no data and does not account for newly added sites, like BF101.
    - Analyses will need to avoid hard coding categories, and possibly still display categories missing from a subset of the data if they are present in the data superset, e.g. BF108 displaying 0 quantities.
    """)
    return


@app.cell
def _(conn, mo):
    _df = mo.sql(
        f"""
        WITH
            ux_pivot AS
            (
            PIVOT ux_trans
            ON "Site Code"
            USING SUM(Quantity)
            GROUP BY "Product Code"
            ORDER BY "Product Code"
            ),

            prod_totals AS
            (
            SELECT
                "Product Code",
                Sum(Quantity) AS TOT_QTY
            FROM
                ux_trans
            GROUP BY "Product Code"
            )

        SELECT
            ux_pivot."Product Code",
            ux_pivot.BF101,
            ux_pivot.BF102,
            ux_pivot.BF103,
            ux_pivot.BF104,
            ux_pivot.BF105,
            ux_pivot.BF106,
            ux_pivot.BF107,
            ux_pivot.BF108,
            ux_pivot.BF109,
            ux_pivot.BF110
        FROM
            ux_pivot
            LEFT JOIN
            prod_totals
                ON ux_pivot."Product Code" = prod_totals."Product Code"
        """,
        engine=conn
    )
    return


@app.cell
def _(mo, sku_picker):
    mo.vstack([sku_picker, mo.md(", ".join(sku_picker.value))])
    return


@app.cell
def _(sku_picker, ux_trans: pl.DataFrame):
    ux_trans.filter(ux_trans["Product Code"].is_in(sku_picker.value))
    return


@app.cell
def _(ux_trans: pl.DataFrame):
    ux_balances = ux_trans.with_columns(
        pl.col("Quantity")
        .cum_sum()
        .over(["Product Code", "Site Code"])
        .alias("running_balance")
    )
    ux_balances
    return


@app.cell
def _(end_date_picker):
    end_date_picker
    return


@app.cell
def _(ux_trans: pl.DataFrame):
    ux_trans.filter(pl.col("Product Code") == "UX000014").sort(
        by=["date_extracted", "ID"]
    ).group_by_dynamic('date_extracted', every='1w').agg(pl.sum('Quantity'))
    return


@app.cell
def _(end_date_picker, ux_trans: pl.DataFrame):
    delta = (
        ux_trans.filter(pl.col("date_extracted") <= end_date_picker.value)
        .group_by(["date_extracted", "Site Code", "Product Code"])
        .agg(pl.col("Quantity").sum().alias("qty"))
        .sort(by=["date_extracted", "Site Code", "Product Code"])
    )
    delta
    return


@app.cell
def _(snapshot):
    snapshot.pivot(
        index="Product Code",
        on="Site Code",
        values="qty",
        aggregate_function="sum",
        sort_columns=True,
    ).sort(by="Product Code")
    return


@app.cell
def _(ux_trans: pl.DataFrame):
    ux_trans.filter(
        pl.col("date_ingested")
        .str.to_datetime(format="%Y-%m-%d %H:%M:%S", strict=False)
        .is_null()
    )
    return


@app.cell
def _(ux_trans: pl.DataFrame):
    ux_trans.with_columns(
        pl.col("Trans Date")
        .str.to_date(format="%Y-%m-%dT%H:%M:%S%.3fZ").alias("trans_date_extracted"))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Timeline Scratchpad
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This is sample code for developing a timeline.
    """)
    return


@app.cell
def _():
    from dash import Dash, dcc, html

    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd

    return go, px


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Task Sample DataFrame
    """)
    return


@app.cell
def _():
    tasks = pl.DataFrame(
        [
            {
                "Task": "Job A",
                "Start": "2009-01-01",
                "Finish": "2009-02-28",
                "Resource": "Alex",
                "Completion_pct": 0,
            },
            {
                "Task": "Job B",
                "Start": "2009-03-05",
                "Finish": "2009-04-15",
                "Resource": "Alex",
                "Completion_pct": 25,
            },
            {
                "Task": "Job C",
                "Start": "2009-02-20",
                "Finish": "2009-05-30",
                "Resource": "Max",
                "Completion_pct": 75,
            },
        ]
    )

    tasks
    return (tasks,)


@app.cell
def _(go, px, tasks):
    customdata = tasks["Task", "Start", "Finish", "Completion_pct"]

    fig = px.timeline(
        data_frame=tasks,
        x_start="Start",
        x_end="Finish",
        y="Resource",
        color="Task",
        text="Completion_pct",
        title="Tasks",
        opacity=0.5,
        # custom_data=["Task", "Start", "Finish", "Completion_pct"],
    )

    fig.update_yaxes(autorange="reversed")
    # fig.update_traces(width=0.3)
    fig.update_traces(
        customdata=customdata,
        texttemplate="%{customdata[3]}%",
        textposition="inside",
        insidetextanchor="end",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Resource: %{y}<br>"
            "Start: %{customdata[1]}<br>"
            "Finish: %{customdata[2]}<br>"
            "Complete: %{customdata[3]}%"
            "<extra></extra>"
        ),
    )

    fig.update_layout(title={"text": "Tasks", "font_size": 30, "x": 0.5, "xanchor": "right"})

    # Add completion % bars
    task_colours = {trace.name: trace.marker.color for trace in fig.data}

    for row in tasks.iter_rows(named=True):
        start = pl.Series([row["Start"]]).str.to_datetime().item()
        finish = pl.Series([row["Finish"]]).str.to_datetime().item()

        duration_ms = (finish - start).total_seconds() * 1000
        completed_ms = duration_ms * row["Completion_pct"] / 100

        print(f"{start}, {finish}, {duration_ms}, {completed_ms}")

        fig.add_trace(
            go.Bar(
                x=[completed_ms],
                base=[start],
                y=[row["Resource"]],
                orientation="h",
                # width=0.3,
                # marker={"color": "black", "opacity": 0.5},
                marker={
                    "color": task_colours[row["Task"]],
                    "opacity": 0.8,
                    # "pattern": {"shape": "\\", "solidity": 0.3},
                },
                hovertemplate=(
                    f"{row['Task']}<br>"
                    f"Completed: {row['Completion_pct']}%"
                    "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    fig.show()
    return (fig,)


@app.cell
def _(fig):
    fig["layout"]
    return


@app.cell
def _():
    # completion = tasks.with_columns(
    #     (
    #         pl.col("Start").str.to_datetime()
    #         + (
    #             pl.col("Finish").str.to_datetime()
    #             - pl.col("Start").str.to_datetime()
    #         ) * pl.col("Completion_pct") / 100
    #     ).alias("Completion")
    # )

    # fig = px.timeline(
    #     tasks,
    #     x_start="Start",
    #     x_end="Finish",
    #     y="Resource",
    #     color="Task",
    #     text="Completion_pct",
    #     opacity=0.5
    # )

    # fig2 = px.timeline(
    #     completion,
    #     x_start="Start",
    #     x_end="Completion",
    #     y="Resource",
    #     color="Task",
    # )

    # for trace in fig2.data:
    #     trace.width = 0.35
    #     trace.showlegend = False
    #     trace.marker.opacity = 0.5
    #     fig.add_trace(trace)

    # fig.update_yaxes(autorange="reversed")

    # fig.show()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Job DataFrame
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    - Sample code for timeline. Assumes that an External Data `Job` dataframe is uploaded.
    - Datetime handling in the original dataframe columns is an issue and is covered in the Planner project.
    """)
    return


@app.cell
def _(df_dict):
    job = df_dict["Job"]
    job = job.with_columns(
        pl.coalesce("force_start", "start_time").alias("plot_start")
    )
    job
    return (job,)


@app.cell
def _():
    return


@app.cell
def _(job, px):
    job_timeline = px.timeline(
        data_frame=job,
        x_start="start_time",
        x_end="finish_time",
        y="line",
        # color="Task",
        # text="Completion_pct",
        # title="Tasks",
        opacity=0.5,
        # custom_data=["Task", "Start", "Finish", "Completion_pct"],
    )

    job_timeline.show()
    return (job_timeline,)


@app.cell
def _(job):
    print(job["line"].unique().to_list())
    return


@app.cell
def _(job_timeline):
    print(job_timeline.data[0].y)
    print(job_timeline.data[0].base[:10])
    print(job_timeline.data[0].x[:10])
    return


@app.cell
def _(job_timeline):
    print(job_timeline.layout.yaxis)
    print(job_timeline.data[0].y[:20])
    return


if __name__ == "__main__":
    app.run()
