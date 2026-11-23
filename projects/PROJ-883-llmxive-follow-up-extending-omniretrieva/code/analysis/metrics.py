"""Analysis metrics utilities.

Provides the ExecutionMetric dataclass and helper functions for
recording, saving, and loading execution metrics.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

from llmxive_toolkit import get_logger

log = get_logger(__name__)

@dataclass
class ExecutionMetric:
    """Container for a single execution metric."""

    query_id: str
    source_type: str
    complexity_level: int
    ground_truth_plan: Optional[str] = None
    executed_plan: Optional[str] = None
    latency_ms: float = -1.0
    success: bool = False
    timeout: bool = False
    # fields that are derived later but needed for CSV output
    translation_error: bool = field(default=False, init=False)
    timeout_flag: bool = field(default=False, init=False)

def record_execution_metric(
    query_id: str,
    source_type: str,
    complexity_level: int,
    ground_truth_plan: Optional[str],
    executed_plan: Optional[str],
    latency_ms: float,
    success: bool,
    timeout: bool,
) -> ExecutionMetric:
    """Create and return an ExecutionMetric instance."""
    metric = ExecutionMetric(
        query_id=query_id,
        source_type=source_type,
        complexity_level=complexity_level,
        ground_truth_plan=ground_truth_plan,
        executed_plan=executed_plan,
        latency_ms=latency_ms,
        success=success,
        timeout=timeout,
    )
    # The translation error is computed by the caller (main) and
    # injected later; initialise to False here.
    metric.translation_error = False
    metric.timeout_flag = timeout
    log.debug(
        "Recorded metric for query_id=%s source=%s complexity=%d latency=%.2f",
        query_id,
        source_type,
        complexity_level,
        latency_ms,
    )
    return metric

def calculate_translation_error_rate(metrics: List[ExecutionMetric]) -> float:
    """Return the proportion of metrics where the executed plan differs."""
    if not metrics:
        return 0.0
    mismatches = sum(1 for m in metrics if m.translation_error)
    return mismatches / len(metrics)

def aggregate_metrics_by_complexity(
    metrics: List[ExecutionMetric],
) -> dict[int, dict]:
    """Aggregate metrics per complexity level."""
    agg: dict[int, dict] = {}
    for m in metrics:
        lvl = m.complexity_level
        if lvl not in agg:
            agg[lvl] = {"latencies": [], "errors": 0, "count": 0}
        agg[lvl]["latencies"].append(m.latency_ms)
        agg[lvl]["errors"] += int(m.translation_error)
        agg[lvl]["count"] += 1
    # Compute summary statistics
    for lvl, data in agg.items():
        lat = data["latencies"]
        data["mean_latency"] = sum(lat) / len(lat) if lat else 0.0
        data["error_rate"] = data["errors"] / data["count"] if data["count"] else 0.0
    return agg

def save_metrics_to_file(metrics: List[ExecutionMetric], filepath: str) -> None:
    """Write a CSV file that matches ``execution_log.schema.yaml`` plus extra columns.

    The CSV contains:
      query_id, source_type, complexity_level, latency_ms,
      translation_error, success_flag, timeout_flag
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "query_id",
        "source_type",
        "complexity_level",
        "latency_ms",
        "translation_error",
        "success_flag",
        "timeout_flag",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics:
            row = {
                "query_id": m.query_id,
                "source_type": m.source_type,
                "complexity_level": m.complexity_level,
                "latency_ms": f"{m.latency_ms:.3f}",
                "translation_error": str(m.translation_error),
                "success_flag": str(m.success),
                "timeout_flag": str(m.timeout_flag),
            }
            writer.writerow(row)
    log.info("Saved %d execution metrics to %s", len(metrics), path)

def load_metrics_from_file(filepath: str) -> List[ExecutionMetric]:
    """Read the CSV written by ``save_metrics_to_file`` and return metrics."""
    path = Path(filepath)
    metrics: List[ExecutionMetric] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metric = ExecutionMetric(
                query_id=row["query_id"],
                source_type=row["source_type"],
                complexity_level=int(row["complexity_level"]),
                latency_ms=float(row["latency_ms"]),
                success=row["success_flag"].lower() == "true",
                timeout=row["timeout_flag"].lower() == "true",
            )
            # CSV stores booleans as strings
            metric.translation_error = row["translation_error"].lower() == "true"
            metric.timeout_flag = metric.timeout
            metrics.append(metric)
    log.info("Loaded %d execution metrics from %s", len(metrics), path)
    return metrics
