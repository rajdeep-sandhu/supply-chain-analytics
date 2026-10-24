import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", app_title="Q Status Analytics")

with app.setup:
    import marimo as mo

    from supply_chain_analytics.config import AppConfig


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Q Status Analytics
    """)
    return


if __name__ == "__main__":
    app.run()
