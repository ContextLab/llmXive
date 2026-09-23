"""
API Log Aggregation Utility for llmXive research pipeline.

This module implements the API log aggregation utility required by SC-004.
It calculates and reports the success/failure ratio for API calls made
by the various clients in the system.

The utility tracks metrics for all API clients (NpmClient, GithubClient, AuditClient)
and provides aggregated statistics for monitoring and debugging purposes.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from collections import defaultdict

from src.utils.logging_config import get_all_api_metrics, get_api_success_rate

logger = logging.getLogger(__name__)


class APIMetricsAggregator:
    """
    Aggregates and reports API success/failure metrics.

    This class collects metrics from the logging infrastructure and
    calculates aggregate statistics across all API clients.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the metrics aggregator.

        Args:
            output_dir: Directory to write metrics reports. Defaults to 'data/processed'.
        """
        if output_dir is None:
            output_dir = Path("data/processed")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._metrics_snapshot: Dict[str, Any] = {}

    def collect_metrics(self) -> Dict[str, Any]:
        """
        Collect current API metrics from the logging infrastructure.

        Returns:
            Dictionary containing aggregated metrics for all API clients.
        """
        all_metrics = get_all_api_metrics()
        
        total_calls = 0
        total_successes = 0
        total_failures = 0
        client_breakdown = {}

        for client_name, metrics in all_metrics.items():
            calls = metrics.get("total_calls", 0)
            successes = metrics.get("successes", 0)
            failures = metrics.get("failures", 0)
            
            total_calls += calls
            total_successes += successes
            total_failures += failures

            success_rate = (successes / calls * 100) if calls > 0 else 0.0
            failure_rate = (failures / calls * 100) if calls > 0 else 0.0

            client_breakdown[client_name] = {
                "total_calls": calls,
                "successes": successes,
                "failures": failures,
                "success_rate_percent": round(success_rate, 2),
                "failure_rate_percent": round(failure_rate, 2)
            }

        overall_success_rate = (total_successes / total_calls * 100) if total_calls > 0 else 0.0
        overall_failure_rate = (total_failures / total_calls * 100) if total_calls > 0 else 0.0

        self._metrics_snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_api_calls": total_calls,
                "total_successful": total_successes,
                "total_failed": total_failures,
                "overall_success_rate_percent": round(overall_success_rate, 2),
                "overall_failure_rate_percent": round(overall_failure_rate, 2)
            },
            "client_breakdown": client_breakdown,
            "raw_metrics": all_metrics
        }

        return self._metrics_snapshot

    def get_success_failure_ratio(self) -> Dict[str, float]:
        """
        Calculate the success/failure ratio as required by SC-004.

        Returns:
            Dictionary with success_ratio and failure_ratio values.
        """
        if not self._metrics_snapshot:
            self.collect_metrics()

        summary = self._metrics_snapshot.get("summary", {})
        
        return {
            "success_ratio": summary.get("overall_success_rate_percent", 0.0) / 100.0,
            "failure_ratio": summary.get("overall_failure_rate_percent", 0.0) / 100.0,
            "total_calls": summary.get("total_api_calls", 0)
        }

    def report_metrics(self) -> str:
        """
        Generate a human-readable report of API metrics.

        Returns:
            Formatted string report of API success/failure metrics.
        """
        if not self._metrics_snapshot:
            self.collect_metrics()

        summary = self._metrics_snapshot.get("summary", {})
        client_breakdown = self._metrics_snapshot.get("client_breakdown", {})

        report_lines = [
            "=" * 60,
            "API METRICS REPORT",
            f"Generated: {self._metrics_snapshot.get('timestamp', 'N/A')}",
            "=" * 60,
            "",
            "SUMMARY:",
            f"  Total API Calls: {summary.get('total_api_calls', 0)}",
            f"  Successful: {summary.get('total_successful', 0)}",
            f"  Failed: {summary.get('total_failed', 0)}",
            f"  Success Rate: {summary.get('overall_success_rate_percent', 0.0)}%",
            f"  Failure Rate: {summary.get('overall_failure_rate_percent', 0.0)}%",
            "",
            "CLIENT BREAKDOWN:"
        ]

        for client_name, metrics in client_breakdown.items():
            report_lines.extend([
                f"\n  {client_name}:",
                f"    Calls: {metrics.get('total_calls', 0)}",
                f"    Successes: {metrics.get('successes', 0)}",
                f"    Failures: {metrics.get('failures', 0)}",
                f"    Success Rate: {metrics.get('success_rate_percent', 0.0)}%",
                f"    Failure Rate: {metrics.get('failure_rate_percent', 0.0)}%"
            ])

        report_lines.append("")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def save_report(self, filename: str = "api_metrics_report.json") -> Path:
        """
        Save the metrics report to a JSON file.

        Args:
            filename: Name of the output file.

        Returns:
            Path to the saved file.
        """
        if not self._metrics_snapshot:
            self.collect_metrics()

        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self._metrics_snapshot, f, indent=2, default=str)

        logger.info(f"API metrics report saved to {output_path}")
        return output_path


def generate_api_metrics_report(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to generate and return API metrics report.

    Args:
        output_dir: Directory to save the report. Defaults to 'data/processed'.

    Returns:
        Dictionary containing the metrics snapshot.
    """
    aggregator = APIMetricsAggregator(output_dir)
    metrics = aggregator.collect_metrics()
    aggregator.save_report()
    return metrics


def get_api_success_failure_ratio() -> Dict[str, float]:
    """
    Get the current success/failure ratio for all API calls.

    Returns:
        Dictionary with success_ratio, failure_ratio, and total_calls.
    """
    aggregator = APIMetricsAggregator()
    return aggregator.get_success_failure_ratio()


def main():
    """
    Main entry point for standalone execution.

    This function collects API metrics, generates a report, and prints
    the results to stdout.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting API metrics aggregation...")

    aggregator = APIMetricsAggregator()
    metrics = aggregator.collect_metrics()
    
    print(aggregator.report_metrics())
    
    output_path = aggregator.save_report()
    print(f"\nDetailed report saved to: {output_path}")

    # Calculate and display the success/failure ratio
    ratio = aggregator.get_success_failure_ratio()
    print(f"\nSuccess/Failure Ratio:")
    print(f"  Success Ratio: {ratio['success_ratio']:.4f}")
    print(f"  Failure Ratio: {ratio['failure_ratio']:.4f}")
    print(f"  Total Calls: {ratio['total_calls']}")

    logger.info("API metrics aggregation complete.")

    return metrics


if __name__ == "__main__":
    main()