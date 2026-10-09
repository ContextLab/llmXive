"""
Main pipeline orchestrator for predicting alloy phase diagrams.
Executes the full pipeline from data ingestion to visualization,
now including provenance generation and baseline comparison.
"""
import os
import sys
import argparse
import json
import time
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.checksum import compute_file_sha256
from utils.config import get_config, validate_data_sources
from utils.error_codes import ErrorCode
from setup_data_directories import create_directories as setup_dirs
from features.seed_elemental_properties import main as seed_properties
from ingest.load_data import main as run_ingest
from features.generate_descriptors import main as run_descriptors
from models.train import main as run_training
from models.null_baseline import main as run_null_baseline
from viz.plot_phase_diagrams import main as run_viz
from utils.resource_monitor import get_peak_memory_gb, log_resource_usage
from provenance import generate_provenance

logger = get_logger(__name__)


def ensure_state_directory():
    """Ensure the state directory exists."""
    state_dir = "state/PROJ-485"
    os.makedirs(state_dir, exist_ok=True)
    return state_dir


def load_state(state_file):
    """Load state from YAML/JSON file."""
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            return json.load(f)
    return {"steps": {}, "artifacts": {}}


def save_state(state_file, state):
    """Save state to YAML/JSON file."""
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def update_step_status(state_file, step_name, status, details=None):
    """Update the status of a pipeline step."""
    state = load_state(state_file)
    state["steps"][step_name] = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    save_state(state_file, state)


def update_artifact_hash(state_file, artifact_name, file_path):
    """Compute and store SHA-256 hash of an artifact."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    hash_value = compute_file_sha256(file_path)
    state = load_state(state_file)
    state["artifacts"][artifact_name] = {
        "path": file_path,
        "sha256": hash_value,
        "timestamp": datetime.now().isoformat()
    }
    save_state(state_file, state)


def run_step(step_name, func, state_file, *args, **kwargs):
    """Run a pipeline step with logging and state update."""
    log_info(logger, f"Starting step: {step_name}")
    update_step_status(state_file, step_name, "running")
    try:
        func(*args, **kwargs)
        update_step_status(state_file, step_name, "completed")
        log_info(logger, f"Completed step: {step_name}")
        return True
    except Exception as e:
        log_error(logger, f"Step {step_name} failed: {str(e)}")
        update_step_status(state_file, step_name, "failed", {"error": str(e)})
        return False


def run_data_ingestion(state_file):
    """Run the data ingestion step."""
    run_ingest()
    # Update hashes for ingested data
    update_artifact_hash(state_file, "raw_data", "data/raw/elemental_properties.csv")
    update_artifact_hash(state_file, "processed_descriptors", "data/processed/descriptors.csv")


def run_feature_generation(state_file):
    """Run the feature generation step."""
    run_descriptors()
    update_artifact_hash(state_file, "descriptors", "data/processed/descriptors.csv")


def run_model_training(state_file):
    """Run the model training step and baseline analysis."""
    run_training()
    # Model artifact
    update_artifact_hash(state_file, "model", "data/artifacts/model.pkl")

    # Run null‑baseline analysis to produce baseline_comparison.json
    run_null_baseline()
    update_artifact_hash(state_file, "baseline_comparison", "data/artifacts/baseline_comparison.json")

    # Record resource usage after training
    peak_mem = get_peak_memory_gb()
    exec_time = int(time.time() - start_times["training"])
    log_resource_usage(exec_time, peak_mem, output_path="data/artifacts/resource_log.json")
    update_artifact_hash(state_file, "resource_log", "data/artifacts/resource_log.json")


def run_visualization(state_file):
    """Run the visualization step."""
    run_viz()
    update_artifact_hash(state_file, "fidelity_report", "data/artifacts/fidelity_report.json")
    update_artifact_hash(state_file, "tcs_report", "data/artifacts/tcs_report.json")
    # Update plot hashes if they exist
    plot_dir = "data/artifacts/plots"
    if os.path.exists(plot_dir):
        for plot_file in os.listdir(plot_dir):
            if plot_file.endswith('.png'):
                update_artifact_hash(state_file,
                                     f"plot_{plot_file}",
                                     os.path.join(plot_dir, plot_file))


def run_provenance(state_file):
    """Generate provenance information for raw inputs."""
    generate_provenance()
    update_artifact_hash(state_file, "provenance", "data/provenance.json")
    update_artifact_hash(state_file, "raw_checksum", "data/raw/checksum.sha256")


def run_compliance_check(state_file):
    """Run the compliance check."""
    from compliance_check import run_compliance_check as check
    check()


def run_pipeline(args):
    """Run the full pipeline."""
    state_file = "state/PROJ-485/pipeline_state.json"
    ensure_state_directory()
    save_state(state_file, {"steps": {}, "artifacts": {}})

    # Global timing dictionary for resource logs
    global start_times
    start_times = {}

    # Step 1: Setup directories
    log_info(logger, "Setting up directories...")
    setup_dirs()

    # Step 2: Seed elemental properties (T007)
    if not os.path.exists("data/raw/elemental_properties.csv"):
        seed_properties()
        update_artifact_hash(state_file, "elemental_properties", "data/raw/elemental_properties.csv")

    # Step 3: Provenance generation (new for T001)
    start_times["provenance"] = time.time()
    if not run_step("provenance", run_provenance, state_file):
        return False

    # Step 4: Data Ingestion (T012‑T020)
    start_times["ingestion"] = time.time()
    if not run_step("ingestion", run_data_ingestion, state_file):
        return False

    # Step 5: Feature Generation (T017‑T020)
    start_times["features"] = time.time()
    if not run_step("features", run_feature_generation, state_file):
        return False

    # Step 6: Model Training & Baseline (T022‑T031)
    start_times["training"] = time.time()
    if not run_step("training", run_model_training, state_file):
        return False

    # Step 7: Visualization (T032‑T040)
    start_times["visualization"] = time.time()
    if not run_step("visualization", run_visualization, state_file):
        return False

    # Step 8: Compliance Check (Optional)
    if args.compliance:
        run_compliance_check(state_file)

    log_info(logger, "Pipeline completed successfully!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Alloy Phase Diagram Prediction Pipeline")
    parser.add_argument("--compliance", action="store_true", help="Run compliance check at end")
    args = parser.parse_args()

    try:
        success = run_pipeline(args)
        sys.exit(0 if success else 1)
    except Exception as e:
        log_error(logger, f"Pipeline execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
