"""
Script: 02_prepare_human_coding_dir.py
--------------------------------------
Creates the human‑coding directory and a CSV template for annotators.

The script performs the following steps:

1. Ensures the directory ``data/raw/human_coding/`` exists.
2. Loads ``data/processed/candidates_filtered.csv`` (produced by T001) and extracts the
   ``scenario_id`` column.
3. Writes a README (``README.md``) that explains the annotation procedure and the
   required number of raters.
4. Generates ``annotations_template.csv`` with one row per scenario and three empty
   columns for independent annotators to record a 1‑5 ambiguity rating.

The script is deliberately argument‑free – it is invoked directly from the quick‑start
run‑book:

    python code/02_prepare_human_coding_dir.py

The output files are written inside the project tree using the
``llmxive_toolkit.paths`` helpers, guaranteeing that the required folders are created.
"""

import pandas as pd
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _ensure_output_dir() -> Path:
    """
    Ensure that the human‑coding directory exists and return its Path.
    """
    human_coding_dir = paths.data("raw", "human_coding")
    human_coding_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Created/ensured human‑coding directory at {human_coding_dir}")
    return human_coding_dir

def _write_readme(target_dir: Path) -> None:
    """
    Write a short README describing the annotation procedure.
    """
    readme_path = target_dir / "README.md"
    content = (
        "# Human Coding Annotation Procedure\\n\\n"
        "This folder contains the template CSV that annotators should fill out.\\n"
        "For each ``scenario_id`` you must provide an **ambiguity rating** on a 1‑5 Likert scale,\\n"
        "where 1 = *Not ambiguous* and 5 = *Highly ambiguous*.\\n\\n"
        "Three independent annotators are required for each scenario.\\n"
        "Please do not modify the ``scenario_id`` column.\\n"
        "When all three columns are completed, save the file as ``annotations_filled.csv``\\n"
        "and place it back into this directory for downstream processing (T003).\\n"
    )
    readme_path.write_text(content, encoding="utf-8")
    log.info(f"Wrote README to {readme_path}")

def _load_scenario_ids(candidates_csv: Path) -> list:
    """
    Load the ``scenario_id`` column from the candidates CSV.
    """
    if not candidates_csv.is_file():
        raise FileNotFoundError(f"Candidates file not found: {candidates_csv}")

    df = pd.read_csv(candidates_csv, dtype=str)
    if "scenario_id" not in df.columns:
        raise ValueError("The candidates CSV must contain a 'scenario_id' column.")
    scenario_ids = df["scenario_id"].tolist()
    log.info(f"Loaded {len(scenario_ids)} scenario IDs from {candidates_csv}")
    return scenario_ids

def _write_template_csv(scenario_ids: list, output_path: Path) -> None:
    """
    Write the annotation template CSV.
    Columns: scenario_id, annotator_1, annotator_2, annotator_3
    """
    header = ["scenario_id", "annotator_1", "annotator_2", "annotator_3"]
    rows = [[sid, "", "", ""] for sid in scenario_ids]

    df = pd.DataFrame(rows, columns=header)
    df.to_csv(output_path, index=False, encoding="utf-8")
    log.info(f"Wrote annotation template with {len(rows)} rows to {output_path}")

def main() -> None:
    # 1. Ensure output directory exists
    human_coding_dir = _ensure_output_dir()

    # 2. Write README
    _write_readme(human_coding_dir)

    # 3. Load scenario IDs from the candidates file produced by T001
    candidates_csv = paths.processed("candidates_filtered.csv")
    scenario_ids = _load_scenario_ids(candidates_csv)

    # 4. Write the template CSV
    template_csv_path = human_coding_dir / "annotations_template.csv"
    _write_template_csv(scenario_ids, template_csv_path)

    log.info("Human‑coding preparation complete.")

if __name__ == "__main__":
    main()
