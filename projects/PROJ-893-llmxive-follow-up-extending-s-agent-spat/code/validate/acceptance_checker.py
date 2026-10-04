"""
Acceptance Checker for llmXive Spatial Reasoning Pipeline.
Verifies all acceptance scenarios in spec.md (US-1, US-2, US-3) are met.
Outputs data/results/acceptance_checklist.md with pass/fail status.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

class AcceptanceChecker:
    """Verifies acceptance scenarios against pipeline outputs."""

    def __init__(self):
        self.results_dir = Path(Config.DATA_RESULTS)
        self.derived_dir = Path(Config.DATA_DERIVED)
        self.raw_dir = Path(Config.DATA_RAW)
        self.checklist = {
            "US-1": {"status": "FAIL", "details": []},
            "US-2": {"status": "FAIL", "details": []},
            "US-3": {"status": "FAIL", "details": []},
            "SC-005": {"status": "FAIL", "details": [], "metric_value": None}
        }
        self.vlm_baseline_accuracy = None
        self.symbolic_exact_match = None

    def check_file_exists(self, file_path: Path, description: str) -> bool:
        """Check if a required file exists."""
        if file_path.exists():
            self._log_pass(description, f"File exists: {file_path}")
            return True
        else:
            self._log_fail(description, f"File missing: {file_path}")
            return False

    def _log_pass(self, scenario: str, message: str):
        """Log a passing check."""
        if scenario in self.checklist:
            if self.checklist[scenario]["status"] != "PASS":
                self.checklist[scenario]["status"] = "PASS"
                self.checklist[scenario]["details"] = []
            self.checklist[scenario]["details"].append(f"PASS: {message}")

    def _log_fail(self, scenario: str, message: str):
        """Log a failing check."""
        if scenario in self.checklist:
            self.checklist[scenario]["status"] = "FAIL"
            self.checklist[scenario]["details"].append(f"FAIL: {message}")

    def verify_us1_solver_execution(self) -> bool:
        """
        Verify US-1: Symbolic solver execution.
        Checks for predictions.jsonl, latency_log.jsonl, solver_failures.json.
        """
        passed = True
        
        # Check for predictions
        predictions_file = self.derived_dir / "predictions.jsonl"
        if not self.check_file_exists(predictions_file, "US-1: predictions.jsonl"):
            passed = False
        else:
            # Validate content
            try:
                with open(predictions_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) == 0:
                        self._log_fail("US-1", "predictions.jsonl is empty")
                        passed = False
                    else:
                        # Check schema
                        sample = json.loads(lines[0])
                        required_keys = {"scene_id", "prediction", "status"}
                        if not required_keys.issubset(sample.keys()):
                            self._log_fail("US-1", f"predictions.jsonl missing keys. Found: {sample.keys()}")
                            passed = False
                        else:
                            self._log_pass("US-1", f"predictions.jsonl valid with {len(lines)} entries")
            except Exception as e:
                self._log_fail("US-1", f"Error reading predictions.jsonl: {str(e)}")
                passed = False

        # Check for latency log
        latency_file = self.derived_dir / "latency_log.jsonl"
        if not self.check_file_exists(latency_file, "US-1: latency_log.jsonl"):
            passed = False
        else:
            try:
                with open(latency_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) == 0:
                        self._log_fail("US-1", "latency_log.jsonl is empty")
                        passed = False
                    else:
                        sample = json.loads(lines[0])
                        if "latency_ms" not in sample:
                            self._log_fail("US-1", "latency_log.jsonl missing latency_ms")
                            passed = False
                        else:
                            self._log_pass("US-1", f"latency_log.jsonl valid with {len(lines)} entries")
            except Exception as e:
                self._log_fail("US-1", f"Error reading latency_log.jsonl: {str(e)}")
                passed = False

        # Check for solver failures
        failures_file = self.derived_dir / "solver_failures.json"
        if not self.check_file_exists(failures_file, "US-1: solver_failures.json"):
            passed = False
        else:
            try:
                with open(failures_file, 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        self._log_fail("US-1", "solver_failures.json is not a list")
                        passed = False
                    else:
                        self._log_pass("US-1", f"solver_failures.json valid with {len(data)} entries")
            except Exception as e:
                self._log_fail("US-1", f"Error reading solver_failures.json: {str(e)}")
                passed = False

        return passed

    def verify_us2_benchmark_metrics(self) -> bool:
        """
        Verify US-2: Comparative benchmarking.
        Checks for benchmark_results.csv, sensitivity_analysis.csv, p_values.jsonl.
        """
        passed = True

        # Check for base benchmark results
        base_results = self.results_dir / "benchmark_results_base.csv"
        final_results = self.results_dir / "benchmark_results.csv"
        
        # Prefer final, fall back to base for existence check if final missing
        target_results = final_results if final_results.exists() else base_results
        
        if not self.check_file_exists(target_results, "US-2: benchmark results CSV"):
            passed = False
        else:
            try:
                with open(target_results, 'r') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    required_headers = {"scene_id", "symbolic_pred", "vlm_pred", "ground_truth", "exact_match", "f1", "latency_ms"}
                    if not required_headers.issubset(set(headers)):
                        self._log_fail("US-2", f"benchmark results missing headers. Found: {headers}")
                        passed = False
                    else:
                        rows = list(reader)
                        self._log_pass("US-2", f"benchmark results valid with {len(rows)} entries")
                        
                        # Calculate metrics for SC-005
                        if len(rows) > 0:
                            total = len(rows)
                            exact_matches = sum(1 for r in rows if r.get('exact_match', 'False').lower() == 'true')
                            self.symbolic_exact_match = exact_matches / total if total > 0 else 0.0
                            self._log_pass("US-2", f"Symbolic Exact Match: {self.symbolic_exact_match:.2%}")
            except Exception as e:
                self._log_fail("US-2", f"Error reading benchmark results: {str(e)}")
                passed = False

        # Check for sensitivity analysis
        sensitivity_file = self.results_dir / "sensitivity_analysis.csv"
        if not self.check_file_exists(sensitivity_file, "US-2: sensitivity_analysis.csv"):
            passed = False
        else:
            try:
                with open(sensitivity_file, 'r') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    required_headers = {"threshold", "success_rate", "false_positive_rate"}
                    if not required_headers.issubset(set(headers)):
                        self._log_fail("US-2", f"sensitivity_analysis.csv missing headers. Found: {headers}")
                        passed = False
                    else:
                        rows = list(reader)
                        self._log_pass("US-2", f"sensitivity_analysis.csv valid with {len(rows)} entries")
            except Exception as e:
                self._log_fail("US-2", f"Error reading sensitivity_analysis.csv: {str(e)}")
                passed = False

        # Check for p_values if final results exist
        if final_results.exists():
            p_values_file = self.results_dir / "p_values.jsonl"
            if not self.check_file_exists(p_values_file, "US-2: p_values.jsonl"):
                passed = False
            else:
                try:
                    with open(p_values_file, 'r') as f:
                        lines = f.readlines()
                        self._log_pass("US-2", f"p_values.jsonl valid with {len(lines)} entries")
                except Exception as e:
                    self._log_fail("US-2", f"Error reading p_values.jsonl: {str(e)}")
                    passed = False

        return passed

    def verify_us3_failure_analysis(self) -> bool:
        """
        Verify US-3: Failure case analysis.
        Checks for failure_classification.json and failure_analysis_report.md.
        """
        passed = True

        # Check for failure classification JSON
        classification_file = self.derived_dir / "failure_classification.json"
        if not self.check_file_exists(classification_file, "US-3: failure_classification.json"):
            passed = False
        else:
            try:
                with open(classification_file, 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        self._log_fail("US-3", "failure_classification.json is not a list")
                        passed = False
                    else:
                        self._log_pass("US-3", f"failure_classification.json valid with {len(data)} entries")
                        
                        # Check for semantic_gap_proportion if present in structure
                        # Some implementations might have a summary object at the end or separate
                        # We check if any item has the key or if there's a summary
                        has_proportion = any("semantic_gap_proportion" in item for item in data)
                        if has_proportion:
                            self._log_pass("US-3", "semantic_gap_proportion found in classification data")
            except Exception as e:
                self._log_fail("US-3", f"Error reading failure_classification.json: {str(e)}")
                passed = False

        # Check for failure analysis report
        report_file = self.results_dir / "failure_analysis_report.md"
        if not self.check_file_exists(report_file, "US-3: failure_analysis_report.md"):
            passed = False
        else:
            try:
                with open(report_file, 'r') as f:
                    content = f.read()
                    if "Geometric Ambiguity" not in content or "Semantic Gap" not in content:
                        self._log_fail("US-3", "failure_analysis_report.md missing required sections")
                        passed = False
                    else:
                        self._log_pass("US-3", "failure_analysis_report.md contains required sections")
            except Exception as e:
                self._log_fail("US-3", f"Error reading failure_analysis_report.md: {str(e)}")
                passed = False

        return passed

    def verify_sc005_exact_match_threshold(self) -> bool:
        """
        Verify SC-005: Exact Match score >= 85% of VLM baseline.
        Requires benchmark results to be present and metrics calculated.
        """
        # If we haven't calculated metrics yet, try to load them
        if self.symbolic_exact_match is None:
            final_results = self.results_dir / "benchmark_results.csv"
            if final_results.exists():
                try:
                    with open(final_results, 'r') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        total = len(rows)
                        exact_matches = sum(1 for r in rows if r.get('exact_match', 'False').lower() == 'true')
                        self.symbolic_exact_match = exact_matches / total if total > 0 else 0.0
                except Exception:
                    pass

        # If we still don't have the metric, we can't verify
        if self.symbolic_exact_match is None:
            self._log_fail("SC-005", "Cannot verify: Symbolic Exact Match not calculated (missing benchmark results)")
            return False

        # We need VLM baseline accuracy. If not calculated, we assume VLM is 100% for the check
        # or we try to load it from the benchmark results if available
        if self.vlm_baseline_accuracy is None:
            # Try to calculate from benchmark results if vlm_pred and ground_truth are present
            final_results = self.results_dir / "benchmark_results.csv"
            if final_results.exists():
                try:
                    with open(final_results, 'r') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        total = len(rows)
                        vlm_correct = sum(1 for r in rows if r.get('vlm_pred') == r.get('ground_truth'))
                        self.vlm_baseline_accuracy = vlm_correct / total if total > 0 else 1.0
                except Exception:
                    self.vlm_baseline_accuracy = 1.0 # Default assumption

        threshold = 0.85 * self.vlm_baseline_accuracy
        passed = self.symbolic_exact_match >= threshold

        if passed:
            self._log_pass("SC-005", f"Exact Match {self.symbolic_exact_match:.2%} >= {threshold:.2%} (85% of VLM {self.vlm_baseline_accuracy:.2%})")
            self.checklist["SC-005"]["metric_value"] = self.symbolic_exact_match
        else:
            self._log_fail("SC-005", f"Exact Match {self.symbolic_exact_match:.2%} < {threshold:.2%} (85% of VLM {self.vlm_baseline_accuracy:.2%})")

        return passed

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all acceptance checks."""
        self.verify_us1_solver_execution()
        self.verify_us2_benchmark_metrics()
        self.verify_us3_failure_analysis()
        self.verify_sc005_exact_match_threshold()
        return self.checklist

    def generate_checklist_md(self, output_path: Path):
        """Generate the acceptance checklist markdown file."""
        lines = [
            "# Acceptance Checklist",
            "",
            "This document verifies that all acceptance scenarios defined in `spec.md` are met.",
            "",
            "## Verification Summary",
            ""
        ]

        for scenario, data in self.checklist.items():
            status_icon = "✅" if data["status"] == "PASS" else "❌"
            lines.append(f"### {scenario} {status_icon}")
            lines.append("")
            for detail in data["details"]:
                lines.append(f"- {detail}")
            if "metric_value" in data and data["metric_value"] is not None:
                lines.append(f"- **Metric Value**: {data['metric_value']:.4f}")
            lines.append("")

        lines.append("---")
        lines.append(f"*Generated on: {__import__('datetime').datetime.now().isoformat()}*")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("\n".join(lines))

    def main(self):
        """Main entry point."""
        parser = argparse.ArgumentParser(description="Verify acceptance scenarios for llmXive pipeline.")
        parser.add_argument("--output", type=str, default=None, help="Output path for checklist markdown")
        args = parser.parse_args()

        output_path = Path(args.output) if args.output else self.results_dir / "acceptance_checklist.md"

        checker = AcceptanceChecker()
        results = checker.run_all_checks()
        checker.generate_checklist_md(output_path)

        print(f"Acceptance checklist generated at: {output_path}")
        
        # Print summary
        all_passed = all(data["status"] == "PASS" for data in results.values())
        if all_passed:
            print("✅ All acceptance scenarios PASSED.")
            sys.exit(0)
        else:
            print("❌ Some acceptance scenarios FAILED.")
            sys.exit(1)

if __name__ == "__main__":
    main()
