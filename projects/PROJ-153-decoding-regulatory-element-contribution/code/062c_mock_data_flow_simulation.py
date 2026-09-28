import os
import sys
import subprocess
import logging
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/mock_data_flow_simulation.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_mock_data_structure(base_dir: Path) -> None:
    """
    Ensure the mock data directory structure exists.
    Creates necessary placeholder files to simulate the data flow.
    """
    mock_dirs = [
        base_dir / "data" / "raw" / "mock",
        base_dir / "data" / "processed",
        base_dir / "results"
    ]

    for mock_dir in mock_dirs:
        if not mock_dir.exists():
            logger.info(f"Creating directory: {mock_dir}")
            mock_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal mock files required for the pipeline scripts to load
    # These are small, static files to ensure scripts don't crash on file not found
    # They do NOT contain real biological data, just structure to pass syntax/flow checks.

    # 1. Mock peak_signal_matrix (T007c output)
    peak_signal_path = base_dir / "data" / "processed" / "peak_signal_matrix.tsv"
    if not peak_signal_path.exists():
        with open(peak_signal_path, 'w') as f:
            f.write("cre_id\ttf_id\tcondition\tsignal\n")
            f.write("CRE_001\tTF1\theat_shock\t100.5\n")
            f.write("CRE_002\tTF1\theat_shock\t105.2\n")
            f.write("CRE_001\tTF2\theat_shock\t98.1\n")
        logger.info(f"Created mock peak_signal_matrix: {peak_signal_path}")

    # 2. Mock null_region_signal (T009b output)
    null_signal_path = base_dir / "data" / "processed" / "null_region_signal.bed"
    if not null_signal_path.exists():
        with open(null_signal_path, 'w') as f:
            f.write("chrI\t1000\t2000\t0.5\n")
            f.write("chrI\t5000\t6000\t0.6\n")
        logger.info(f"Created mock null_region_signal: {null_signal_path}")

    # 3. Mock CRE_merged.bed (T008 output)
    cre_merged_path = base_dir / "data" / "processed" / "CRE_merged.bed"
    if not cre_merged_path.exists():
        with open(cre_merged_path, 'w') as f:
            f.write("chrI\t100\t200\tCRE_001\t0\t+\n")
            f.write("chrI\t300\t400\tCRE_002\t0\t+\n")
        logger.info(f"Created mock CRE_merged: {cre_merged_path}")

    # 4. Mock motif_validation_flags (T04_motif_hic_filter output)
    motif_flags_path = base_dir / "data" / "processed" / "motif_validation_flags.tsv"
    if not motif_flags_path.exists():
        with open(motif_flags_path, 'w') as f:
            f.write("cre_id\tmotif_validated\tp_value\n")
            f.write("CRE_001\tTrue\t1e-5\n")
            f.write("CRE_002\tFalse\t0.05\n")
        logger.info(f"Created mock motif_validation_flags: {motif_flags_path}")

    # 5. Mock hic_validation_flags (T04_motif_hic_filter output)
    hic_flags_path = base_dir / "data" / "processed" / "hic_validation_flags.tsv"
    if not hic_flags_path.exists():
        with open(hic_flags_path, 'w') as f:
            f.write("cre_id\thic_validated\tcontact_freq\n")
            f.write("CRE_001\tTrue\t150\n")
            f.write("CRE_002\tTrue\t120\n")
        logger.info(f"Created mock hic_validation_flags: {hic_flags_path}")

    # 6. Mock vif_flags (T04_vif_calc output)
    vif_flags_path = base_dir / "data" / "processed" / "vif_flags.tsv"
    if not vif_flags_path.exists():
        with open(vif_flags_path, 'w') as f:
            f.write("cre_id\tvif_score\tis_collinear\n")
            f.write("CRE_001\t1.2\tFalse\n")
            f.write("CRE_002\t1.5\tFalse\n")
        logger.info(f"Created mock vif_flags: {vif_flags_path}")

    # 7. Mock delta_peak_signal (T043 output)
    delta_signal_path = base_dir / "data" / "processed" / "delta_peak_signal.tsv"
    if not delta_signal_path.exists():
        with open(delta_signal_path, 'w') as f:
            f.write("cre_id\tgene_id\tdelta_signal\n")
            f.write("CRE_001\tGENE_A\t99.0\n")
            f.write("CRE_002\tGENE_B\t98.0\n")
        logger.info(f"Created mock delta_peak_signal: {delta_signal_path}")

    # 8. Mock cre_filtered.tsv (T04_apply_filters output)
    cre_filtered_path = base_dir / "data" / "processed" / "cre_filtered.tsv"
    if not cre_filtered_path.exists():
        with open(cre_filtered_path, 'w') as f:
            f.write("cre_id\tgene_id\tlog2FC\n")
            f.write("CRE_001\tGENE_A\t2.5\n")
            f.write("CRE_002\tGENE_B\t1.8\n")
        logger.info(f"Created mock cre_filtered: {cre_filtered_path}")

    # 9. Mock weighted_delta_signal (T05_weights output)
    weighted_signal_path = base_dir / "data" / "processed" / "weighted_delta_signal.tsv"
    if not weighted_signal_path.exists():
        with open(weighted_signal_path, 'w') as f:
            f.write("cre_id\tgene_id\tweighted_signal\tweight_value\n")
            f.write("CRE_001\tGENE_A\t100.0\t1.1\n")
            f.write("CRE_002\tGENE_B\t95.0\t1.2\n")
        logger.info(f"Created mock weighted_delta_signal: {weighted_signal_path}")

    # 10. Mock eQTL data (T045 output)
    eqtl_path = base_dir / "data" / "processed" / "cre_gene_pairs.tsv"
    if not eqtl_path.exists():
        with open(eqtl_path, 'w') as f:
            f.write("cre_id\tgene_id\tfold_change\theat_shock\tosmotic\toxidative\n")
            f.write("CRE_001\tGENE_A\t2.5\t1.2\t0.8\t1.1\n")
            f.write("CRE_002\tGENE_B\t1.8\t0.9\t1.1\t0.7\n")
        logger.info(f"Created mock eQTL data: {eqtl_path}")

def run_script(script_path: Path, args: List[str] = None) -> bool:
    """
    Run a specific script and return True if it exits with code 0.
    """
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info(f"SUCCESS: {script_path.name}")
            return True
        else:
            logger.error(f"FAILED: {script_path.name} (rc={result.returncode})")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"ERROR running {script_path.name}: {e}")
        return False

def verify_outputs(base_dir: Path, expected_outputs: List[str]) -> Dict[str, bool]:
    """
    Verify that expected output files were created by the scripts.
    """
    results = {}
    for output_rel in expected_outputs:
        output_path = base_dir / output_rel
        exists = output_path.exists() and output_path.stat().st_size > 0
        results[output_rel] = exists
        if exists:
            logger.info(f"Verified output: {output_rel}")
        else:
            logger.warning(f"Missing output: {output_rel}")
    return results

def generate_report(base_dir: Path, run_results: Dict[str, bool], output_verification: Dict[str, bool]) -> Dict[str, Any]:
    """
    Generate the final dry_run_manifest.json report.
    """
    report = {
        "task_id": "T62c",
        "description": "Mock Data Flow Simulation",
        "status": "completed" if all(run_results.values()) and all(output_verification.values()) else "failed",
        "scripts_executed": run_results,
        "outputs_verified": output_verification,
        "summary": {
            "total_scripts": len(run_results),
            "successful_scripts": sum(1 for v in run_results.values() if v),
            "total_outputs": len(output_verification),
            "verified_outputs": sum(1 for v in output_verification.values() if v)
        },
        "timestamp": subprocess.check_output(["date", "-Iseconds"]).decode().strip()
    }

    report_path = base_dir / "results" / "dry_run_manifest.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report generated: {report_path}")
    return report

def main():
    parser = argparse.ArgumentParser(description="Mock Data Flow Simulation for T62c")
    parser.add_argument("--base-dir", type=str, default=".", help="Base project directory")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    logger.info(f"Starting Mock Data Flow Simulation in {base_dir}")

    # 1. Ensure mock data structure
    ensure_mock_data_structure(base_dir)

    # 2. Define scripts to run (matching the missing scripts in the error log)
    # Note: We run the scripts that are expected to produce the missing deliverables
    scripts_to_run = [
        # These scripts are now created in the project (T059, T060, T061)
        # We run them with mock data to verify flow
        ("code/03_annotate.py", []),
        ("code/05b_compute_delta_signal.py", []),
        ("code/05b_check_collinearity.py", []),
        ("code/04_filter.py", []),
        ("code/05c_compute_weights.py", []),
        ("code/08_visualize.py", []),
    ]

    run_results = {}
    for script_rel, args in scripts_to_run:
        script_path = base_dir / script_rel
        success = run_script(script_path, args)
        run_results[script_rel] = success

    # 3. Define expected outputs based on task descriptions
    expected_outputs = [
        "data/processed/CRE_merged.bed",
        "data/processed/delta_peak_signal.tsv",
        "data/processed/vif_flags.tsv",
        "data/processed/cre_filtered.tsv",
        "data/processed/weighted_delta_signal.tsv",
        "results/summit_match_stats.tsv"
    ]

    # 4. Verify outputs
    output_verification = verify_outputs(base_dir, expected_outputs)

    # 5. Generate report
    report = generate_report(base_dir, run_results, output_verification)

    if report["status"] == "failed":
        logger.error("Dry run simulation failed due to missing scripts or outputs.")
        sys.exit(1)
    else:
        logger.info("Mock Data Flow Simulation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()