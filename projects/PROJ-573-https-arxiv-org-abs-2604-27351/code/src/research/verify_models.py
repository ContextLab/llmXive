"""
verify_models.py

This script verifies that the selected models have weights smaller than 1 GB
and records whether they are tractable on a CPU. The results are written
to ``data/model_verification.json`` and a markdown table is appended to
``research.md`` under a "Model Verification" section.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from huggingface_hub import HfApi

# Configure a simple logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_model_size_mb(hf_id: str) -> Optional[float]:
    """
    Retrieve the total size of a HuggingFace model repository in megabytes.

    Parameters
    ----------
    hf_id: str
        The model identifier on HuggingFace Hub (e.g. ``distilbert-base-uncased``).

    Returns
    -------
    Optional[float]
        Size in megabytes, or ``None`` if the repository cannot be inspected.
    """
    try:
        api = HfApi()
        # ``model_info`` returns an object with a ``siblings`` attribute containing
        # a list of files with their ``size`` in bytes.
        info = api.model_info(repo_id=hf_id)
        total_bytes = sum(sibling.size for sibling in info.siblings if sibling.size)
        size_mb = total_bytes / (1024 * 1024)
        logger.info("Model %s size: %.2f MB", hf_id, size_mb)
        return size_mb
    except Exception as exc:  # pragma: no cover – network failures are rare in tests
        logger.error("Failed to fetch size for %s: %s", hf_id, exc)
        return None

def is_cpu_tractable(size_mb: Optional[float]) -> bool:
    """
    Determine CPU tractability based on size.

    The benchmark assumes any model < 1 GB (1024 MB) can be loaded on a CPU.
    """
    if size_mb is None:
        return False
    return size_mb < 1024.0

def _write_json_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the verification results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info("Wrote model verification JSON to %s", output_path)

def update_research_md(results: List[Dict[str, Any]], md_path: Path) -> None:
    """
    Append a markdown table with the verification results to ``research.md``.
    If the file does not exist, it is created.

    Parameters
    ----------
    results: List[Dict[str, Any]]
        List of dictionaries containing ``model_name``, ``hf_id``, ``size_mb``,
        and ``cpu_tractable``.
    md_path: Path
        Path to ``research.md``.
    """
    header = "\n## Model Verification\n\n"
    table_header = "| model_name | hf_id | size_mb | cpu_tractable |\n"
    table_divider = "|---|---|---|---|\n"
    rows = [
        f"| {r['model_name']} | {r['hf_id']} | {r['size_mb']:.2f} | {r['cpu_tractable']} |\n"
        for r in results
    ]

    content = header + table_header + table_divider + "".join(rows)

    md_path.parent.mkdir(parents=True, exist_ok=True)
    with md_path.open("a", encoding="utf-8") as f:
        f.write(content)

    logger.info("Appended model verification table to %s", md_path)

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main() -> None:
    """
    Verify a curated list of models and persist the results.
    """
    # List of models to verify: (human‑readable name, HuggingFace repo id)
    models_to_check = [
        ("TimeSeries‑Transformer", "ydataai/time-series-transformer"),
        ("TabPFN", "TabPFN/tabpfn"),
        ("Distilled‑LLM (DistilBERT)", "distilbert-base-uncased"),
    ]

    results: List[Dict[str, Any]] = []
    for model_name, hf_id in models_to_check:
        size_mb = get_model_size_mb(hf_id)
        cpu_ok = is_cpu_tractable(size_mb)
        results.append(
            {
                "model_name": model_name,
                "hf_id": hf_id,
                "size_mb": size_mb if size_mb is not None else float("nan"),
                "cpu_tractable": cpu_ok,
            }
        )

    # Write JSON report
    json_path = Path("data") / "model_verification.json"
    _write_json_report(results, json_path)

    # Update research.md
    md_path = Path("research.md")
    update_research_md(results, md_path)

if __name__ == "__main__":
    main()
