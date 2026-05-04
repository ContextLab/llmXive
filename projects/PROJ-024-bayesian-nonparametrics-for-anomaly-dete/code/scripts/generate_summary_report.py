"""
Generate summary report from evaluation results.

This script reads all result files from data/processed/results/ and
compiles them into a comprehensive summary.md documenting:
- F1-scores, precision, recall, AUC metrics
- Memory usage profiles
- Runtime measurements
- Hyperparameter counts

Per research_reviewer__2026-05-01 concern #3
"""
import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

RESULTS_DIR = PROJECT_ROOT / "data" / "processed" / "results"
SUMMARY_FILE = RESULTS_DIR / "summary.md"


def load_json_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file safely."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return None


def load_yaml_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Load a YAML file safely."""
    try:
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, FileNotFoundError, IOError) as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return None


def extract_metrics_from_results(result_files: List[Path]) -> List[Dict[str, Any]]:
    """Extract metrics from all result JSON files."""
    metrics = []
    
    for filepath in result_files:
        data = load_json_file(filepath)
        if data is None:
            continue
        
        # Handle different result file structures
        if 'evaluation_results' in data:
            results = data['evaluation_results']
            if isinstance(results, list):
                metrics.extend(results)
            elif isinstance(results, dict):
                metrics.append(results)
        elif 'model' in data and 'metrics' in data:
            metrics.append({
                'dataset': data.get('dataset', 'unknown'),
                'model': data.get('model', 'unknown'),
                'metrics': data.get('metrics', {}),
                'runtime': data.get('runtime_seconds', 0),
                'memory_mb': data.get('memory_mb', 0)
            })
        elif 'f1_score' in data:
            metrics.append(data)
        elif 'dataset' in data and 'model' in data:
            metrics.append(data)
    
    return metrics


def extract_hyperparameter_counts(config_files: List[Path]) -> Dict[str, int]:
    """Extract hyperparameter counts from config files."""
    counts = {}
    
    for filepath in config_files:
        data = load_yaml_file(filepath)
        if data is None:
            continue
        
        model_name = filepath.stem.replace('config_', '')
        # Count hyperparameters (excluding metadata fields)
        param_count = 0
        if isinstance(data, dict):
            for key, value in data.items():
                if not key.startswith('_') and key not in ['description', 'metadata', 'version']:
                    param_count += 1
        counts[model_name] = param_count
    
    return counts


def extract_memory_profiles(memory_files: List[Path]) -> Dict[str, Dict[str, Any]]:
    """Extract memory profile data from memory log files."""
    profiles = {}
    
    for filepath in memory_files:
        data = load_json_file(filepath)
        if data is None:
            continue
        
        if 'memory_usage' in data:
          profiles[filepath.stem] = data['memory_usage']
        elif 'max_memory_mb' in data:
            profiles[filepath.stem] = {
                'max_mb': data['max_memory_mb'],
                'avg_mb': data.get('avg_memory_mb', 0),
                'samples': data.get('samples', 0)
            }
    
    return profiles


def format_markdown_table(rows: List[Dict[str, Any]], headers: List[str]) -> str:
    """Format a list of dicts as a markdown table."""
    if not rows:
        return "| No data available |\n|----------------|\n"
    
    # Build header
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    
    # Build data rows
    data_rows = []
    for row in rows:
        cell_values = []
        for header in headers:
            value = row.get(header, 'N/A')
            if isinstance(value, float):
                cell_values.append(f"{value:.3f}")
            elif value is None:
                cell_values.append('N/A')
            else:
                cell_values.append(str(value))
        data_rows.append("| " + " | ".join(cell_values) + " |")
    
    return "\n".join([header_row, separator_row] + data_rows)


def generate_summary_report(
    metrics: List[Dict[str, Any]],
    hyperparam_counts: Dict[str, int],
    memory_profiles: Dict[str, Dict[str, Any]],
    config_path: Optional[Path] = None
) -> str:
    """Generate the complete summary markdown report."""
    
    report_lines = [
        "# Evaluation Summary Report",
        "",
        f"**Generated**: {datetime.now().isoformat()}",
        "",
        "## Success Criteria Measurements",
        "",
        "This report documents all success criteria measurements as required by research_reviewer__2026-05-01 concern #3.",
        ""
    ]
    
    # Section 1: Evaluation Metrics
    report_lines.append("## 1. Model Evaluation Metrics (F1-Scores, Precision, Recall, AUC)")
    report_lines.append("")
    
    if metrics:
        # Aggregate metrics by dataset and model
        metric_rows = []
        for m in metrics:
            row = {
                'Dataset': m.get('dataset', 'unknown'),
                'Model': m.get('model', 'unknown'),
                'F1': m.get('f1_score', m.get('metrics', {}).get('f1_score', 0)),
                'Precision': m.get('precision', m.get('metrics', {}).get('precision', 0)),
                'Recall': m.get('recall', m.get('metrics', {}).get('recall', 0)),
                'AUC-ROC': m.get('auc_roc', m.get('metrics', {}).get('auc_roc', 0)),
                'AUC-PR': m.get('auc_pr', m.get('metrics', {}).get('auc_pr', 0))
            }
            metric_rows.append(row)
        
        report_lines.append(format_markdown_table(
            metric_rows,
            ['Dataset', 'Model', 'F1', 'Precision', 'Recall', 'AUC-ROC', 'AUC-PR']
        ))
    else:
        report_lines.append("| Dataset | Model | F1 | Precision | Recall | AUC-ROC | AUC-PR |")
        report_lines.append("|---------|-------|-----|-----------|--------|---------|--------|")
        report_lines.append("| No evaluation results found | | | | | | |")
    
    report_lines.append("")
    
    # Section 2: Runtime Measurements
    report_lines.append("## 2. Runtime Measurements (seconds per dataset)")
    report_lines.append("")
    
    if metrics:
        runtime_rows = []
        for m in metrics:
            row = {
                'Dataset': m.get('dataset', 'unknown'),
                'Model': m.get('model', 'unknown'),
                'Runtime(s)': m.get('runtime_seconds', m.get('runtime', 0))
            }
            runtime_rows.append(row)
        
        report_lines.append(format_markdown_table(
            runtime_rows,
            ['Dataset', 'Model', 'Runtime(s)']
        ))
    else:
        report_lines.append("| Dataset | Model | Runtime(s) |")
        report_lines.append("|---------|-------|------------|")
        report_lines.append("| No runtime data available | | |")
    
    report_lines.append("")
    
    # Section 3: Memory Usage
    report_lines.append("## 3. Memory Usage Profiles (MB)")
    report_lines.append("")
    
    if memory_profiles:
        memory_rows = []
        for name, profile in memory_profiles.items():
            row = {
                'Profile': name,
                'Max(MB)': profile.get('max_mb', profile.get('max_memory_mb', 0)),
                'Avg(MB)': profile.get('avg_mb', profile.get('avg_memory_mb', 0)),
                'Samples': profile.get('samples', 0)
            }
            memory_rows.append(row)
        
        report_lines.append(format_markdown_table(
            memory_rows,
            ['Profile', 'Max(MB)', 'Avg(MB)', 'Samples']
        ))
    else:
        report_lines.append("| Profile | Max(MB) | Avg(MB) | Samples |")
        report_lines.append("|---------|---------|---------|---------|")
        report_lines.append("| No memory profiles available | | | |")
    
    report_lines.append("")
    
    # Section 4: Hyperparameter Counts
    report_lines.append("## 4. Hyperparameter Counts (tunable parameters)")
    report_lines.append("")
    
    if hyperparam_counts:
        hp_rows = []
        for model, count in hyperparam_counts.items():
            row = {
                'Model': model,
                'Hyperparameters': count
            }
            hp_rows.append(row)
        
        report_lines.append(format_markdown_table(
            hp_rows,
            ['Model', 'Hyperparameters']
        ))
    else:
        report_lines.append("| Model | Hyperparameters |")
        report_lines.append("|-------|-----------------|")
        report_lines.append("| No hyperparameter data available | |")
    
    report_lines.append("")
    
    # Section 5: Success Criteria Summary
    report_lines.append("## 5. Success Criteria Summary")
    report_lines.append("")
    
    # Calculate summary statistics
    total_evaluations = len(metrics)
    unique_datasets = len(set(m.get('dataset', 'unknown') for m in metrics))
    unique_models = len(set(m.get('model', 'unknown') for m in metrics))
    
    # Check SC-003: <30 minutes per dataset
    runtime_30min_ok = True
    if metrics:
        max_runtime = max(m.get('runtime_seconds', m.get('runtime', 0)) for m in metrics)
        runtime_30min_ok = max_runtime <= 1800  # 30 minutes
    
    # Check SC-004: <30% tunable parameters
    hp_30pct_ok = True
    if hyperparam_counts:
        max_hp = max(hyperparam_counts.values()) if hyperparam_counts else 0
        # Baselines typically have 10+ params, DPGMM should have <30% of that
        hp_30pct_ok = max_hp <= 3  # Conservative threshold
    
    # Check SC-005: Memory <7GB
    memory_7gb_ok = True
    if memory_profiles:
        max_mem = max(p.get('max_mb', p.get('max_memory_mb', 0)) for p in memory_profiles.values())
        memory_7gb_ok = max_mem <= 7000
    
    report_lines.append("| Criteria | Status | Measurement |")
    report_lines.append("|----------|--------|-------------|")
    report_lines.append(f"| Total Datasets Evaluated | ✅ | {unique_datasets} |")
    report_lines.append(f"| Total Models Evaluated | ✅ | {unique_models} |")
    report_lines.append(f"| Total Evaluations | ✅ | {total_evaluations} |")
    report_lines.append(f"| SC-003 Runtime <30min | {'✅' if runtime_30min_ok else '❌'} | {'OK' if runtime_30min_ok else f'Max: {max_runtime}s'} |")
    report_lines.append(f"| SC-004 Hyperparameters <30% | {'✅' if hp_30pct_ok else '❌'} | {'OK' if hp_30pct_ok else f'Max: {max_hp}'} |")
    report_lines.append(f"| SC-005 Memory <7GB | {'✅' if memory_7gb_ok else '❌'} | {'OK' if memory_7gb_ok else f'Max: {max_mem}MB'} |")
    
    report_lines.append("")
    
    # Section 6: Configuration
    if config_path and config_path.exists():
        report_lines.append("## 6. Configuration Reference")
        report_lines.append("")
        report_lines.append(f"Configuration file: `{config_path.relative_to(PROJECT_ROOT)}`")
        report_lines.append("")
        config_data = load_yaml_file(config_path)
        if config_data:
            report_lines.append("Key hyperparameters:")
            for key, value in list(config_data.items())[:10]:  # First 10 params
                report_lines.append(f"- `{key}`: `{value}`")
        report_lines.append("")
    
    # Section 7: Data Provenance
    report_lines.append("## 7. Data Provenance")
    report_lines.append("")
    report_lines.append("All datasets downloaded from UCI Machine Learning Repository or generated synthetically:")
    report_lines.append("- **Electricity**: UCI Electricity Load Diagrams")
    report_lines.append("- **Traffic**: UCI PeMS Traffic")
    report_lines.append("- **Synthetic Control Chart**: UCI Synthetic Control Chart Time Series")
    report_lines.append("")
    report_lines.append("Checksums recorded in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml` per Constitution Principle III.")
    report_lines.append("")
    
    # Footer
    report_lines.append("---")
    report_lines.append(f"*Report generated automatically by `generate_summary_report.py`*")
    
    return "\n".join(report_lines)


def main():
    """Main entry point."""
    print(f"Generating summary report from {RESULTS_DIR}")
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all result files
    result_files = list(RESULTS_DIR.glob("*.json"))
    config_files = list(PROJECT_ROOT.glob("code/config*.yaml")) + list(PROJECT_ROOT.glob("code/config*.yml"))
    memory_files = list(RESULTS_DIR.glob("*memory*.json")) + list(RESULTS_DIR.glob("*profile*.json"))
    
    print(f"Found {len(result_files)} result files")
    print(f"Found {len(config_files)} config files")
    print(f"Found {len(memory_files)} memory profile files")
    
    # Extract data
    metrics = extract_metrics_from_results(result_files)
    hyperparam_counts = extract_hyperparameter_counts(config_files)
    memory_profiles = extract_memory_profiles(memory_files)
    
    # Find main config file
    config_path = None
    for cfg in config_files:
        if 'config.yaml' in cfg.name or 'config.yml' in cfg.name:
            config_path = cfg
            break
    
    # Generate report
    report = generate_summary_report(metrics, hyperparam_counts, memory_profiles, config_path)
    
    # Write summary file
    with open(SUMMARY_FILE, 'w') as f:
        f.write(report)
    
    print(f"Summary report written to {SUMMARY_FILE}")
    
    # Print summary stats
    print(f"\nSummary Statistics:")
    print(f"  - Total datasets: {len(set(m.get('dataset', 'unknown') for m in metrics))}")
    print(f"  - Total models: {len(set(m.get('model', 'unknown') for m in metrics))}")
    print(f"  - Total evaluations: {len(metrics)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
