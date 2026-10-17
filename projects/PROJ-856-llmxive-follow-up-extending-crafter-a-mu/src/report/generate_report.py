"""
Generate a human‑readable markdown report summarising the
cognitive‑load comparison study.

The script is intended to be run after the validation and analysis
steps have produced their artefacts:

    python -m src.validation.run_validation \
        --log-dir data/logs/ \
        --ground-truth-dir data/ground_truth/ \
        --output-dir data/validation/

    python -m src.analysis.wilcoxon_analysis \
        --validation-dir data/validation/ \
        --output-dir outputs/

It reads the validation records (``data/validation/semantic_validation.jsonl``)
and any JSON‑line analysis result files written to the ``outputs/`` directory,
computes descriptive statistics, success‑rate tables and embeds the Wilcoxon
test results, then writes ``outputs/report.md``.
The report contains:

  1. Mean and median time‑to‑success and iteration counts per interface.
  2. Wilcoxon signed‑rank statistics, p‑values (Bonferroni‑adjusted),
     effect size *r* and 95 % bootstrap confidence intervals.
  3. Separate success‑rate tables for vector‑match and semantic‑similarity.
  4. A brief “Methods” paragraph referencing the pipeline scripts.

The script uses only the standard library and ``pandas`` (already
available in the environment).  All paths are resolved via the
``llmxive_toolkit.paths`` helpers which automatically create the
required directories.
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict

import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _load_jsonl(file_path: Path) -> List[Dict]:
    """Load a JSON‑lines file and return a list of dictionaries."""
    records = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def _load_validation_records(validation_dir: Path) -> pd.DataFrame:
    """Load semantic validation records into a DataFrame."""
    validation_file = validation_dir / "semantic_validation.jsonl"
    if not validation_file.exists():
        raise FileNotFoundError(f"Validation file not found: {validation_file}")

    records = _load_jsonl(validation_file)
    df = pd.DataFrame(records)
    # Ensure required columns exist
    required = {"participant_id", "interface", "time_to_success_ms",
                "iteration_count", "vector_match", "semantic_pass"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Validation records missing columns: {missing}")
    return df

def _compute_descriptive_stats(df: pd.DataFrame) -> Dict[str, Dict]:
    """Compute mean/median time and iteration stats per interface."""
    stats = {}
    for iface, sub in df.groupby("interface"):
        # Consider only trials where both checks passed (as required by downstream analysis)
        successful = sub[(sub["vector_match"]) & (sub["semantic_pass"])]
        if successful.empty:
            # Avoid division by zero – report NaNs
            time_mean = time_median = iter_mean = iter_median = float("nan")
        else:
            time_mean = successful["time_to_success_ms"].mean()
            time_median = successful["time_to_success_ms"].median()
            iter_mean = successful["iteration_count"].mean()
            iter_median = successful["iteration_count"].median()
        stats[iface] = {
            "time_mean_ms": time_mean,
            "time_median_ms": time_median,
            "iter_mean": iter_mean,
            "iter_median": iter_median,
        }
    return stats

def _compute_success_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Return a table with vector‑match and semantic‑similarity success rates per interface."""
    rows = []
    for iface, sub in df.groupby("interface"):
        total = len(sub)
        vec_success = sub["vector_match"].sum()
        sem_success = sub["semantic_pass"].sum()
        rows.append({
            "interface": iface,
            "vector_match_success": f"{vec_success}/{total} ({vec_success/total:.1%})",
            "semantic_success": f"{sem_success}/{total} ({sem_success/total:.1%})",
        })
    return pd.DataFrame(rows)

def _load_analysis_results(analysis_dir: Path) -> List[Dict]:
    """Load any JSON‑line analysis result files produced by wilcoxon_analysis."""
    results = []
    if not analysis_dir.is_dir():
        log.warning("Analysis directory does not exist: %s", analysis_dir)
        return results
    for file in analysis_dir.iterdir():
        if file.suffix == ".jsonl":
            results.extend(_load_jsonl(file))
    return results

def _format_analysis_section(analysis_results: List[Dict]) -> str:
    """Render the statistical analysis section of the report."""
    if not analysis_results:
        return "No analysis results were found.\n"

    lines = ["## Statistical Analysis\n"]
    for res in analysis_results:
        metric = res.get("metric", "unknown")
        statistic = res.get("statistic")
        p_value = res.get("p_value")
        bonferroni = res.get("p_value_corrected")
        effect_r = res.get("effect_size_r")
        ci_low, ci_high = res.get("ci_95", (None, None))

        lines.append(f"### {metric.replace('_', ' ').title()}\n")
        lines.append(f"- Wilcoxon statistic: `{statistic}`\n")
        lines.append(f"- p‑value (raw): `{p_value:.5f}`\n")
        if bonferroni is not None:
            lines.append(f"- p‑value (Bonferroni‑corrected): `{bonferroni:.5f}`\n")
        if effect_r is not None:
            lines.append(f"- Effect size *r*: `{effect_r:.3f}`\n")
        if ci_low is not None and ci_high is not None:
            lines.append(f"- 95 % CI of mean difference: `{ci_low:.3f}` – `{ci_high:.3f}`\n")
        lines.append("\n")
    return "\n".join(lines)

def _build_methods_paragraph() -> str:
    """Return a short Methods description referencing pipeline scripts."""
    return (
        "### Methods\\n"
        "The study pipeline consisted of the following steps, each implemented by a "
        "dedicated script in the repository:\\n"
        "- `src.curators.curate_failed_figures.py` – downloaded (or synthetically "
        "generated) a reproducible set of 50 failed figures and injected a single "
        "localized error into each image.\\n"
        "- `src.simulation.simulate_participants.py` – simulated 30 participants, "
        "randomising interface order and generating realistic edit latencies.\\n"
        "- `src.validation.run_validation.py` – performed both exact vector‑match "
        "and semantic‑similarity (cosine similarity ≥ 0.95) checks, writing a "
        "`SemanticValidation` record for each successful trial.\\n"
        "- `src.analysis.wilcoxon_analysis.py` – aggregated the successful trials, "
        "computed paired Wilcoxon signed‑rank tests for *time‑to‑success* and "
        "*iteration count*, applied Bonferroni correction, calculated effect size "
        "*r* and bootstrap 95 % confidence intervals.\\n"
        "- `src.report.generate_report.py` (this script) – collated the descriptive "
        "statistics, success‑rate tables and the Wilcoxon results into this "
        "human‑readable report.\\n"
    )

def _write_report(output_path: Path,
                  descr_stats: Dict[str, Dict],
                  success_table: pd.DataFrame,
                  analysis_md: str) -> None:
    """Compose and write the final markdown report."""
    lines = ["# Cognitive‑load Comparison Study Report\n"]
    lines.append(_build_methods_paragraph())
    lines.append("## Descriptive Statistics\n")

    for iface, stats in descr_stats.items():
        lines.append(f"### {iface.title()} Interface\n")
        lines.append(f"- Mean time to success (ms): `{stats['time_mean_ms']:.2f}`\n")
        lines.append(f"- Median time to success (ms): `{stats['time_median_ms']:.2f}`\n")
        lines.append(f"- Mean iteration count: `{stats['iter_mean']:.2f}`\n")
        lines.append(f"- Median iteration count: `{stats['iter_median']:.2f}`\n")
        lines.append("\n")

    lines.append("## Success‑Rate Tables\n")
    # Render the success table as markdown
    lines.append(success_table.to_markdown(index=False))
    lines.append("\n")

    lines.append(analysis_md)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    log.info("Report written to %s", output_path)

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the final markdown report for the cognitive‑load study."
    )
    parser.add_argument(
        "--validation-dir",
        type=Path,
        default=paths.data("validation"),
        help="Directory containing `semantic_validation.jsonl`.",
    )
    parser.add_argument(
        "--analysis-dir",
        type=Path,
        default=paths.outputs(),
        help="Directory where wilcoxon_analysis JSON‑line results are stored.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=paths.outputs("report.md"),
        help="Path to write the markdown report.",
    )
    return parser.parse_args()

def main() -> int:
    """Entry point for ``python -m src.report.generate_report``."""
    args = _parse_args()

    try:
        df_val = _load_validation_records(args.validation_dir)
    except Exception as e:
        log.error("Failed to load validation records: %s", e)
        return 1

    descr_stats = _compute_descriptive_stats(df_val)
    success_table = _compute_success_rates(df_val)
    analysis_results = _load_analysis_results(args.analysis_dir)
    analysis_md = _format_analysis_section(analysis_results)

    _write_report(args.output_path, descr_stats, success_table, analysis_md)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
