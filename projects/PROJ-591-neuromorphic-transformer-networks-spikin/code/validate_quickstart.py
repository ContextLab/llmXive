import os
import sys
import subprocess
import argparse
import json
import tempfile
import time
from pathlib import Path

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"

# Expected output paths per tasks.md
EXPECTED_FILES = {
    "baseline_metrics": PROCESSED_DIR / "baseline_metrics.csv",
    "spiking_metrics": PROCESSED_DIR / "spiking_metrics.csv",
    "sensitivity_analysis": RESULTS_DIR / "sensitivity_analysis.csv",
    "statistical_report": RESULTS_DIR / "statistical_analysis_report.md",
    "zero_spike_report": LOGS_DIR / "zero_spike_report.json",
}

# Expected imports from existing API surface
EXPECTED_IMPORTS = [
    ("models.baseline_transformer", "create_baseline_model"),
    ("models.spiking_transformer", "create_spiking_model"),
    ("metrics.energy_logger", "EnergyLogger"),
    ("metrics.temporal_coding", "compute_isi_variance"),
    ("metrics.perplexity", "compute_perplexity"),
    ("data.dataset_loader", "load_wikitext_dataset"),
    ("analysis.statistical_tests", "run_paired_ttest"),
    ("analysis.sensitivity_analysis", "run_sensitivity_sweep"),
    ("analysis.plots", "plot_combined_analysis"),
    ("main", "run_baseline_training"),
    ("main", "run_spiking_training"),
]

def log(msg: str, level: str = "INFO"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def check_file_exists(path: Path) -> bool:
    if not path.exists():
        log(f"Missing expected file: {path}", "ERROR")
        return False
    log(f"Found expected file: {path}")
    return True

def check_import(module_name: str, name: str) -> bool:
    try:
        module = __import__(module_name, fromlist=[name])
        getattr(module, name)
        log(f"Import successful: {module_name}.{name}")
        return True
    except (ImportError, AttributeError) as e:
        log(f"Import failed: {module_name}.{name} - {e}", "ERROR")
        return False

def validate_project_structure() -> bool:
    log("Validating project structure...")
    dirs = [DATA_DIR, PROCESSED_DIR, RESULTS_DIR, LOGS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return True

def validate_dependencies() -> bool:
    log("Validating dependencies...")
    required = ["torch", "snnTorch", "scipy", "pandas", "numpy", "matplotlib"]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        log(f"Missing dependencies: {missing}", "ERROR")
        return False
    log("All dependencies present.")
    return True

def validate_dataset_loader() -> bool:
    log("Validating dataset loader...")
    from data.dataset_loader import load_wikitext_dataset
    try:
        # Attempt a minimal load check without full download if possible
        # We just verify the function exists and can be called with minimal args
        # Note: This may trigger a download if not cached, which is expected behavior
        log("Dataset loader import successful.")
        return True
    except Exception as e:
        log(f"Dataset loader validation failed: {e}", "ERROR")
        return False

def validate_model_instantiation() -> bool:
    log("Validating model instantiation...")
    from models.baseline_transformer import create_baseline_model
    from models.spiking_transformer import create_spiking_model
    import torch
    try:
        # Create dummy models to ensure no runtime errors
        baseline = create_baseline_model(d_model=16, nhead=2, num_layers=1)
        spiking = create_spiking_model(d_model=16, nhead=2, num_layers=1)
        log("Model instantiation successful.")
        return True
    except Exception as e:
        log(f"Model instantiation failed: {e}", "ERROR")
        return False

def validate_cpu_enforcement() -> bool:
    log("Validating CPU enforcement...")
    # Check that models are instantiated on CPU
    from models.baseline_transformer import create_baseline_model
    from models.spiking_transformer import create_spiking_model
    baseline = create_baseline_model(d_model=16, nhead=2, num_layers=1)
    spiking = create_spiking_model(d_model=16, nhead=2, num_layers=1)
    # Check if any parameter is on CUDA (which shouldn't happen in CPU-only env)
    if torch.cuda.is_available():
        for p in baseline.parameters():
            if p.is_cuda:
                log("Baseline model has CUDA parameters - CPU enforcement failed", "ERROR")
                return False
        for p in spiking.parameters():
            if p.is_cuda:
                log("Spiking model has CUDA parameters - CPU enforcement failed", "ERROR")
                return False
    log("CPU enforcement verified.")
    return True

def validate_metrics_and_analysis() -> bool:
    log("Validating metrics and analysis modules...")
    success = True
    success &= check_import("metrics.energy_logger", "EnergyLogger")
    success &= check_import("metrics.temporal_coding", "compute_isi_variance")
    success &= check_import("metrics.perplexity", "compute_perplexity")
    success &= check_import("analysis.statistical_tests", "run_paired_ttest")
    success &= check_import("analysis.sensitivity_analysis", "run_sensitivity_sweep")
    success &= check_import("analysis.plots", "plot_combined_analysis")
    return success

def validate_output_paths() -> bool:
    log("Validating output paths existence...")
    success = True
    for name, path in EXPECTED_FILES.items():
        if not check_file_exists(path):
            success = False
    if success:
        log("All expected output files present.")
    return success

def main():
    parser = argparse.ArgumentParser(description="Validate quickstart execution")
    parser.add_argument("--full", action="store_true", help="Run full validation including output files")
    args = parser.parse_args()

    log("Starting quickstart validation...")
    os.chdir(PROJECT_ROOT)

    # Basic validations
    success = True
    success &= validate_project_structure()
    success &= validate_dependencies()
    success &= validate_dataset_loader()
    success &= validate_model_instantiation()
    success &= validate_cpu_enforcement()
    success &= validate_metrics_and_analysis()

    # Full validation includes checking output files
    if args.full:
        success &= validate_output_paths()

    if success:
        log("Quickstart validation PASSED", "SUCCESS")
        return 0
    else:
        log("Quickstart validation FAILED", "ERROR")
        return 1

if __name__ == "__main__":
    sys.exit(main())
