"""
Module to measure and record Retrieval Latency for Baseline and Compressed agents.

FR-005 Requirement: Measure and record Retrieval Latency (time to context-ready) for both agents.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from config import get_config
from utils.loaders import TraceLoader


class RetrievalLatencyMeasurer:
    """
    Measures the time taken for an agent to retrieve context (make it 'ready')
    before generating a response or performing an action.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.trace_loader = TraceLoader(config)

    def measure_baseline_latency(self, trace_id: str) -> float:
        """
        Measures retrieval latency for the BaselineAgent.

        The BaselineAgent loads raw memory (trace data) into context.
        Latency is the time taken from start of retrieval to the point
        the context object is fully constructed and ready for use.

        Args:
            trace_id: The UUID of the trace to load.

        Returns:
            float: Time in seconds.
        """
        # Simulate the agent's retrieval process as defined in baseline.py
        # The BaselineAgent loads the trace JSON.
        start_time = time.perf_counter()

        # Load the raw trace data (simulating 'context-ready' state)
        trace_data = self.trace_loader.load_trace(trace_id)

        end_time = time.perf_counter()
        return end_time - start_time

    def measure_compressed_latency(self, trace_id: str) -> float:
        """
        Measures retrieval latency for the CompressedAgent.

        The CompressedAgent loads the symbolic rule set corresponding to the trace.
        Latency is the time taken to load and parse the rule set.

        Args:
            trace_id: The UUID of the trace to load.

        Returns:
            float: Time in seconds.
        """
        # Simulate the agent's retrieval process as defined in compressed.py
        # The CompressedAgent loads the rule set JSON from data/processed/rules/
        start_time = time.perf_counter()

        # Construct path to the rule set file
        # Assuming rules are stored in data/processed/rules/{trace_id}.json
        rules_path = Path(self.config['data']['processed']) / 'rules' / f"{trace_id}.json"

        if not rules_path.exists():
            raise FileNotFoundError(f"Rule set not found for trace {trace_id} at {rules_path}")

        with open(rules_path, 'r') as f:
            _ = json.load(f)

        end_time = time.perf_counter()
        return end_time - start_time

    def measure_all_traces(self, trace_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Measures retrieval latency for a list of trace IDs for both agents.

        Args:
            trace_ids: List of trace UUIDs.

        Returns:
            List of dictionaries containing trace_id, baseline_latency, compressed_latency.
        """
        results = []
        for tid in trace_ids:
            try:
                baseline_lat = self.measure_baseline_latency(tid)
                compressed_lat = self.measure_compressed_latency(tid)
                results.append({
                    'trace_id': tid,
                    'baseline_retrieval_latency_sec': baseline_lat,
                    'compressed_retrieval_latency_sec': compressed_lat
                })
            except Exception as e:
                # Log error but continue to next trace
                print(f"Error measuring latency for {tid}: {e}")
        return results


def calculate_retrieval_latencies(output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Main entry point to calculate retrieval latencies for all held-out traces.

    Args:
        output_path: Optional path to save the results JSON. If None, results are returned.

    Returns:
        List of latency measurement dictionaries.
    """
    config = get_config()
    measurer = RetrievalLatencyMeasurer(config)

    # Determine which traces to process (Held-out set or all processed traces)
    # Based on T032/T033 flow, we expect a held-out set or a specific benchmark set.
    # We will attempt to load the list of trace IDs from the processed feature matrix
    # or simply scan the data/raw directory if a specific list isn't provided.
    # For robustness, we scan data/raw for session_*.json files.
    raw_data_dir = Path(config['data']['raw'])
    trace_files = list(raw_data_dir.glob("session_*.json"))
    trace_ids = [f.stem.replace("session_", "") for f in trace_files]

    if not trace_ids:
        raise FileNotFoundError("No session files found in data/raw/. Ensure T012 has run.")

    results = measurer.measure_all_traces(trace_ids)

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Retrieval latencies saved to {output_path}")
    else:
        # If no output path provided, we still need to return the data
        # but for the pipeline, we usually require a file.
        # Defaulting to a standard location if not specified.
        default_path = Path(config['data']['processed']) / 'retrieval_latencies.json'
        default_path.parent.mkdir(parents=True, exist_ok=True)
        with open(default_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Retrieval latencies saved to {default_path}")

    return results


def main():
    """
    CLI entry point for measuring retrieval latency.
    """
    config = get_config()
    output_path = Path(config['data']['processed']) / 'retrieval_latencies.json'
    calculate_retrieval_latencies(str(output_path))


if __name__ == "__main__":
    main()