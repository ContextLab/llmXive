"""
run_e2e.py
------------
End‑to‑end driver that (1) runs the ingestion pipeline, (2) computes the
proxy‑measured agreement, and (3) writes a summary JSON file.
The driver uses the ``phase_timer`` context manager to record runtimes for
each phase and appends them to ``runtime_summary.csv``.
"""
import json
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger
from code.src.timing import phase_timer
from code.ingest.ingest import run_ingest
from code.src.proxy_agreement import compute_proxy_agreement, write_proxy_agreement

log = get_logger(__name__)

def _write_e2e_summary(
    total_rows: int,
    proxy_rows: int,
    agreement: pd.DataFrame,
    summary_path: Path,
) -> None:
    """
    Write a JSON summary containing:
    - total_rows
    - proxy_rows
    - percent_proxy_rows
    - pearson_r
    - r_squared
    """
    percent_proxy = round((proxy_rows / total_rows) * 100, 2) if total_rows else 0.0
    summary = {
        "total_rows": total_rows,
        "proxy_rows": proxy_rows,
        "percent_proxy_rows": percent_proxy,
        "pearson_r": float(agreement["pearson_r"].iloc[0]),
        "r_squared": float(agreement["r_squared"].iloc[0]),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    log.info("E2E summary written to %s", summary_path)

def main() -> None:
    """
    Execute the full pipeline:
    1. Ingestion (writes unified_fatigue.csv)
    2. Proxy‑measured agreement (writes proxy_agreement.csv)
    3. Summary JSON (writes e2e_summary.json)
    Each step is timed via ``phase_timer``.
    """
    # Phase 1 – Ingestion
    with phase_timer("ingest"):
        unified_path = paths.processed("unified_fatigue.csv")
        run_ingest(output_path=unified_path)

    # Load the unified dataset once for the remaining phases
    df = pd.read_csv(unified_path)

    # Phase 2 – Proxy agreement
    with phase_timer("proxy_agreement"):
        agreement_df = compute_proxy_agreement(df)
        write_proxy_agreement(agreement_df)

    # Phase 3 – Summary JSON
    with phase_timer("e2e_summary"):
        total_rows = len(df)
        proxy_rows = int(df["is_proxy"].sum())
        summary_path = paths.results("e2e_summary.json")
        _write_e2e_summary(
            total_rows=total_rows,
            proxy_rows=proxy_rows,
            agreement=agreement_df,
            summary_path=summary_path,
        )

    log.info("End‑to‑end pipeline completed successfully.")

if __name__ == "__main__":
    main()
