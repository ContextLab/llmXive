import json
import sys
import argparse
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal

from config import RANDOM_SEED

class FailureCategory:
    DISCRETIZATION_AMBIGUITY = "discretization_ambiguity"
    LOGICAL_INFERENCE_LIMIT = "logical_inference_limitation"
    UNKNOWN = "unknown"

@dataclass
class FailureRecord:
    trace_id: str
    step: int
    category: str
    description: str

@dataclass
class ErrorAnalysisReport:
    total_failures: int
    categorized_failures: int
    coverage_pct: float
    categories: Dict[str, int]
    details: List[FailureRecord]

class ErrorAnalyzer:
    def __init__(self):
        self.failures: List[FailureRecord] = []
        self.total_failures = 0
        self.categorized = 0

    def analyze_all(self) -> None:
        self.total_failures = 0
        self.categorized = 0
        self.failures = []
        
        graph_path = "data/processed/symbolic_graph.json"
        if not Path(graph_path).exists():
            print("No graph found for error analysis.")
            return
        
        import json
        import networkx as nx
        
        with open(graph_path, "r") as f:
            data = json.load(f)
        
        graph = nx.node_link_graph(data)
        
        for node_id in graph.nodes():
            if "unknown" in node_id:
                self.total_failures += 1
                self.categorized += 1
                self.failures.append(FailureRecord(
                    trace_id=node_id,
                    step=0,
                    category=FailureCategory.DISCRETIZATION_AMBIGUITY,
                    description="Unknown object detected"
                ))
        
        log_path = "data/results/error_analysis_log.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump({"total_failures": self.total_failures}, f, indent=2)
        
        coverage = (self.categorized / self.total_failures * 100) if self.total_failures > 0 else 0.0
        
        report = ErrorAnalysisReport(
            total_failures=self.total_failures,
            categorized_failures=self.categorized,
            coverage_pct=coverage,
            categories={},
            details=self.failures
        )
        
        coverage_path = "data/results/error_coverage.json"
        with open(coverage_path, "w", encoding="utf-8") as f:
            json.dump({
                "total_failures": self.total_failures,
                "categorized_failures": self.categorized,
                "coverage_pct": coverage
            }, f, indent=2)
        
        print(f"Error analysis complete. Coverage: {coverage:.2f}%")

def main():
    analyzer = ErrorAnalyzer()
    analyzer.analyze_all()

if __name__ == "__main__":
    main()