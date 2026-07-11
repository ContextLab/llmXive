"""
API Metrics Aggregation Utility

Implements SC-004: Calculate and report success/failure ratios for API calls.
Tracks metrics for NPM, GitHub, and Audit API interactions.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Singleton instance for global state
_metrics_store: Optional['APIMetricsStore'] = None


class APIMetricsStore:
    """
    Thread-safe store for API call metrics.
    Tracks successes and failures per service and endpoint.
    """

    def __init__(self):
        # Structure: { service_name: { endpoint: { 'success': int, 'failure': int } } }
        self._metrics: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: {'success': 0, 'failure': 0})
        )
        self._lock = None  # Optional threading lock if needed later
        self._history: List[Dict[str, Any]] = []

    def record_call(self, service: str, endpoint: str, success: bool) -> None:
        """
        Record an API call result.

        Args:
            service: Name of the service (e.g., 'npm', 'github', 'audit')
            endpoint: Specific endpoint or operation name
            success: True if the call succeeded, False otherwise
        """
        if success:
            self._metrics[service][endpoint]['success'] += 1
        else:
            self._metrics[service][endpoint]['failure'] += 1

        # Log to history for detailed tracking
        self._history.append({
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'endpoint': endpoint,
            'success': success
        })
        logger.debug(f"API Metric recorded: {service}/{endpoint} - {'Success' if success else 'Failure'}")

    def get_success_ratio(self, service: Optional[str] = None, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate success/failure ratios.

        Args:
            service: Filter by specific service (None for all)
            endpoint: Filter by specific endpoint (None for all)

        Returns:
            Dictionary containing metrics and calculated ratios
        """
        results = {}

        services_to_process = [service] if service else list(self._metrics.keys())

        for svc in services_to_process:
            if svc not in self._metrics:
                continue

            endpoints_to_process = [endpoint] if endpoint else list(self._metrics[svc].keys())

            for ep in endpoints_to_process:
                if ep not in self._metrics[svc]:
                    continue

                data = self._metrics[svc][ep]
                total = data['success'] + data['failure']
                ratio = data['success'] / total if total > 0 else 0.0

                key = f"{svc}/{ep}" if endpoint else f"{svc}"
                results[key] = {
                    'service': svc,
                    'endpoint': ep,
                    'total_calls': total,
                    'successes': data['success'],
                    'failures': data['failure'],
                    'success_ratio': round(ratio, 4),
                    'failure_ratio': round(1.0 - ratio, 4) if total > 0 else 0.0
                }

        return results

    def get_aggregate_metrics(self) -> Dict[str, Any]:
        """
        Get aggregate metrics across all services and endpoints.

        Returns:
            Dictionary with overall success/failure statistics
        """
        total_success = 0
        total_failure = 0
        service_breakdown = {}

        for svc, endpoints in self._metrics.items():
            svc_success = sum(d['success'] for d in endpoints.values())
            svc_failure = sum(d['failure'] for d in endpoints.values())
            total_success += svc_success
            total_failure += svc_failure
            service_breakdown[svc] = {
                'successes': svc_success,
                'failures': svc_failure,
                'total': svc_success + svc_failure
            }

        overall_ratio = total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 0.0

        return {
            'timestamp': datetime.now().isoformat(),
            'total_calls': total_success + total_failure,
            'total_successes': total_success,
            'total_failures': total_failure,
            'overall_success_ratio': round(overall_ratio, 4),
            'overall_failure_ratio': round(1.0 - overall_ratio, 4) if (total_success + total_failure) > 0 else 0.0,
            'service_breakdown': service_breakdown
        }

    def save_report(self, output_path: str) -> None:
        """
        Save current metrics to a JSON file.

        Args:
            output_path: Path to the output JSON file
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'aggregate': self.get_aggregate_metrics(),
            'detailed': self.get_success_ratio()
        }

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"API metrics report saved to {output_path}")

    def reset(self) -> None:
        """Reset all metrics to zero."""
        self._metrics.clear()
        self._history.clear()


def get_metrics_store() -> APIMetricsStore:
    """Get or create the global metrics store instance."""
    global _metrics_store
    if _metrics_store is None:
        _metrics_store = APIMetricsStore()
    return _metrics_store


def record_api_call(service: str, endpoint: str, success: bool) -> None:
    """
    Convenience function to record an API call to the global store.

    Args:
        service: Name of the service
        endpoint: Endpoint or operation name
        success: Call success status
    """
    store = get_metrics_store()
    store.record_call(service, endpoint, success)


def calculate_and_report_success_ratio(service: Optional[str] = None, endpoint: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate and return the success/failure ratio for the given scope.

    Args:
        service: Optional service filter
        endpoint: Optional endpoint filter

    Returns:
        Dictionary containing the calculated ratios
    """
    store = get_metrics_store()
    return store.get_success_ratio(service, endpoint)


def generate_metrics_report(output_path: str = "data/processed/api_metrics_report.json") -> Dict[str, Any]:
    """
    Generate and save a full metrics report.

    Args:
        output_path: Path for the output JSON file

    Returns:
        The generated report dictionary
    """
    store = get_metrics_store()
    store.save_report(output_path)

    # Load and return the report
    with open(output_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Convenience functions for specific services
def record_npm_call(endpoint: str, success: bool) -> None:
    """Record an NPM API call."""
    record_api_call('npm', endpoint, success)


def record_github_call(endpoint: str, success: bool) -> None:
    """Record a GitHub API call."""
    record_api_call('github', endpoint, success)


def record_audit_call(endpoint: str, success: bool) -> None:
    """Record an npm audit API call."""
    record_api_call('audit', endpoint, success)


def main():
    """
    Main entry point for testing the metrics utility.
    Simulates some API calls and generates a report.
    """
    # Reset store for clean test
    store = get_metrics_store()
    store.reset()

    # Simulate some calls
    print("Simulating API calls...")
    record_npm_call('get_top_packages', True)
    record_npm_call('get_top_packages', True)
    record_npm_call('get_top_packages', False)  # Rate limit hit
    record_npm_call('get_package_metadata', True)
    record_github_call('get_commit_date', True)
    record_github_call('get_commit_date', False)  # Repo not found
    record_github_call('get_release_date', True)
    record_audit_call('get_vulnerabilities', True)
    record_audit_call('get_vulnerabilities', True)
    record_audit_call('get_vulnerabilities', False)  # Network error

    # Get and print metrics
    print("\n--- Detailed Metrics ---")
    detailed = store.get_success_ratio()
    for key, value in detailed.items():
        print(f"{key}: Success={value['successes']}, Failure={value['failures']}, Ratio={value['success_ratio']}")

    print("\n--- Aggregate Metrics ---")
    aggregate = store.get_aggregate_metrics()
    print(f"Total Calls: {aggregate['total_calls']}")
    print(f"Successes: {aggregate['total_successes']}")
    print(f"Failures: {aggregate['total_failures']}")
    print(f"Overall Success Ratio: {aggregate['overall_success_ratio']}")

    # Generate report
    output_file = "data/processed/api_metrics_report.json"
    print(f"\nGenerating report to {output_file}...")
    generate_metrics_report(output_file)

    print("Done.")


if __name__ == "__main__":
    main()