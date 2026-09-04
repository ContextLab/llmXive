"""
Error Analysis Module for llmXive Symbolic Memory Project.

Provides functionality to categorize failures, calculate coverage metrics,
and generate reports on error analysis effectiveness.
"""
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from metrics import MetricsLogger

class FailureCategory(Enum):
    """Enumeration of possible failure categories for symbolic system errors."""
    DISCRETIZATION_AMBIGUITY = "discretization_ambiguity"
    LOGICAL_INFERENCE_LIMITATIONS = "logical_inference_limitations"
    UNKNOWN = "unknown"

@dataclass
class FailureRecord:
    """Record of a single failure event."""
    trace_id: str
    error_type: str
    category: Optional[str] = None
    details: Optional[str] = None
    categorized: bool = False

@dataclass
class ErrorAnalysisReport:
    """Report containing error analysis statistics."""
    total_failures: int = 0
    categorized_failures: int = 0
    uncategorized_failures: int = 0
    coverage_percentage: float = 0.0
    category_counts: Dict[str, int] = field(default_factory=dict)
    uncategorized_samples: List[Dict[str, Any]] = field(default_factory=list)

class ErrorAnalyzer:
    """
    Analyzes failure records to categorize errors and compute coverage metrics.
    
    This class extends the functionality of T030 and T030a by calculating
    the percentage of failures that were successfully categorized.
    """
    def __init__(self, logger: Optional[MetricsLogger] = None):
        self.failures: List[FailureRecord] = []
        self.category_counts: Dict[str, int] = {
            FailureCategory.DISCRETIZATION_AMBIGUITY.value: 0,
            FailureCategory.LOGICAL_INFERENCE_LIMITATIONS.value: 0,
            FailureCategory.UNKNOWN.value: 0
        }
        self.logger = logger

    def add_failure(self, record: FailureRecord) -> None:
        """Add a failure record to the analysis pool."""
        self.failures.append(record)

    def categorize_failure(self, record: FailureRecord) -> FailureCategory:
        """
        Categorize a failure based on its error type and details.
        
        Args:
            record: The failure record to categorize.
            
        Returns:
            The determined FailureCategory.
        """
        error_type = record.error_type.lower()
        details = (record.details or "").lower()
        
        # Categorization logic based on T030 implementation
        if any(term in error_type or term in details for term in ["ambiguous", "token", "mapping", "discretize"]):
            category = FailureCategory.DISCRETIZATION_AMBIGUITY
        elif any(term in error_type or term in details for term in ["logic", "inference", "contradict", "graph", "query"]):
            category = FailureCategory.LOGICAL_INFERENCE_LIMITATIONS
        else:
            category = FailureCategory.UNKNOWN
        
        record.category = category.value
        record.categorized = (category != FailureCategory.UNKNOWN)
        
        if record.categorized:
            self.category_counts[category.value] = self.category_counts.get(category.value, 0) + 1
        
        return category

    def analyze_all(self) -> None:
        """Categorize all failure records in the pool."""
        for record in self.failures:
            if not record.categorized:
                self.categorize_failure(record)

    def calculate_coverage(self) -> float:
        """
        Calculate the error analysis coverage percentage.
        
        Coverage = (categorized_failures / total_failures) * 100
        
        Returns:
            Coverage percentage as a float.
        """
        total = len(self.failures)
        if total == 0:
            return 0.0
        
        categorized = sum(1 for r in self.failures if r.categorized)
        return (categorized / total) * 100

    def generate_report(self) -> ErrorAnalysisReport:
        """
        Generate the final error analysis report.
        
        Returns:
            An ErrorAnalysisReport object containing all statistics.
        """
        total_failures = len(self.failures)
        categorized_failures = sum(1 for r in self.failures if r.categorized)
        uncategorized_failures = total_failures - categorized_failures
        coverage = self.calculate_coverage()
        
        # Collect uncategorized samples
        uncategorized_samples = [
            asdict(r) for r in self.failures if not r.categorized
        ]
        
        # Filter out the UNKNOWN category from the report counts if desired, 
        # or keep it to show "unknown" categorization. 
        # Here we keep the counts as they are.
        
        return ErrorAnalysisReport(
            total_failures=total_failures,
            categorized_failures=categorized_failures,
            uncategorized_failures=uncategorized_failures,
            coverage_percentage=coverage,
            category_counts=self.category_counts,
            uncategorized_samples=uncategorized_samples
        )

def main():
    """
    Main entry point for running error analysis and generating the coverage report.
    
    This function:
    1. Loads failure data from data/results/failures.json (generated by T030/T030a)
    2. Categorizes failures
    3. Calculates coverage
    4. Writes report to data/results/error_coverage.json
    """
    # Paths
    failures_path = Path("data/results/failures.json")
    output_path = Path("data/results/error_coverage.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize logger
    logger = MetricsLogger()
    analyzer = ErrorAnalyzer(logger)
    
    # Load failures
    if not failures_path.exists():
        # If no failures file exists, create an empty report
        logger.log_memory(0.0) # Dummy log
        empty_report = ErrorAnalysisReport()
        with open(output_path, "w") as f:
            json.dump(asdict(empty_report), f, indent=2)
        print(f"No failures found at {failures_path}. Wrote empty report.")
        return
    
    with open(failures_path, "r") as f:
        failures_data = json.load(f)
    
    # Convert JSON data to FailureRecord objects
    for item in failures_data:
        record = FailureRecord(
            trace_id=item.get("trace_id", "unknown"),
            error_type=item.get("error_type", "unknown"),
            details=item.get("details"),
            categorized=item.get("categorized", False)
        )
        analyzer.add_failure(record)
    
    # Analyze and categorize
    analyzer.analyze_all()
    
    # Generate report
    report = analyzer.generate_report()
    
    # Save report
    with open(output_path, "w") as f:
        json.dump(asdict(report), f, indent=2)
    
    print(f"Error analysis complete.")
    print(f"Total failures: {report.total_failures}")
    print(f"Categorized: {report.categorized_failures}")
    print(f"Uncategorized: {report.uncategorized_failures}")
    print(f"Coverage: {report.coverage_percentage:.2f}%")
    print(f"Report saved to {output_path}")

if __name__ == "__main__":
    main()
