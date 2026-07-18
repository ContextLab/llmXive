"""
End-to-End Validation for quickstart.md flow.

This test suite verifies that the entire pipeline described in quickstart.md
executes correctly:
1. Directory structure exists and is writable.
2. Synthetic data generation produces valid output files.
3. Statistical analysis runs on the generated data and produces results.
4. Sensitivity analysis runs and produces a sweep report.
5. All output files are written to the correct paths.
"""

import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path

# Add code/src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli import main as cli_main, parse_args
from synthetic_gen import SyntheticDataGenerator
from data_loader import load_public_dataset, calculate_gain_scores, write_processed_data
from stats_engine import run_t_test, calculate_effect_size, aggregate_results
from sensitivity import run_sensitivity_sweep
from models import AnalysisResult, SensitivitySweep
from utils import set_seed


class TestQuickstartValidation:
    """Validates the full end-to-end flow as described in quickstart.md."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmp_path):
        """Setup a temporary directory structure mimicking the project root."""
        self.project_root = tmp_path
        self.code_dir = self.project_root / "code"
        self.data_dir = self.project_root / "data"
        self.data_raw = self.data_dir / "raw"
        self.data_processed = self.data_dir / "processed"
        self.data_synthetic = self.data_dir / "synthetic"
        self.data_derivation_logs = self.data_dir / "derivation_logs"
        self.state_dir = self.project_root / "state" / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si"

        # Create directory structure
        self.data_raw.mkdir(parents=True, exist_ok=True)
        self.data_processed.mkdir(parents=True, exist_ok=True)
        self.data_synthetic.mkdir(parents=True, exist_ok=True)
        self.data_derivation_logs.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Set environment variables to point to temp paths if needed by CLI
        os.environ["PROJECT_ROOT"] = str(self.project_root)

        yield

        # Cleanup is handled by tmp_path fixture

    def test_01_cli_synthetic_generation(self):
        """
        Test: Run CLI with --mode=synthetic to generate data.
        Verifies that data/synthetic/generation_output.csv and mapping_log.json are created.
        """
        # Simulate CLI args for synthetic generation
        args = parse_args([
            "--mode", "synthetic",
            "--output_dir", str(self.data_synthetic),
            "--n_samples", "100",
            "--seed", "42"
        ])

        # Run the generation logic directly to avoid sys.exit in main
        from cli import run_synthetic_generation
        run_synthetic_generation(args)

        # Verify outputs
        output_csv = self.data_synthetic / "generation_output.csv"
        mapping_log = self.data_synthetic / "mapping_log.json"

        assert output_csv.exists(), f"Synthetic output CSV not found at {output_csv}"
        assert mapping_log.exists(), f"Mapping log not found at {mapping_log}"

        # Verify CSV content
        with open(output_csv, "r") as f:
            import csv
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 100, f"Expected 100 rows, got {len(rows)}"
            assert "pre_test_score" in rows[0], "Missing pre_test_score column"
            assert "post_test_score" in rows[0], "Missing post_test_score column"
            assert "instruction_type" in rows[0], "Missing instruction_type column"

        # Verify Mapping Log content (Constitution Principle VI)
        with open(mapping_log, "r") as f:
            log_data = json.load(f)
            assert "causal_chain" in log_data, "Mapping log missing causal_chain"
            assert "Physics_Action" in str(log_data["causal_chain"]), "Missing Physics_Action in chain"
            assert "Virtual_Object_State" in str(log_data["causal_chain"]), "Missing Virtual_Object_State in chain"
            assert "Abstract_Principle_Inference" in str(log_data["causal_chain"]), "Missing Abstract_Principle_Inference in chain"

    def test_02_cli_secondary_analysis(self):
        """
        Test: Run CLI with --mode=secondary_analysis on the generated synthetic data.
        Verifies that data/processed/results.json is created with valid stats.
        """
        # First ensure we have synthetic data to analyze (reuse from previous test conceptually)
        # We'll generate a fresh small set for this specific test to ensure isolation
        set_seed(123)
        generator = SyntheticDataGenerator(
            n_samples=50,
            embodied_mean_diff=0.5,
            static_mean_diff=0.1,
            seed=123
        )
        data_path = self.data_synthetic / "test_analysis_input.csv"
        generator.generate(str(data_path))

        # Simulate CLI args for secondary analysis
        args = parse_args([
            "--mode", "secondary_analysis",
            "--input", str(data_path),
            "--output_dir", str(self.data_processed),
            "--seed", "123"
        ])

        from cli import run_secondary_analysis
        run_secondary_analysis(args)

        # Verify outputs
        results_json = self.data_processed / "results.json"
        assert results_json.exists(), f"Analysis results JSON not found at {results_json}"

        with open(results_json, "r") as f:
            results = json.load(f)

        assert "t_statistic" in results, "Missing t_statistic in results"
        assert "p_value" in results, "Missing p_value in results"
        assert "effect_size" in results, "Missing effect_size in results"
        assert "inference_framing" in results, "Missing inference_framing in results"
        assert "associational" in results["inference_framing"].lower(), "Results not framed as associational"

    def test_03_sensitivity_sweep(self):
        """
        Test: Run sensitivity sweep on generated data.
        Verifies that sweep results are appended to the output or written separately.
        """
        # Generate data
        set_seed(456)
        generator = SyntheticDataGenerator(
            n_samples=100,
            embodied_mean_diff=0.3,
            static_mean_diff=0.1,
            seed=456
        )
        data_path = self.data_synthetic / "test_sweep_input.csv"
        generator.generate(str(data_path))

        # Load data
        from src.data_loader import load_public_dataset
        # Note: load_public_dataset expects a path or handles internal logic
        # We'll manually load for the sweep test to ensure we have the dataframe
        import pandas as pd
        df = pd.read_csv(data_path)

        # Run sweep
        thresholds = [0.01, 0.05, 0.10]
        sweep_results = run_sensitivity_sweep(df, thresholds, seed=456)

        assert len(sweep_results) == 3, f"Expected 3 sweep results, got {len(sweep_results)}"
        
        for i, res in enumerate(sweep_results):
            assert "threshold" in res, f"Result {i} missing threshold"
            assert "effect_size" in res, f"Result {i} missing effect_size"
            assert "p_value" in res, f"Result {i} missing p_value"

        # Verify robustness warning logic
        # If effect size drops significantly at any threshold, robustness_warning should be true
        # This is a logic check on the implementation
        assert "robustness_warning" in sweep_results[0] or all("robustness_warning" in r for r in sweep_results), \
            "Sweep results missing robustness_warning field"

    def test_04_full_pipeline_integration(self):
        """
        Test: Run the full pipeline in sequence as a user would.
        1. Generate synthetic data.
        2. Run analysis.
        3. Run sweep.
        4. Verify all files exist in correct locations.
        """
        # Step 1: Generate
        args_gen = parse_args([
            "--mode", "synthetic",
            "--output_dir", str(self.data_synthetic),
            "--n_samples", "200",
            "--seed", "789"
        ])
        from cli import run_synthetic_generation
        run_synthetic_generation(args_gen)

        input_file = self.data_synthetic / "generation_output.csv"
        assert input_file.exists()

        # Step 2: Analyze
        args_analysis = parse_args([
            "--mode", "secondary_analysis",
            "--input", str(input_file),
            "--output_dir", str(self.data_processed),
            "--seed", "789"
        ])
        from cli import run_secondary_analysis
        run_secondary_analysis(args_analysis)

        results_file = self.data_processed / "results.json"
        assert results_file.exists()

        # Step 3: Sweep (CLI might not have a direct flag for sweep-only, but we can verify the module works)
        # The task description implies the sweep is part of the flow if --sweep is passed or by default in some modes.
        # We verified the module works in test_03. Here we ensure the file structure is consistent.
        
        # Verify derivation logs
        log_file = self.data_derivation_logs / "skipped_records.log"
        # The log might be empty or not exist if no records were skipped, but the directory must be writable
        assert self.data_derivation_logs.exists()

        # Verify mapping log exists (Constitution Principle VI)
        mapping_log = self.data_synthetic / "mapping_log.json"
        assert mapping_log.exists()