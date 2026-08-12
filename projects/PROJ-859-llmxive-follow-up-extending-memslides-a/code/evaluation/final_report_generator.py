"""
Final Report Generator for llmXive Trace Compressibility Analysis.

Compiles statistical analysis, sensitivity sweeps, imputation summaries,
and data lineage into a single comprehensive Markdown report.
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

# Import config for path resolution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_config

class FinalReportError(Exception):
    """Custom exception for report generation failures."""
    pass

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    if not file_path.exists():
        raise FinalReportError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise FinalReportError(f"Error reading file {file_path} for hashing: {e}")

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise FinalReportError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise FinalReportError(f"Error loading {file_path}: {e}")

def load_markdown_safe(file_path: Path) -> Optional[str]:
    """Safely load a Markdown file."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise FinalReportError(f"Error loading {file_path}: {e}")

def load_csv_safe(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Safely load a CSV file into a list of dicts."""
    if not file_path.exists():
        return None
    try:
        import csv
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        raise FinalReportError(f"Error loading {file_path}: {e}")

def generate_data_provenance_section(
    stats_data: Optional[Dict], 
    sweep_data: Optional[List], 
    imputation_data: Optional[Dict], 
    lineage_data: Optional[Dict],
    config: Any
) -> str:
    """Generate the Data Provenance section of the report."""
    lines = []
    lines.append("## Data Provenance")
    lines.append("")
    lines.append("This section documents the exact sources, processing parameters, and integrity checks for the data used in this analysis.")
    lines.append("")
    
    # 1. Configuration & Seed
    lines.append("### Configuration & Random Seed")
    lines.append(f"- **Project Seed**: {config.SEED}")
    lines.append(f"- **Execution Timestamp**: {datetime.now().isoformat()}")
    lines.append(f"- **Python Version**: {sys.version}")
    lines.append("")

    # 2. Imputation Summary
    lines.append("### Imputation Statistics")
    if imputation_data:
        total_traces = imputation_data.get('total_traces', 0)
        imputed_count = imputation_data.get('imputed_count', 0)
        imputed_pct = (imputed_count / total_traces * 100) if total_traces > 0 else 0.0
        lines.append(f"- **Total Traces Processed**: {total_traces}")
        lines.append(f"- **Traces with Imputed Values**: {imputed_count} ({imputed_pct:.2f}%)")
        lines.append("")
        lines.append("#### Imputation Breakdown by Reason")
        if 'reasons' in imputation_data:
            for reason, count in imputation_data['reasons'].items():
                lines.append(f"- `{reason}`: {count}")
        else:
            lines.append("- No specific reason breakdown available.")
        lines.append("")
    else:
        lines.append("- **Warning**: Imputation summary file not found. Assuming 0 imputations.")
        lines.append("")

    # 3. Artifact Hashes
    lines.append("### Input Artifact Integrity (SHA-256)")
    lines.append("")
    lines.append("| Artifact Name | File Path | SHA-256 Hash |")
    lines.append("| :--- | :--- | :--- |")
    
    artifacts = [
        ("Statistical Analysis", "data/processed/statistical_analysis.json"),
        ("Sensitivity Sweep", "data/processed/sensitivity_sweep.csv"),
        ("Imputation Summary", "data/processed/imputation_summary.md"),
        ("Data Lineage", "data/processed/data_lineage.json"),
        ("Feature Matrix", "data/processed/feature_matrix.csv"),
        ("Benchmark Results", "data/processed/benchmark_results.json"),
        ("Per-Trace Scores", "data/processed/per_trace_scores.csv"),
        ("Global Rules", "data/processed/rules/global_rules.json")
    ]

    base_dir = Path.cwd()
    
    for name, rel_path in artifacts:
        full_path = base_dir / rel_path
        if full_path.exists():
            try:
                file_hash = compute_file_hash(full_path)
                lines.append(f"| {name} | `{rel_path}` | `{file_hash}` |")
            except FinalReportError:
                lines.append(f"| {name} | `{rel_path}` | `ERROR_READING` |")
        else:
            lines.append(f"| {name} | `{rel_path}` | `MISSING` |")
    
    lines.append("")
    return "\n".join(lines)

def generate_statistical_analysis_section(stats_data: Optional[Dict]) -> str:
    """Generate the Statistical Analysis section."""
    lines = []
    lines.append("## Statistical Analysis Results")
    lines.append("")
    
    if not stats_data:
        lines.append("**Warning**: Statistical analysis data not found.")
        lines.append("")
        return "\n".join(lines)

    method = stats_data.get('method_used', 'Unknown')
    lines.append(f"**Method Used**: {method}")
    lines.append("")

    if method == 'beta_regression':
        lines.append("### Beta Regression: Fidelity Loss ~ Structural Metrics")
        lines.append("")
        lines.append("The following model predicts `fidelity_loss` based on sequence entropy, tool repetition frequency, and argument variance.")
        lines.append("")
        
        if 'beta_coefficients' in stats_data:
            lines.append("| Variable | Coefficient | P-Value | Significant (p < 0.05) |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for var, coeff in stats_data['beta_coefficients'].items():
                p_val = stats_data.get('p_values', {}).get(var, 1.0)
                sig = "Yes" if p_val < 0.05 else "No"
                lines.append(f"| {var} | {coeff:.4f} | {p_val:.4f} | {sig} |")
            lines.append("")
        
        if 'model_summary' in stats_data:
            lines.append("#### Model Summary")
            lines.append("```")
            lines.append(stats_data['model_summary'])
            lines.append("```")
            lines.append("")

    elif method == 'spearman_correlation':
        lines.append("### Spearman Correlation: Fidelity Loss vs Metrics")
        lines.append("")
        if 'spearman_coefficients' in stats_data:
            lines.append("| Variable | Correlation (rho) | P-Value | Significant |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for var, rho in stats_data['spearman_coefficients'].items():
                p_val = stats_data.get('p_values', {}).get(var, 1.0)
                sig = "Yes" if p_val < 0.05 else "No"
                lines.append(f"| {var} | {rho:.4f} | {p_val:.4f} | {sig} |")
            lines.append("")

    return "\n".join(lines)

def generate_sensitivity_sweep_section(sweep_data: Optional[List]) -> str:
    """Generate the Sensitivity Sweep section."""
    lines = []
    lines.append("## Sensitivity Sweep Analysis")
    lines.append("")
    
    if not sweep_data:
        lines.append("**Warning**: Sensitivity sweep data not found.")
        lines.append("")
        return "\n".join(lines)

    lines.append("### Trade-off Curve: Compression Ratio vs Fidelity Rate")
    lines.append("")
    lines.append("| Compression Ratio | Fidelity Tolerance | Fidelity Rate | Retrieval Latency (ms) | Rule Count |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")
    
    for row in sweep_data:
        ratio = row.get('compression_ratio', 'N/A')
        tol = row.get('fidelity_tolerance', 'N/A')
        fid_rate = row.get('fidelity_rate', 'N/A')
        latency = row.get('latency', 'N/A')
        rule_count = row.get('rule_count', 'N/A')
        lines.append(f"| {ratio} | {tol} | {fid_rate} | {latency} | {rule_count} |")
    
    lines.append("")
    return "\n".join(lines)

def generate_report(
    stats_path: Path,
    sweep_path: Path,
    imputation_path: Path,
    lineage_path: Path,
    output_path: Path,
    config: Any
) -> None:
    """Compile all sections into the final report."""
    # Load data
    stats_data = load_json_safe(stats_path)
    sweep_data = load_csv_safe(sweep_path)
    imputation_data = load_json_safe(imputation_path)
    lineage_data = load_json_safe(lineage_path)

    # Build report parts
    header = "# llmXive Final Report: Trace Compressibility Analysis\n\n"
    intro = "This report aggregates the results of the trace compressibility analysis, including statistical modeling, sensitivity sweeps, and data lineage verification.\n\n"
    
    provenance = generate_data_provenance_section(stats_data, sweep_data, imputation_data, lineage_data, config)
    stats_section = generate_statistical_analysis_section(stats_data)
    sweep_section = generate_sensitivity_sweep_section(sweep_data)
    
    # Lineage Summary (if available)
    lineage_section = ""
    if lineage_data:
        lineage_section = "## Data Lineage\n\n"
        lineage_section += "A directed acyclic graph (DAG) of data transformations has been generated and saved to `data/processed/data_lineage.json` and `data/processed/data_lineage.dot`.\n\n"
        if 'summary' in lineage_data:
            lineage_section += f"**Summary**: {lineage_data['summary']}\n\n"
    else:
        lineage_section = "## Data Lineage\n\n**Warning**: Lineage data not found.\n\n"

    # Combine
    full_report = header + intro + provenance + stats_section + sweep_section + lineage_section

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_report)

    print(f"Final report generated successfully at: {output_path}")

def main():
    """Entry point for the final report generator."""
    try:
        config = get_config()
        base_dir = Path.cwd()

        # Define paths relative to project root
        stats_path = base_dir / "data" / "processed" / "statistical_analysis.json"
        sweep_path = base_dir / "data" / "processed" / "sensitivity_sweep.csv"
        imputation_path = base_dir / "data" / "processed" / "imputation_summary.md"
        lineage_path = base_dir / "data" / "processed" / "data_lineage.json"
        output_path = base_dir / "data" / "processed" / "final_report.md"

        # Check for existence of critical inputs (fail loud if missing)
        missing = []
        if not stats_path.exists(): missing.append(str(stats_path))
        if not sweep_path.exists(): missing.append(str(sweep_path))
        if not imputation_path.exists(): missing.append(str(imputation_path))
        if not lineage_path.exists(): missing.append(str(lineage_path))

        if missing:
            raise FinalReportError(
                f"Critical input files missing for report generation:\n" + "\n".join(missing)
            )

        generate_report(stats_path, sweep_path, imputation_path, lineage_path, output_path, config)

    except FinalReportError as e:
        print(f"Error generating final report: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
