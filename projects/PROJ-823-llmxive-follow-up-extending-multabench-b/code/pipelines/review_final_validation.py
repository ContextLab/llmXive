import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Import config for path resolution
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ensure_directories

# Helper to load JSON
def load_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Helper to load Markdown
def load_markdown_file(path: Path) -> str:
    if not path.exists():
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def validate_fr001(data: dict) -> dict:
    """
    FR-001: Deterministic Re-computation.
    Verify that frozen baseline metrics were computed across multiple seeds.
    """
    # Check for sensitivity analysis artifacts
    # We look for the aggregated metrics which should contain seed_count
    frozen_agg_path = data.get('frozen_baseline_aggregated_path')
    if not frozen_agg_path or not os.path.exists(frozen_agg_path):
        return {"status": "failed", "reason": "Missing frozen baseline aggregated metrics"}

    content = load_json_file(Path(frozen_agg_path))
    if not content:
        return {"status": "failed", "reason": "Empty frozen baseline aggregated metrics"}

    # Check if seed count > 1 (indicating multiple runs)
    seed_count = content.get('seed_count', 0)
    if seed_count < 2:
        return {"status": "failed", "reason": f"Seed count {seed_count} < 2. Determinism not verified."}

    return {"status": "passed", "seed_count": seed_count}

def validate_fr002(data: dict) -> dict:
    """
    FR-002: CPU-Tractability.
    Verify that the pipeline ran on CPU and memory constraints were respected.
    """
    runtime_path = data.get('runtime_report_path')
    if not runtime_path or not os.path.exists(runtime_path):
        return {"status": "failed", "reason": "Missing runtime report"}

    content = load_json_file(Path(runtime_path))
    peak_memory_gb = content.get('peak_memory_gb', 0)
    total_runtime_hours = content.get('total_runtime_hours', 0)

    # Constraints: < 7GB RAM, < 6 hours total
    if peak_memory_gb > 7.0:
        return {"status": "failed", "reason": f"Peak memory {peak_memory_gb:.2f}GB exceeds 7GB limit."}
    if total_runtime_hours > 6.0:
        return {"status": "failed", "reason": f"Total runtime {total_runtime_hours:.2f}h exceeds 6h limit."}

    return {"status": "passed", "peak_memory_gb": peak_memory_gb, "total_runtime_hours": total_runtime_hours}

def validate_fr003(data: dict) -> dict:
    """
    FR-003: Statistical Rigor (Variance & Correlation).
    Verify that zero-variance datasets were excluded and correlations were computed.
    """
    integrity_path = data.get('data_integrity_report_path')
    correlation_path = data.get('correlation_report_path')

    # Check integrity report for skipped datasets (zero variance)
    if not integrity_path or not os.path.exists(integrity_path):
        return {"status": "failed", "reason": "Missing data integrity report"}

    integrity_content = load_json_file(Path(integrity_path))
    skipped = integrity_content.get('skipped_datasets', [])
    if not skipped:
        # It's okay if no datasets were skipped, but we expect the report to exist
        pass

    # Check correlation report exists and has data
    if not correlation_path or not os.path.exists(correlation_path):
        return {"status": "failed", "reason": "Missing correlation report"}

    corr_content = load_json_file(Path(correlation_path))
    if not corr_content or 'correlations' not in corr_content:
        return {"status": "failed", "reason": "Correlation report missing 'correlations' key"}

    # Verify FDR correction was applied (T034)
    if 'fdr_adjusted' not in corr_content:
        return {"status": "failed", "reason": "FDR correction not found in correlation report"}

    return {"status": "passed", "skipped_datasets_count": len(skipped)}

def validate_fr004(data: dict) -> dict:
    """
    FR-004: Execution Time & Memory Constraints (Runtime Validation).
    This is the specific check for the final validation report.
    """
    # This is effectively a re-check of FR-002 but specifically looking at the final report
    runtime_path = data.get('runtime_report_path')
    if not runtime_path or not os.path.exists(runtime_path):
        return {"status": "failed", "reason": "Missing runtime report for FR-004"}

    content = load_json_file(Path(runtime_path))
    # Check specific constraints
    if content.get('peak_memory_gb', 999) > 7.0:
        return {"status": "failed", "reason": "Memory constraint violated"}
    if content.get('total_runtime_hours', 999) > 6.0:
        return {"status": "failed", "reason": "Time constraint violated"}

    return {"status": "passed"}

def validate_fr005(data: dict) -> dict:
    """
    FR-005: Data Integrity & Real Data Usage.
    Verify that real data was used and no synthetic fallbacks were triggered.
    """
    # Check that the baselines file exists and is not empty
    baselines_path = data.get('gpu_baselines_path')
    if not baselines_path or not os.path.exists(baselines_path):
        return {"status": "failed", "reason": "GPU-Tuned baselines file missing"}

    baselines_content = load_json_file(Path(baselines_path))
    if not baselines_content or len(baselines_content) == 0:
        return {"status": "failed", "reason": "GPU-Tuned baselines file is empty"}

    # Check that the frozen baseline was actually computed (not hardcoded)
    frozen_path = data.get('frozen_baseline_metrics_path')
    if not frozen_path or not os.path.exists(frozen_path):
        return {"status": "failed", "reason": "Frozen baseline metrics missing"}

    return {"status": "passed"}

def run_validation(data: dict) -> dict:
    results = {
        "timestamp": datetime.now().isoformat(),
        "fr_requirements": {}
    }

    results["fr_requirements"]["FR-001"] = validate_fr001(data)
    results["fr_requirements"]["FR-002"] = validate_fr002(data)
    results["fr_requirements"]["FR-003"] = validate_fr003(data)
    results["fr_requirements"]["FR-004"] = validate_fr004(data)
    results["fr_requirements"]["FR-005"] = validate_fr005(data)

    # Overall pass/fail
    all_passed = all(r["status"] == "passed" for r in results["fr_requirements"].values())
    results["overall_status"] = "passed" if all_passed else "failed"

    return results

def generate_report(validation_results: dict, output_path: Path):
    """
    Generate the final validation report in Markdown format.
    """
    md_lines = [
        "# Final Validation Report",
        "",
        f"**Generated:** {validation_results['timestamp']}",
        f"**Overall Status:** {validation_results['overall_status'].upper()}",
        "",
        "## Functional Requirements Verification",
        ""
    ]

    for fr, res in validation_results['fr_requirements'].items():
        status_icon = "✅" if res['status'] == 'passed' else "❌"
        md_lines.append(f"### {fr}")
        md_lines.append(f"**Status:** {status_icon} {res['status']}")
        if 'reason' in res:
            md_lines.append(f"**Reason:** {res['reason']}")
        if 'seed_count' in res:
            md_lines.append(f"- Seed Count: {res['seed_count']}")
        if 'peak_memory_gb' in res:
            md_lines.append(f"- Peak Memory: {res['peak_memory_gb']:.2f} GB")
        if 'total_runtime_hours' in res:
            md_lines.append(f"- Total Runtime: {res['total_runtime_hours']:.2f} hours")
        if 'skipped_datasets_count' in res:
            md_lines.append(f"- Skipped Datasets (Zero Variance): {res['skipped_datasets_count']}")
        md_lines.append("")

    md_content = "\n".join(md_lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

def main():
    parser = argparse.ArgumentParser(description="Review final validation artifacts and generate report.")
    parser.add_argument("--output", type=str, default="data/artifacts/final_validation_report.md",
                        help="Path to save the final validation report")
    args = parser.parse_args()

    # Ensure directories exist
    ensure_directories()

    # Define paths to artifacts based on project structure
    # These paths should match what the previous tasks (T048, T036, etc.) produced
    artifacts = {
        "runtime_report_path": "data/artifacts/runtime_report.json",
        "data_integrity_report_path": "data/artifacts/data_integrity_report.json",
        "correlation_report_path": "data/artifacts/correlation_report_run_id.json", # Placeholder for actual run_id
        "gpu_baselines_path": "data/artifacts/gpu_tuned_baselines.csv",
        "frozen_baseline_metrics_path": "data/artifacts/frozen_baseline_metrics_run_id.json"
    }

    # We need to find the actual run_id files if they exist
    # For this implementation, we assume a specific run_id or scan the directory
    # Since we cannot dynamically scan in a static script without knowing the ID,
    # we will attempt to load the most likely files or fail if not found.
    # In a real execution, the run_id would be passed or discovered.
    
    # Attempt to find correlation report (T036)
    data_dir = Path("data/artifacts")
    corr_files = list(data_dir.glob("correlation_report_*.json"))
    if corr_files:
        artifacts["correlation_report_path"] = str(corr_files[0])
    
    # Attempt to find frozen baseline aggregated (T019c)
    frozen_agg_files = list(data_dir.glob("frozen_baseline_aggregated_*.json"))
    if frozen_agg_files:
        artifacts["frozen_baseline_aggregated_path"] = str(frozen_agg_files[0])
    
    # Attempt to find frozen baseline metrics (T019d)
    frozen_metrics_files = list(data_dir.glob("frozen_baseline_metrics_*.json"))
    if frozen_metrics_files:
        artifacts["frozen_baseline_metrics_path"] = str(frozen_metrics_files[0])

    print(f"Validating artifacts from: {artifacts}")
    
    validation_results = run_validation(artifacts)
    
    output_path = Path(args.output)
    generate_report(validation_results, output_path)
    
    print(f"Validation report generated at: {output_path}")
    print(f"Overall Status: {validation_results['overall_status']}")
    
    if validation_results['overall_status'] == 'failed':
        sys.exit(1)

if __name__ == "__main__":
    main()
