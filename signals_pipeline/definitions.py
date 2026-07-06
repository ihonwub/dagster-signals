"""Signals code location -- a tiny demo pipeline for the platform bring-up.

WHAT THIS FILE IS
-----------------
This module exposes a single `Definitions` object (the variable `defs` below).
The Dagster gRPC code server loads it when started with:

    dagster api grpc --python-module signals_pipeline.definitions --port 4001

That command is what the Helm chart runs inside the code-location pod (see
`dagsterApiGrpcArgs` in apps/dagster-code-locations/applicationset.yaml). The
control plane (webserver + daemon) then talks to this server over gRPC -- it
never imports this code directly.

THE ASSET GRAPH
---------------
Three assets form a simple chain so you can SEE lineage in the UI:

    raw_signals  ->  cleaned_signals  ->  signals_report

They use only in-memory Python data (no S3, no database), so a run completes
end-to-end inside the run pod with no external dependencies. Swap these for real
assets later -- the deployment wiring stays identical.
"""

from dagster import asset, Definitions, MaterializeResult, MetadataValue


@asset
def raw_signals() -> list[dict]:
    """Pretend we pulled raw rows from an upstream source."""
    return [
        {"id": 1, "value": 10, "status": "ok"},
        {"id": 2, "value": -3, "status": "ok"},
        {"id": 3, "value": 7, "status": "bad"},
        {"id": 4, "value": 5, "status": "ok"},
    ]


@asset
def cleaned_signals(raw_signals: list[dict]) -> list[dict]:
    """Drop bad rows and negative values -- a basic cleaning step.

    Note the function PARAMETER `raw_signals` matches the asset above: that is
    how Dagster wires the dependency (and draws the arrow in the UI).
    """
    return [
        row
        for row in raw_signals
        if row["status"] == "ok" and row["value"] >= 0
    ]


@asset
def signals_report(cleaned_signals: list[dict]) -> MaterializeResult:
    """Summarise the cleaned signals; attach metadata visible in the UI."""
    count = len(cleaned_signals)
    total = sum(row["value"] for row in cleaned_signals)
    avg = total / count if count else 0.0
    return MaterializeResult(
        metadata={
            "num_rows": MetadataValue.int(count),
            "total_value": MetadataValue.int(total),
            "avg_value": MetadataValue.float(avg),
        }
    )


# The single object the gRPC server looks for in this module.
defs = Definitions(
    assets=[raw_signals, cleaned_signals, signals_report],
)
