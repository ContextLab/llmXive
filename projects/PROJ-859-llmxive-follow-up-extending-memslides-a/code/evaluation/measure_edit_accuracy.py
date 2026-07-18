"""
Module to measure and record Edit Accuracy for Baseline and Compressed agents.

Edit Accuracy is defined as the fraction of edits matching the ground truth
using exact match on structured slide objects.

FR-005 Implementation.
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from config import get_config
from utils.loaders import TraceLoader
from agents.baseline import BaselineAgent
from agents.compressed import CompressedAgent


class EditAccuracyMeasurer:
    """
    Measures Edit Accuracy for agents by comparing their output slide states
    against ground truth slide states from traces.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.trace_loader = TraceLoader(config)
        self.baseline_agent = BaselineAgent(config)
        self.compressed_agent = CompressedAgent(config)

    def _exact_match_slides(self, predicted: Dict[str, Any], ground_truth: Dict[str, Any]) -> bool:
        """
        Perform exact match comparison between two slide state dictionaries.
        
        Args:
            predicted: The slide state produced by an agent.
            ground_truth: The ground truth slide state from the trace.
            
        Returns:
            True if the structures and values match exactly, False otherwise.
        """
        # Serialize to JSON for deep comparison to handle nested structures
        # This ensures order-independent comparison for dicts if needed, 
        # but standard JSON dumps preserves structure for exact match.
        pred_str = json.dumps(predicted, sort_keys=True)
        truth_str = json.dumps(ground_truth, sort_keys=True)
        return pred_str == truth_str

    def measure_single_trace(
        self, 
        trace_id: str, 
        trace_data: Dict[str, Any]
    ) -> Tuple[str, float, float, Optional[Dict], Optional[Dict], float, float]:
        """
        Run both agents on a single trace and measure their edit accuracy.
        
        Args:
            trace_id: Unique identifier for the trace.
            trace_data: The full trace dictionary containing tool sequence and ground truth.
            
        Returns:
            Tuple of:
            - trace_id
            - baseline_accuracy (0.0 or 1.0)
            - compressed_accuracy (0.0 or 1.0)
            - baseline_output (dict or None)
            - compressed_output (dict or None)
            - baseline_latency (seconds)
            - compressed_latency (seconds)
        """
        # Extract ground truth slide state
        # The trace structure typically has a 'final_state' or similar key
        # based on the synthetic generation schema.
        ground_truth = trace_data.get('final_state') or trace_data.get('ground_truth_slide')
        
        if ground_truth is None:
            # Fallback: try to find a key containing 'state' or 'slide'
            for key in trace_data:
                if 'state' in key.lower() or 'slide' in key.lower():
                    ground_truth = trace_data[key]
                    break
        
        if ground_truth is None:
            raise ValueError(f"Trace {trace_id} missing ground truth slide state.")

        # --- Baseline Agent ---
        start_time = time.perf_counter()
        baseline_output = self.baseline_agent.run(trace_data)
        baseline_latency = time.perf_counter() - start_time

        baseline_accuracy = 0.0
        if baseline_output and 'final_state' in baseline_output:
            baseline_accuracy = 1.0 if self._exact_match_slides(
                baseline_output['final_state'], ground_truth
            ) else 0.0
        elif baseline_output and isinstance(baseline_output, dict):
            # If the agent returns the state directly without a wrapper
            baseline_accuracy = 1.0 if self._exact_match_slides(
                baseline_output, ground_truth
            ) else 0.0

        # --- Compressed Agent ---
        start_time = time.perf_counter()
        compressed_output = self.compressed_agent.run(trace_data)
        compressed_latency = time.perf_counter() - start_time

        compressed_accuracy = 0.0
        if compressed_output and 'final_state' in compressed_output:
            compressed_accuracy = 1.0 if self._exact_match_slides(
                compressed_output['final_state'], ground_truth
            ) else 0.0
        elif compressed_output and isinstance(compressed_output, dict):
            compressed_accuracy = 1.0 if self._exact_match_slides(
                compressed_output, ground_truth
            ) else 0.0

        return (
            trace_id,
            baseline_accuracy,
            compressed_accuracy,
            baseline_output,
            compressed_output,
            baseline_latency,
            compressed_latency
        )

    def measure_all_traces(
        self, 
        trace_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Measure edit accuracy for all traces in the dataset.
        
        Args:
            trace_ids: Optional list of specific trace IDs to process.
                       If None, processes all available traces.
                       
        Returns:
            List of dictionaries containing accuracy and latency metrics.
        """
        results = []
        
        if trace_ids is None:
            # Load all traces from the raw data directory
            trace_files = self.trace_loader.list_traces()
            trace_ids = [Path(f).stem for f in trace_files]

        for trace_id in trace_ids:
            try:
                trace_data = self.trace_loader.load_trace(trace_id)
                if not trace_data:
                    continue
                    
                result = self.measure_single_trace(trace_id, trace_data)
                results.append({
                    'trace_id': result[0],
                    'baseline_accuracy': result[1],
                    'compressed_accuracy': result[2],
                    'baseline_latency_s': result[5],
                    'compressed_latency_s': result[6],
                    # We don't store full outputs in the summary to save space,
                    # but they are available if needed for debugging.
                })
            except Exception as e:
                print(f"Error processing trace {trace_id}: {e}")
                continue

        return results


def calculate_aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate aggregate statistics from the measurement results.
    
    Args:
        results: List of result dictionaries from measure_all_traces.
                
    Returns:
        Dictionary with mean accuracy and latency for both agents.
    """
    if not results:
        return {
            'baseline_mean_accuracy': 0.0,
            'compressed_mean_accuracy': 0.0,
            'baseline_mean_latency_s': 0.0,
            'compressed_mean_latency_s': 0.0,
            'total_traces': 0
        }

    baseline_acc = [r['baseline_accuracy'] for r in results]
    compressed_acc = [r['compressed_accuracy'] for r in results]
    baseline_lat = [r['baseline_latency_s'] for r in results]
    compressed_lat = [r['compressed_latency_s'] for r in results]

    return {
        'baseline_mean_accuracy': sum(baseline_acc) / len(baseline_acc),
        'compressed_mean_accuracy': sum(compressed_acc) / len(compressed_acc),
        'baseline_mean_latency_s': sum(baseline_lat) / len(baseline_lat),
        'compressed_mean_latency_s': sum(compressed_lat) / len(compressed_lat),
        'total_traces': len(results)
    }


def main():
    """
    Main entry point to measure edit accuracy and save results.
    """
    config = get_config()
    measurer = EditAccuracyMeasurer(config)
    
    print("Starting Edit Accuracy Measurement...")
    results = measurer.measure_all_traces()
    
    if not results:
        print("No traces processed. Check data source.")
        return

    # Save detailed results to JSON
    output_path = Path(config['paths']['processed']) / 'edit_accuracy_results.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Saved detailed results to {output_path}")
    
    # Calculate and print aggregates
    aggregates = calculate_aggregate_metrics(results)
    print("\n--- Aggregate Metrics ---")
    print(f"Total Traces: {aggregates['total_traces']}")
    print(f"Baseline Mean Accuracy: {aggregates['baseline_mean_accuracy']:.4f}")
    print(f"Compressed Mean Accuracy: {aggregates['compressed_mean_accuracy']:.4f}")
    print(f"Baseline Mean Latency: {aggregates['baseline_mean_latency_s']:.4f}s")
    print(f"Compressed Mean Latency: {aggregates['compressed_mean_latency_s']:.4f}s")
    
    # Save aggregate summary
    summary_path = Path(config['paths']['processed']) / 'edit_accuracy_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(aggregates, f, indent=2)
    print(f"Saved summary to {summary_path}")


if __name__ == '__main__':
    main()