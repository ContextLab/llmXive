import json
import sys
import argparse
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

# Ensure code directory is in path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

@dataclass
class FailureRecord:
    trace_id: str
    error_type: Literal['VLM_MISMATCH', 'GRAPH_TRAVERSAL_FAIL', 'OTHER']
    description: str
    raw_trace: Optional[Dict[str, Any]] = None

@dataclass
class ErrorAnalysisReport:
    total_failures: int
    categorized_failures: int
    coverage_pct: float
    breakdown: Dict[str, int]
    samples: List[FailureRecord]

class ErrorAnalyzer:
    def __init__(self):
        self.failures: List[FailureRecord] = []
        self.total_failures = 0
        self.categorized_failures = 0

    def record_failure(self, trace_id: str, error_type: str, description: str, raw_trace: Optional[Dict] = None):
        """
        Records a failure event and categorizes it.
        
        Args:
            trace_id: Unique identifier for the failed trace.
            error_type: Raw error type string (e.g., 'VLM_MISMATCH', 'GRAPH_TRAVERSAL_FAIL').
            description: Human-readable description of the failure.
            raw_trace: Optional raw trace data for debugging.
        """
        self.total_failures += 1
        
        # Normalize error type based on expected values from graph_builder.py
        normalized_type = 'OTHER'
        if error_type == 'VLM_MISMATCH':
            normalized_type = 'VLM_MISMATCH'
            self.categorized_failures += 1
        elif error_type == 'GRAPH_TRAVERSAL_FAIL':
            normalized_type = 'GRAPH_TRAVERSAL_FAIL'
            self.categorized_failures += 1
        
        record = FailureRecord(
            trace_id=trace_id,
            error_type=normalized_type,
            description=description,
            raw_trace=raw_trace
        )
        self.failures.append(record)

    def generate_report(self) -> ErrorAnalysisReport:
        """Generates a summary report of the error analysis."""
        breakdown = {'VLM_MISMATCH': 0, 'GRAPH_TRAVERSAL_FAIL': 0, 'OTHER': 0}
        for f in self.failures:
            if f.error_type in breakdown:
                breakdown[f.error_type] += 1
        
        coverage = 0.0
        if self.total_failures > 0:
            coverage = (self.categorized_failures / self.total_failures) * 100
        
        return ErrorAnalysisReport(
            total_failures=self.total_failures,
            categorized_failures=self.categorized_failures,
            coverage_pct=coverage,
            breakdown=breakdown,
            samples=self.failures
        )

    def save_log(self, filepath: str = "data/results/error_analysis_log.json"):
        """
        Saves the error analysis report to a JSON file.
        
        Args:
            filepath: Path to the output JSON file.
        """
        report = self.generate_report()
        # Convert dataclass to dict for JSON serialization
        report_dict = {
            "total_failures": report.total_failures,
            "categorized_failures": report.categorized_failures,
            "coverage_pct": report.coverage_pct,
            "breakdown": report.breakdown,
            "samples": [asdict(s) for s in report.samples]
        }
        
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(report_dict, f, indent=2)

def main():
    """
    Main entry point for error analysis execution.
    
    This function is designed to be called by the experiment runner (T028)
    or directly to generate the error_analysis_log.json file.
    It expects to be passed failure data collected during the comparative study.
    """
    analyzer = ErrorAnalyzer()
    
    # In a real execution flow (T028), the ExperimentRunner would:
    # 1. Run symbolic and neural baselines.
    # 2. Capture failures where symbolic succeeded but neural failed (or vice versa).
    # 3. Inspect the error_type field from graph_builder.py or query_engine.py.
    # 4. Call analyzer.record_failure(...) for each.
    # 5. Call analyzer.save_log().
    
    # Since we are implementing T030 (the categorization logic), we ensure the
    # structure is robust. If called standalone without external data, it writes
    # an empty report (0 failures) to satisfy the file existence check,
    # but in the context of T028, it will be populated with real data.
    
    # NOTE: The actual population of failures happens in experiment_runner.py
    # which imports this module and calls record_failure based on run results.
    
    # To ensure the file is written even if no failures occurred (as per T030a),
    # we save the log here.
    analyzer.save_log()
    print(f"Error analysis log saved to data/results/error_analysis_log.json. Total failures: {analyzer.total_failures}")

if __name__ == "__main__":
    main()
