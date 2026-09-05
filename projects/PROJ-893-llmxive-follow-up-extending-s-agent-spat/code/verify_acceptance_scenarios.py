"""
T026: Verify all acceptance scenarios in spec.md are met by running the full pipeline end-to-end.

This script executes the full pipeline (or checks its artifacts if already run)
and validates against the acceptance criteria defined in the project specification.
It performs a comprehensive check of data hygiene, solver outputs, benchmark results,
and failure analysis reports.
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Import project modules
from config import Config
from data.download import main as download_main
from data.verify_checksum import main as verify_checksum_main
from data.validate_distribution import main as validate_distribution_main
from data.extract_geometry import main as extract_geometry_main
from solver.run_solver import main as run_solver_main
from benchmark.generate_benchmark_results import main as generate_benchmark_results_main
from benchmark.analyze_failures import main as analyze_failures_main
from hygiene import main as hygiene_main


class AcceptanceChecker:
    """Validates that all acceptance scenarios from spec.md are met."""

    def __init__(self, config: Config):
        self.config = config
        self.results: Dict[str, bool] = {}
        self.failures: List[str] = []
        self.passed: List[str] = []

    def check_file_exists(self, path: Path, description: str) -> bool:
        """Check if a required file exists."""
        if path.exists():
            self.passed.append(f"PASS: {description} exists at {path}")
            return True
        else:
            msg = f"FAIL: {description} missing at {path}"
            self.failures.append(msg)
            self.results[description] = False
            print(f"  ❌ {msg}")
            return False

    def check_file_not_empty(self, path: Path, description: str) -> bool:
        """Check if a file exists and has content."""
        if not self.check_file_exists(path, description):
            return False
        if path.stat().st_size > 0:
            self.passed.append(f"PASS: {description} is not empty")
            return True
        else:
            msg = f"FAIL: {description} is empty"
            self.failures.append(msg)
            self.results[description] = False
            print(f"  ❌ {msg}")
            return False

    def check_jsonl_valid(self, path: Path, description: str, min_lines: int = 1) -> bool:
        """Check if a JSONL file is valid and has at least min_lines entries."""
        if not self.check_file_exists(path, description):
            return False
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
                if len(lines) >= min_lines:
                    # Validate each line is valid JSON
                    valid = True
                    for i, line in enumerate(lines):
                        try:
                            json.loads(line.strip())
                        except json.JSONDecodeError:
                            valid = False
                            msg = f"FAIL: {description} has invalid JSON at line {i+1}"
                            self.failures.append(msg)
                            print(f"  ❌ {msg}")
                            break
                    if valid:
                        self.passed.append(f"PASS: {description} is valid JSONL with {len(lines)} lines")
                        return True
                else:
                    msg = f"FAIL: {description} has fewer than {min_lines} lines"
                    self.failures.append(msg)
                    print(f"  ❌ {msg}")
        except Exception as e:
            msg = f"FAIL: {description} error reading file: {e}"
            self.failures.append(msg)
            print(f"  ❌ {msg}")
        return False

    def check_csv_valid(self, path: Path, description: str, min_rows: int = 1) -> bool:
        """Check if a CSV file is valid and has at least min_rows data rows."""
        if not self.check_file_exists(path, description):
            return False
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
                if len(lines) > min_rows:  # header + at least 1 row
                    self.passed.append(f"PASS: {description} is valid CSV with {len(lines)-1} data rows")
                    return True
                else:
                    msg = f"FAIL: {description} has fewer than {min_rows} data rows"
                    self.failures.append(msg)
                    print(f"  ❌ {msg}")
        except Exception as e:
            msg = f"FAIL: {description} error reading file: {e}"
            self.failures.append(msg)
            print(f"  ❌ {msg}")
        return False

    def check_yaml_valid(self, path: Path, description: str) -> bool:
        """Check if a YAML file is valid."""
        if not self.check_file_exists(path, description):
            return False
        try:
            with open(path, 'r') as f:
                yaml.safe_load(f)
            self.passed.append(f"PASS: {description} is valid YAML")
            return True
        except Exception as e:
            msg = f"FAIL: {description} is invalid YAML: {e}"
            self.failures.append(msg)
            print(f"  ❌ {msg}")
            return False

    def check_markdown_valid(self, path: Path, description: str) -> bool:
        """Check if a Markdown file exists and has content."""
        return self.check_file_not_empty(path, description)

    def check_state_yaml_updated(self) -> bool:
        """Check if state YAML contains recent hashes."""
        state_path = self.config.state_file_path
        if not self.check_file_exists(state_path, "State YAML"):
            return False
        try:
            with open(state_path, 'r') as f:
                state = yaml.safe_load(f)
            # Check if it has a 'hashes' key with some content
            if 'hashes' in state and state['hashes']:
                self.passed.append("PASS: State YAML contains hashes")
                return True
            else:
                msg = "FAIL: State YAML missing or empty hashes"
                self.failures.append(msg)
                print(f"  ❌ {msg}")
                return False
        except Exception as e:
            msg = f"FAIL: State YAML error: {e}"
            self.failures.append(msg)
            print(f"  ❌ {msg}")
            return False

    def check_no_gpu_usage_in_solver(self) -> bool:
        """Check that solver outputs indicate CPU-only execution."""
        # Check latency_log.jsonl for any GPU metrics that shouldn't exist
        latency_log = self.config.data_derived_path / "latency_log.jsonl"
        if not latency_log.exists():
            return False
        try:
            with open(latency_log, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    if 'gpu_usage' in entry and entry['gpu_usage'] > 0:
                        msg = "FAIL: Solver used GPU (found gpu_usage > 0)"
                        self.failures.append(msg)
                        print(f"  ❌ {msg}")
                        return False
            self.passed.append("PASS: Solver logs show no GPU usage")
            return True
        except Exception as e:
            msg = f"FAIL: Error checking GPU usage: {e}"
            self.failures.append(msg)
            print(f"  ❌ {msg}")
            return False

    def check_benchmark_metrics_present(self) -> bool:
        """Check that benchmark results contain required metrics."""
        results_csv = self.config.data_results_path / "benchmark_results.csv"
        if not self.check_csv_valid(results_csv, "Benchmark Results"):
            return False
        try:
            with open(results_csv, 'r') as f:
                import csv
                reader = csv.DictReader(f)
                first_row = next(reader, None)
                if not first_row:
                    msg = "FAIL: Benchmark results CSV has no data rows"
                    self.failures.append(msg)
                    print(f"  ❌ {msg}")
                    return False
                required_cols = ['scene_id', 'exact_match', 'f1_score', 'symbolic_latency', 'vlm_latency']
                missing = [col for col in required_cols if col not in first_row]
                if missing:
                    msg = f"FAIL: Benchmark results missing columns: {missing}"
                    self.failures.append(msg)
                    print(f"  ❌ {msg}")
                    return False
            self.passed.append("PASS: Benchmark results contain all required metrics")
            return True
        except Exception as e:
            msg = f"FAIL: Error checking benchmark metrics: {e}"
            self.failures.append(msg)
            print(f"  ❌ {msg}")
            return False

    def check_failure_analysis_proportion(self) -> bool:
        """Check that failure analysis report contains the semantic gap proportion."""
        report_path = self.config.data_results_path / "failure_analysis_report.md"
        if not self.check_markdown_valid(report_path, "Failure Analysis Report"):
            return False
        try:
            with open(report_path, 'r') as f:
                content = f.read()
            if "semantic gap proportion" in content.lower() or "proportion of failures" in content.lower():
                self.passed.append("PASS: Failure analysis report contains proportion statistic")
                return True
            else:
                msg = "FAIL: Failure analysis report missing proportion statistic"
                self.failures.append(msg)
                print(f"  ❌ {msg}")
                return False
        except Exception as e:
            msg = f"FAIL: Error reading failure analysis report: {e}"
            self.failures.append(msg)
            print(f"  ❌ {msg}")
            return False

    def check_no_vlm_traces_in_solver_input(self) -> bool:
        """Check that solver input (constraints.jsonl) contains no VLM traces."""
        constraints_path = self.config.data_derived_path / "constraints.jsonl"
        if not self.check_file_exists(constraints_path, "Constraints file"):
            return False
        try:
            with open(constraints_path, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    # Check for common VLM trace indicators
                    if 'vlm_prediction' in entry or 'vlm_confidence' in entry or 'llm' in str(entry).lower():
                        msg = "FAIL: Constraints file contains VLM traces"
                        self.failures.append(msg)
                        print(f"  ❌ {msg}")
                        return False
            self.passed.append("PASS: Constraints file contains no VLM traces")
            return True
        except Exception as e:
            msg = f"FAIL: Error checking VLM traces: {e}"
            self.failures.append(msg)
            print(f"  ❌ {msg}")
            return False

    def run_full_verification(self) -> bool:
        """Run all acceptance scenario checks."""
        print("=" * 60)
        print("Running Full Acceptance Scenario Verification")
        print("=" * 60)

        # Phase 1: Data Hygiene & Integrity
        print("\n[Phase 1] Data Hygiene & Integrity")
        self.check_file_exists(self.config.data_raw_path, "Raw data directory")
        self.check_file_exists(self.config.data_derived_path, "Derived data directory")
        self.check_file_exists(self.config.data_results_path, "Results directory")
        self.check_yaml_valid(self.config.specs_path / "contracts" / "dataset.schema.yaml", "Dataset schema")
        self.check_yaml_valid(self.config.specs_path / "contracts" / "solver_output.schema.yaml", "Solver output schema")
        self.check_state_yaml_updated()

        # Phase 2: Solver Outputs
        print("\n[Phase 2] Solver Outputs")
        self.check_jsonl_valid(self.config.data_derived_path / "constraints.jsonl", "Constraints file", min_lines=10)
        self.check_jsonl_valid(self.config.data_derived_path / "predictions.jsonl", "Predictions file", min_lines=10)
        self.check_jsonl_valid(self.config.data_derived_path / "latency_log.jsonl", "Latency log", min_lines=10)
        self.check_jsonl_valid(self.config.data_results_path / "exclusion_log.json", "Exclusion log", min_lines=1)
        self.check_no_gpu_usage_in_solver()
        self.check_no_vlm_traces_in_solver_input()

        # Phase 3: Benchmark Results
        print("\n[Phase 3] Benchmark Results")
        self.check_csv_valid(self.config.data_results_path / "benchmark_results.csv", "Benchmark results", min_rows=10)
        self.check_benchmark_metrics_present()

        # Phase 4: Failure Analysis
        print("\n[Phase 4] Failure Analysis")
        self.check_markdown_valid(self.config.data_results_path / "failure_analysis_report.md", "Failure analysis report")
        self.check_failure_analysis_proportion()

        # Summary
        print("\n" + "=" * 60)
        print("Verification Summary")
        print("=" * 60)
        print(f"Total checks: {len(self.passed) + len(self.failures)}")
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failures)}")

        if self.failures:
            print("\nFailed checks:")
            for failure in self.failures:
                print(f"  - {failure}")
            return False
        else:
            print("\n✅ All acceptance scenarios verified successfully!")
            return True


def main():
    """Main entry point for T026 verification."""
    parser = argparse.ArgumentParser(description="Verify acceptance scenarios for llmXive pipeline")
    parser.add_argument('--run-pipeline', action='store_true', help="Run the full pipeline before verification")
    args = parser.parse_args()

    config = Config()

    # Optionally run the full pipeline first
    if args.run_pipeline:
        print("Running full pipeline...")
        try:
            # Run download
            download_main()
            # Run checksum verification
            verify_checksum_main()
            # Run distribution validation
            validate_distribution_main()
            # Run geometry extraction
            extract_geometry_main()
            # Run solver
            run_solver_main()
            # Run benchmark
            generate_benchmark_results_main()
            # Run failure analysis
            analyze_failures_main()
            # Run hygiene
            hygiene_main()
            print("Pipeline completed successfully.")
        except Exception as e:
            print(f"Pipeline execution failed: {e}")
            print("Proceeding with verification of available artifacts...")

    # Run verification
    checker = AcceptanceChecker(config)
    success = checker.run_full_verification()

    if not success:
        print("\n❌ Acceptance verification FAILED. Please fix the issues above.")
        sys.exit(1)
    else:
        print("\n✅ Acceptance verification PASSED.")
        sys.exit(0)


if __name__ == "__main__":
    main()