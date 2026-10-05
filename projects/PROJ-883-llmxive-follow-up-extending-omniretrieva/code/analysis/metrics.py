"""
Metrics collection and persistence module.

Implements T015 and T021 data persistence requirements.
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import csv

@dataclass
class ExecutionMetric:
    """Represents a single execution metric record."""
    query_id: str
    source_type: str
    complexity_level: int
    ground_truth_plan: Optional[str]
    executed_plan: Optional[str]
    latency_ms: float
    success: bool
    timeout: bool
    timestamp: str = ""

    def __init__(self, query_id, source_type, complexity_level, ground_truth_plan, 
                 executed_plan, latency_ms, success, timeout):
        self.query_id = query_id
        self.source_type = source_type
        self.complexity_level = complexity_level
        self.ground_truth_plan = ground_truth_plan
        self.executed_plan = executed_plan
        self.latency_ms = latency_ms
        self.success = success
        self.timeout = timeout
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)

def record_execution_metric(
    query_id: str,
    source_type: str,
    complexity_level: int,
    ground_truth_plan: Optional[str],
    executed_plan: Optional[str],
    latency_ms: float,
    success: bool,
    timeout: bool
) -> ExecutionMetric:
    """Record a single execution metric."""
    return ExecutionMetric(
        query_id=query_id,
        source_type=source_type,
        complexity_level=complexity_level,
        ground_truth_plan=ground_truth_plan,
        executed_plan=executed_plan,
        latency_ms=latency_ms,
        success=success,
        timeout=timeout
    )

def calculate_translation_error_rate(metrics: List[ExecutionMetric]) -> float:
    """Calculate the binary translation error rate (0=match, 1=mismatch)."""
    if not metrics:
        return 0.0
    
    errors = 0
    for m in metrics:
        if m.ground_truth_plan is None or m.executed_plan is None:
            continue
        if m.ground_truth_plan != m.executed_plan:
            errors += 1
    
    return errors / len(metrics)

def aggregate_metrics_by_complexity(metrics: List[ExecutionMetric]) -> Dict[int, Dict[str, Any]]:
    """Aggregate metrics by complexity level."""
    aggregates = {}
    for m in metrics:
        lvl = m.complexity_level
        if lvl not in aggregates:
            aggregates[lvl] = {
                "count": 0,
                "total_latency": 0.0,
                "successes": 0,
                "timeouts": 0
            }
        aggregates[lvl]["count"] += 1
        aggregates[lvl]["total_latency"] += m.latency_ms
        if m.success:
            aggregates[lvl]["successes"] += 1
        if m.timeout:
            aggregates[lvl]["timeouts"] += 1
    
    # Calculate averages
    for lvl, agg in aggregates.items():
        if agg["count"] > 0:
            agg["avg_latency"] = agg["total_latency"] / agg["count"]
        else:
            agg["avg_latency"] = 0.0
    return aggregates

def save_metrics_to_file(metrics: List[ExecutionMetric], filepath: str) -> None:
    """Save metrics to a CSV file (T021 requirement)."""
    if not metrics:
        return

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        # Header
        header = [
            "query_id", "source_type", "complexity_level", 
            "ground_truth_plan", "executed_plan", "latency_ms", 
            "success", "timeout", "timestamp"
        ]
        writer.writerow(header)

        for m in metrics:
            row = [
                m.query_id,
                m.source_type,
                m.complexity_level,
                m.ground_truth_plan if m.ground_truth_plan else "",
                m.executed_plan if m.executed_plan else "",
                m.latency_ms,
                m.success,
                m.timeout,
                m.timestamp
            ]
            writer.writerow(row)

def load_metrics_from_file(filepath: str) -> List[ExecutionMetric]:
    """Load metrics from a CSV file."""
    metrics = []
    if not os.path.exists(filepath):
        return metrics

    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            m = ExecutionMetric(
                query_id=row["query_id"],
                source_type=row["source_type"],
                complexity_level=int(row["complexity_level"]),
                ground_truth_plan=row["ground_truth_plan"] if row["ground_truth_plan"] else None,
                executed_plan=row["executed_plan"] if row["executed_plan"] else None,
                latency_ms=float(row["latency_ms"]),
                success=row["success"] == "True",
                timeout=row["timeout"] == "True"
            )
            metrics.append(m)
    return metrics
