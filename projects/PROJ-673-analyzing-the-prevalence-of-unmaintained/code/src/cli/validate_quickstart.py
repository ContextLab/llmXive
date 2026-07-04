"""
Quickstart Validation Script for PROJ-673
Validates reproducibility by executing the pipeline steps defined in quickstart.md
and verifying output artifacts exist and are non-empty.
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.cli.collect_data import main as collect_data_main
from src.cli.export_data import main as export_data_main
from src.analysis.correlation import run_correlation_analysis
from src.analysis.visualizer import main as visualize_main
from src.cli.generate_report import main as report_main
from src.analysis.sensitivity_analysis import run_sensitivity_analysis
from src.utils.checksum import generate_checksum, write_checksum_file

# Configuration
OUTPUT_DIR = project_root / "data" / "processed"
REPORT_DIR = project_root / "docs"
RAW_DATA_DIR = project_root / "data" / "raw"
CHECKSUM_FILE = OUTPUT_DIR / "checksums.json"

# Expected artifacts from quickstart.md
EXPECTED_ARTIFACTS = [
    "dependencies_raw.csv",
    "results_correlation.json",
    "sensitivity_analysis.json",
    "metrics.json",
    "figures/age_vs_vulnerability.png",
    "figures/category_distribution.png",
    "report.md"
]

def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def ensure_dirs():
    """Ensure all required directories exist."""
    log("Ensuring output directories exist...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "figures").mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parently=True, exist_ok=True)
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

def run_data_collection():
    """Step 1: Run data collection pipeline."""
    log("Step 1: Executing data collection pipeline...")
    try:
        # The collect_data script orchestrates fetching and initial processing
        # We call the main function directly. Note: In a real scenario, this might
        # require mocking or a subset of data to avoid long runtimes in validation.
        # For this validation task, we assume the pipeline is designed to handle
        # rate limits and timeouts gracefully.
        collect_data_main()
        log("Data collection completed successfully.")
        return True
    except Exception as e:
        log(f"Data collection failed: {e}", "ERROR")
        return False

def run_export():
    """Step 2: Export processed data to CSV."""
    log("Step 2: Exporting data to CSV...")
    try:
        export_data_main()
        log("Data export completed successfully.")
        return True
    except Exception as e:
        log(f"Data export failed: {e}", "ERROR")
        return False

def run_analysis():
    """Step 3: Run correlation analysis."""
    log("Step 3: Running correlation analysis...")
    try:
        input_file = OUTPUT_DIR / "dependencies_raw.csv"
        if not input_file.exists():
            log(f"Input file not found: {input_file}", "ERROR")
            return False
        
        results = run_correlation_analysis(str(input_file))
        
        output_file = OUTPUT_DIR / "results_correlation.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        log("Correlation analysis completed and saved.")
        return True
    except Exception as e:
        log(f"Correlation analysis failed: {e}", "ERROR")
        return False

def run_visualization():
    """Step 4: Generate visualizations."""
    log("Step 4: Generating visualizations...")
    try:
        visualize_main()
        log("Visualizations generated successfully.")
        return True
    except Exception as e:
        log(f"Visualization generation failed: {e}", "ERROR")
        return False

def run_sensitivity():
    """Step 5: Run sensitivity analysis."""
    log("Step 5: Running sensitivity analysis...")
    try:
        input_file = OUTPUT_DIR / "dependencies_raw.csv"
        if not input_file.exists():
            log(f"Input file not found: {input_file}", "ERROR")
            return False
        
        run_sensitivity_analysis(str(input_file))
        log("Sensitivity analysis completed.")
        return True
    except Exception as e:
        log(f"Sensitivity analysis failed: {e}", "ERROR")
        return False

def run_report():
    """Step 6: Generate final report."""
    log("Step 6: Generating final report...")
    try:
        report_main()
        log("Report generation completed.")
        return True
    except Exception as e:
        log(f"Report generation failed: {e}", "ERROR")
        return False

def verify_artifacts():
    """Verify all expected artifacts exist and are non-empty."""
    log("Verifying output artifacts...")
    missing = []
    empty = []
    
    for artifact in EXPECTED_ARTIFACTS:
        full_path = OUTPUT_DIR.parent / "data" / "processed" / artifact
        # Adjust for report which is in docs
        if artifact == "report.md":
            full_path = REPORT_DIR / artifact
        
        if not full_path.exists():
            missing.append(artifact)
        elif full_path.stat().st_size == 0:
            empty.append(artifact)
    
    if missing:
        log(f"Missing artifacts: {missing}", "ERROR")
    if empty:
        log(f"Empty artifacts: {empty}", "ERROR")
    
    return len(missing) == 0 and len(empty) == 0

def generate_checksums():
    """Generate checksums for all output artifacts."""
    log("Generating checksums...")
    checksums = {}
    
    artifacts_to_checksum = [
        "dependencies_raw.csv",
        "results_correlation.json",
        "sensitivity_analysis.json",
        "metrics.json",
        "figures/age_vs_vulnerability.png",
        "figures/category_distribution.png",
        "report.md"
    ]
    
    for artifact in artifacts_to_checksum:
        full_path = OUTPUT_DIR / artifact
        if artifact == "report.md":
            full_path = REPORT_DIR / artifact
        
        if full_path.exists():
          checksums[artifact] = generate_checksum(full_path)
        
    checksum_file = OUTPUT_DIR / "checksums.json"
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    log(f"Checksums saved to {checksum_file}")

def main():
    log("Starting Quickstart Validation for PROJ-673")
    log(f"Project Root: {project_root}")
    
    ensure_dirs()
    
    # Execute pipeline steps
    steps = [
        ("Data Collection", run_data_collection),
        ("Data Export", run_export),
        ("Correlation Analysis", run_analysis),
        ("Visualization", run_visualization),
        ("Sensitivity Analysis", run_sensitivity),
        ("Report Generation", run_report),
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        if not step_func():
            log(f"Validation stopped at {step_name} due to failure.", "ERROR")
            return 1
        success_count += 1
    
    # Verify outputs
    if not verify_artifacts():
        log("Artifact verification failed.", "ERROR")
        return 1
    
    # Generate checksums
    generate_checksums()
    
    log("Quickstart validation PASSED. All artifacts generated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())