"""
Script to execute T030: Latency Meter analysis.
Runs the latency analysis against the generated artifacts.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.latency_meter import main as latency_main

if __name__ == "__main__":
    # Default paths based on project structure
    test_data = project_root / "data" / "processed" / "split_test.parquet"
    predictor = project_root / "data" / "models" / "gap_predictor.pkl"
    baseline_metrics = project_root / "data" / "processed" / "baseline_metrics.json"
    output = project_root / "data" / "processed" / "latency_metrics.json"

    # Check prerequisites
    if not test_data.exists():
        print(f"Error: Test data not found at {test_data}")
        print("Please run T021A (prepare_data_split.py) first.")
        sys.exit(1)
    if not predictor.exists():
        print(f"Error: Predictor model not found at {predictor}")
        print("Please run T021 (train_predictor.py) first.")
        sys.exit(1)
    if not baseline_metrics.exists():
        print(f"Error: Baseline metrics not found at {baseline_metrics}")
        print("Please run T027 (run_baseline_sync.py) first.")
        sys.exit(1)

    # Run the analysis
    sys.argv = [
        "run_latency_analysis.py",
        "--test-data", str(test_data),
        "--predictor", str(predictor),
        "--baseline-metrics", str(baseline_metrics),
        "--output", str(output)
    ]
    latency_main()
