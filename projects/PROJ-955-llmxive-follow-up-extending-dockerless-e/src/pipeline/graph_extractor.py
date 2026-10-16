"""
src/pipeline/graph_extractor.py
------------------------------

Static graph extraction module for the static‑dynamic gap analysis pipeline.

This implementation generates placeholder Control‑Flow Graph (CFG) and Call
Graph (CG) JSON files for every patch listed in ``data/patches.csv`` (or
``data/patches_sample.csv`` when a sampled ingestion mode was used).  The
graphs are deliberately simple but conform to the JSON schema defined in
``specs/001-llmxive-follow-up-extending-dockerless-e/contracts/static_graph.schema.yaml``.
Real‑world analysis tools such as ``pycg`` (for Python) or ``clang‑query``
(for C++) can be swapped in later without changing the surrounding
pipeline logic.

The module can be executed directly:

    python -m src.pipeline.graph_extractor

which will write the JSON files under ``interim/graphs/`` and produce a
summary report ``reports/graph_extraction.yaml``.
"""

import json
import pathlib
from collections import defaultdict

from tqdm import tqdm
import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper to create a minimal yet schema‑valid graph structure
# ----------------------------------------------------------------------
def _make_placeholder_graph(patch_id: str, graph_type: str) -> dict:
    """
    Return a minimal graph dictionary that satisfies the static graph schema.

    Parameters
    ----------
    patch_id: str
        Identifier of the patch.
    graph_type: str
        Either ``"cfg"`` or ``"cg"``.

    Returns
    -------
    dict
        Graph representation ready for JSON serialisation.
    """
    # A single entry node; external attribute set to False.
    node = {
        "id": "n0",
        "label": "entry",
        "attributes": {"external": False},
    }
    return {
        "patch_id": patch_id,
        "graph_type": graph_type,
        "nodes": [node],
        "edges": [],  # No edges in the placeholder graph
    }

# ----------------------------------------------------------------------
# Core extraction logic
# ----------------------------------------------------------------------
def extract_graphs() -> None:
    """
    Generate CFG and CG JSON files for every patch.

    The function reads the patch list from ``data/patches.csv`` if it exists;
    otherwise it falls back to ``data/patches_sample.csv`` (used when the
    ingestion step operated in sampling mode).  For each patch a pair of
    JSON files ``{patch_id}_cfg.json`` and ``{patch_id}_cg.json`` is written
    to ``interim/graphs/``.  A YAML summary report is written to
    ``reports/graph_extraction.yaml``.
    """
    # Determine which CSV file to use
    patches_csv = paths.data("patches.csv")
    if not patches_csv.is_file():
        patches_csv = paths.data("patches_sample.csv")
    if not patches_csv.is_file():
        raise RuntimeError(
            "Neither patches.csv nor patches_sample.csv found in the data directory."
        )

    # Load patch identifiers
    import pandas as pd

    df = pd.read_csv(patches_csv, usecols=["patch_id", "language"])
    total_patches = len(df)
    log.info("Starting graph extraction for %d patches", total_patches)

    # Ensure output directory exists
    graphs_dir = paths.interim("graphs")
    graphs_dir.mkdir(parents=True, exist_ok=True)

    parsed_success = 0
    skipped_unparseable = 0
    # In this placeholder implementation we treat every patch as parseable.
    for _, row in tqdm(df.iterrows(), total=total_patches, desc="Extracting graphs"):
        patch_id = str(row["patch_id"])
        # Generate placeholder CFG and CG
        cfg = _make_placeholder_graph(patch_id, "cfg")
        cg = _make_placeholder_graph(patch_id, "cg")

        cfg_path = graphs_dir / f"{patch_id}_cfg.json"
        cg_path = graphs_dir / f"{patch_id}_cg.json"

        try:
            cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            cg_path.write_text(json.dumps(cg, indent=2), encoding="utf-8")
            parsed_success += 1
        except Exception as exc:
            log.error("Failed to write graph files for %s: %s", patch_id, exc)
            skipped_unparseable += 1

    # Write summary report
    report = {
        "total_patches": total_patches,
        "parsed_success": parsed_success,
        "skipped_unparseable": skipped_unparseable,
    }
    report_path = paths.reports("graph_extraction.yaml")
    report_path.write_text(yaml.safe_dump(report), encoding="utf-8")
    log.info(
        "Graph extraction completed: %d success, %d skipped",
        parsed_success,
        skipped_unparseable,
    )

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    extract_graphs()
