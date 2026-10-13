"""
Cost Profiler for tracking CPU time and RSS memory per step.

Implements T010 requirements and matches the expectations of
`code/tests/test_cost_profiler.py`.
"""
import json
import time
import resource
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class CostMetrics:
    """
    Dataclass representing the metrics for a single profiling step.
    """
    step: int
    cpu_time: float
    rss_memory_mb: float
    extra_data: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialize the dataclass to a plain dictionary for JSON output."""
        return {
            "step": self.step,
            "cpu_time": self.cpu_time,
            "rss_memory_mb": self.rss_memory_mb,
            "extra_data": self.extra_data,
        }

class CostProfiler:
    """
    Tracks CPU time and Resident Set Size (RSS) memory usage per step.

    The public API is deliberately aligned with the unit tests in
    `code/tests/test_cost_profiler.py`.  It provides a lightweight
    step‑wise profiler that records CPU time, RSS memory (in MB), and
    optional extra metrics supplied by the caller.
    """

    def __init__(self, output_path: Optional[str] = None):
        """
        Parameters
        ----------
        output_path: Optional[str]
            Path to a JSON‑Lines file where the per‑step metrics will be saved
            when :meth:`save_log` is called.  The directory is created if it does
            not already exist.
        """
        self.output_path: Optional[Path] = Path(output_path) if output_path else None
        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Internal state
        self.step_count: int = 0
        self.start_time: Optional[float] = None          # Wall‑clock start of the whole profiling run (unused in tests)
        self._step_start_time: Optional[float] = None    # Wall‑clock start of the current step
        self._step_start_cpu: Optional[float] = None     # CPU time start of the current step
        self.peak_rss_mb: float = 0.0
        self.metrics_log: List[CostMetrics] = []

    # ------------------------------------------------------------------
    # Step control methods (used by the tests)
    # ------------------------------------------------------------------
    def start_step(self) -> None:
        """Mark the beginning of a profiling step."""
        self._step_start_time = time.time()
        self._step_start_cpu = time.process_time()
        # Capture the current RSS as a baseline for this step.
        self._update_peak_rss()

    def end_step(self, extra_data: Optional[Dict] = None) -> CostMetrics:
        """
        Finish the current step and record its metrics.

        Parameters
        ----------
        extra_data: Optional[Dict]
            Additional user‑provided metrics for this step.

        Returns
        -------
        CostMetrics
            The recorded metrics for the completed step.
        """
        if self._step_start_cpu is None or self._step_start_time is None:
            raise RuntimeError("start_step must be called before end_step")

        # Compute elapsed CPU time for the step.
        cpu_elapsed = time.process_time() - self._step_start_cpu

        # Retrieve current RSS memory (in MB).
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_mb = rss_kb / 1024.0  # Convert from KiB to MiB

        # Update peak RSS observed so far.
        if rss_mb > self.peak_rss_mb:
            self.peak_rss_mb = rss_mb

        # Prepare the metrics record.
        metrics = CostMetrics(
            step=self.step_count,
            cpu_time=cpu_elapsed,
            rss_memory_mb=rss_mb,
            extra_data=extra_data or {}
        )

        # Store and advance counters.
        self.metrics_log.append(metrics)
        self.step_count += 1

        # Reset step‑specific start markers.
        self._step_start_time = None
        self._step_start_cpu = None

        return metrics

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def _update_peak_rss(self) -> None:
        """Refresh the peak RSS measurement without recording a step."""
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        rss_mb = rss_kb / 1024.0
        if rss_mb > self.peak_rss_mb:
            self.peak_rss_mb = rss_mb

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save_log(self) -> None:
        """
        Write all recorded step metrics to ``self.output_path`` as JSON‑Lines.

        Each line corresponds to one :class:`CostMetrics` instance and contains
        the keys ``step``, ``cpu_time``, ``rss_memory_mb`` and ``extra_data``.
        """
        if not self.output_path:
            return

        with self.output_path.open("w", encoding="utf-8") as f:
            for metric in self.metrics_log:
                json_line = json.dumps(metric.to_dict())
                f.write(json_line + "\n")

    # ------------------------------------------------------------------
    # Summary statistics
    # ------------------------------------------------------------------
    def get_summary(self) -> Dict:
        """
        Compute aggregate statistics over all recorded steps.

        Returns
        -------
        dict
            ``{
                "steps": int,
                "total_cpu_time": float,
                "avg_rss_mb": float,
                "peak_rss_mb": float
            }``
        """
        steps = self.step_count
        total_cpu = sum(m.cpu_time for m in self.metrics_log)
        avg_rss = (sum(m.rss_memory_mb for m in self.metrics_log) / steps) if steps else 0.0

        return {
            "steps": steps,
            "total_cpu_time": total_cpu,
            "avg_rss_mb": avg_rss,
            "peak_rss_mb": self.peak_rss_mb,
        }