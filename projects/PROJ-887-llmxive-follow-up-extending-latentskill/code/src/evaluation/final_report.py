import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_project_root, get_results_path, ensure_directories

def load_json_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely, returning None if it doesn't exist or is invalid."""
    try:
        if not file_path.exists():
            print(f"Warning: File not found: {file_path}")
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON {file_path}: {e}")
        return None

def load_yaml_safe(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a YAML file safely, returning None if it doesn't exist or is invalid."""
    try:
        if not file_path.exists():
            print(f"Warning: File not found: {file_path}")
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML {file_path}: {e}")
        return None

def aggregate_results(results_dir: Path) -> Dict[str, Any]:
    """Aggregate all result files from the results directory."""
    aggregated = {
        'stats': None,
        'sensitivity': None,
        'latency': None,
        'linearity': None,
        'reconstruction_error': None,
        'power_analysis': None
    }

    # Load stats report
    stats_file = results_dir / 'stats_report.json'
    aggregated['stats'] = load_json_safe(stats_file)

    # Load sensitivity results
    sensitivity_yaml = results_dir / 'sensitivity.yaml'
    sensitivity_raw = results_dir / 'sensitivity_raw.json'
    sensitivity = load_yaml_safe(sensitivity_yaml) or load_json_safe(sensitivity_raw)
    aggregated['sensitivity'] = sensitivity

    # Load latency metrics
    latency_file = results_dir / 'latency_metrics.json'
    aggregated['latency'] = load_json_safe(latency_file)

    # Load linearity validation
    linearity_file = results_dir / 'linearity_validation.json'
    aggregated['linearity'] = load_json_safe(linearity_file)

    # Load reconstruction error
    recon_file = results_dir / 'reconstruction_error.json'
    aggregated['reconstruction_error'] = load_json_safe(recon_file)

    # Load power analysis if present
    if aggregated['stats']:
        aggregated['power_analysis'] = aggregated['stats'].get('power_analysis')

    return aggregated

def generate_report(aggregated: Dict[str, Any], output_path: Path) -> None:
    """Generate the final human-readable Markdown report."""
    ensure_directories([output_path.parent])

    lines = []
    lines.append("# Final Report: llmXive LatentSkill Extension\n")
    lines.append("## 1. Methodology\n")
    lines.append("- **Dataset**: ALFWorld & Search-QA (from HuggingFace: latent-skills/alfworld-weights, latent-skills/searchqa-weights)\n")
    lines.append("- **Base Model**: TinyLlama-1B-Chat-v1.0 (GGUF quantized)\n")
    lines.append("- **Hypernetwork**: Standard Fine-Tuned Baseline (TinyLlamaB adapter) - Proxy used as original unavailable\n")
    lines.append("- **Metrics**: Success Rate, Latency (Embedding, Retrieval, Interpolation), Linearity (Pearson Correlation)\n")
    lines.append("")

    lines.append("## 2. Results\n")

    # Success Rates
    lines.append("### Success Rates\n")
    lines.append("| Strategy | Mean Success Rate | Notes |")
    lines.append("|----------|-------------------|-------|")
    if aggregated['stats'] and 'mean_success_rate' in aggregated['stats']:
        # Extract strategy-specific rates if available in stats
        stats_data = aggregated['stats']
        # Assuming stats_report might have detailed breakdowns or just a mean
        if isinstance(stats_data.get('mean_success_rate'), dict):
            for strat, rate in stats_data['mean_success_rate'].items():
                lines.append(f"| {strat} | {rate:.4f} | |")
        else:
            lines.append(f"| Baseline/Aggregated | {stats_data.get('mean_success_rate', 'N/A')} | Overall mean |")
    else:
        lines.append("| N/A | N/A | Evaluation not completed or stats report missing |")
    lines.append("")

    # Latency
    lines.append("### Latency (ms)\n")
    lines.append("| Metric | Value (ms) |")
    lines.append("|--------|------------|")
    if aggregated['latency']:
        for key, value in aggregated['latency'].items():
            if isinstance(value, (int, float)):
                lines.append(f"| {key} | {value:.2f} |")
    else:
        lines.append("| N/A | N/A | Latency metrics missing |")
    lines.append("")

    # Linearity
    lines.append("### Linearity Validation\n")
    if aggregated['linearity']:
        corr = aggregated['linearity'].get('correlation_coefficient', 'N/A')
        valid = aggregated['linearity'].get('linearity_valid', 'N/A')
        recon_err = aggregated['reconstruction_error']
        max_err = recon_err.get('max_error', 'N/A') if recon_err else 'N/A'
        lines.append(f"- **Pearson Correlation**: {corr}")
        lines.append(f"- **Linearity Valid (SC-005)**: {valid}")
        lines.append(f"- **Max Reconstruction Error**: {max_err}")
    else:
        lines.append("- Linearity validation results missing")
    lines.append("")

    lines.append("## 3. Statistical Significance\n")
    lines.append("### Primary BH Corrected P-Values\n")
    if aggregated['stats'] and 'bh_corrected_primary' in aggregated['stats']:
        for comp, p_val in aggregated['stats']['bh_corrected_primary'].items():
            lines.append(f"- {comp}: {p_val:.4f}")
    else:
        lines.append("- No primary comparisons available")
    lines.append("")

    lines.append("### Sensitivity BH Corrected P-Values\n")
    if aggregated['stats'] and 'bh_corrected_sensitivity' in aggregated['stats']:
        for k_val, p_val in aggregated['stats']['bh_corrected_sensitivity'].items():
            lines.append(f"- k={k_val}: {p_val:.4f}")
    else:
        lines.append("- No sensitivity comparisons available")
    lines.append("")

    lines.append("## 4. Limitations\n")
    if aggregated['power_analysis']:
        power = aggregated['power_analysis'].get('estimated_power', 'N/A')
        lines.append(f"- **Power Analysis**: Estimated power = {power}. {'Warning: Power < 0.8, consider increasing N.' if isinstance(power, float) and power < 0.8 else ''}")
    else:
        lines.append("- Power analysis not performed or results missing.")
    
    lines.append("- **OOD Handling**: Queries with distance > 0.8 raise ValueError (as per T042).")
    lines.append("- **Data Source**: Synthetic proxy weights were used if real HuggingFace datasets were inaccessible (per T012c).")
    lines.append("")
    lines.append("---\n")
    lines.append(f"*Report generated on: {__import__('datetime').datetime.now().isoformat()}*")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    """Main entry point for final report generation."""
    parser = argparse.ArgumentParser(description="Generate final Markdown report from aggregated results.")
    parser.add_argument('--results-dir', type=str, default=None,
                        help="Path to results directory (default: inferred from config)")
    parser.add_argument('--output', type=str, default=None,
                        help="Output path for the report (default: reports/final_report.md)")
    args = parser.parse_args()

    root = get_project_root()
    results_dir = Path(args.results_dir) if args.results_dir else get_results_path(root)
    output_path = Path(args.output) if args.output else root / 'reports' / 'final_report.md'

    print(f"Aggregating results from: {results_dir}")
    aggregated = aggregate_results(results_dir)

    print(f"Generating report to: {output_path}")
    generate_report(aggregated, output_path)

    print("Final report generation complete.")

if __name__ == "__main__":
    main()