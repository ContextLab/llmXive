"""
Module to measure Edit Accuracy for Baseline and Compressed agents.

Edit Accuracy is defined as the fraction of edits matching ground truth.
Method: Exact match on structured slide objects.

This module implements the measurement logic required for T033.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from config import get_config
from utils.loaders import TraceLoader


class EditAccuracyMeasurer:
    """
    Measures Edit Accuracy by comparing agent-generated slide states
    against ground-truth states from trace files.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the measurer with configuration.
        
        Args:
            config: Configuration dictionary containing paths and parameters.
        """
        self.config = config
        self.loader = TraceLoader(config)
        
    def _compare_slides(self, generated: Dict[str, Any], ground_truth: Dict[str, Any]) -> bool:
        """
        Perform exact match comparison between two slide objects.
        
        Args:
            generated: The slide state produced by the agent.
            ground_truth: The ground-truth slide state.
            
        Returns:
            True if slides match exactly, False otherwise.
        """
        return generated == ground_truth
    
    def measure_single_trace(self, trace_data: Dict[str, Any], 
                             agent_name: str) -> Tuple[bool, float]:
        """
        Measure edit accuracy for a single trace.
        
        Args:
            trace_data: The full trace dictionary containing tool_sequence,
                        generated_state, and ground_truth_state.
            agent_name: Name of the agent ('baseline' or 'compressed').
                        
        Returns:
            Tuple of (is_correct, latency_seconds).
            is_correct: Boolean indicating if the edit matches ground truth.
            latency_seconds: Time taken to generate the result (if available).
        """
        # Extract relevant fields
        if 'generated_state' not in trace_data:
            # If no generated state, we cannot measure accuracy
            # This might happen if the agent failed or didn't run
            return False, 0.0
            
        generated_state = trace_data['generated_state']
        ground_truth_state = trace_data.get('ground_truth_state')
        
        if ground_truth_state is None:
            raise ValueError(f"Trace {trace_data.get('trace_id', 'unknown')} missing ground_truth_state")
        
        # Perform exact match comparison
        is_correct = self._compare_slides(generated_state, ground_truth_state)
        
        # Get latency if available (from benchmark run)
        latency = trace_data.get('latency_seconds', 0.0)
        
        return is_correct, latency
    
    def measure_batch(self, trace_files: List[Path], 
                     agent_name: str) -> Dict[str, Any]:
        """
        Measure edit accuracy for a batch of trace files.
        
        Args:
            trace_files: List of paths to trace JSON files.
            agent_name: Name of the agent ('baseline' or 'compressed').
                        
        Returns:
            Dictionary containing:
            - total_traces: Number of traces processed
            - correct_count: Number of correct edits
            - accuracy: Fraction of correct edits
            - trace_results: List of individual trace results
        """
        results = []
        correct_count = 0
        total_time = 0.0
        
        for trace_file in trace_files:
            try:
                trace_data = self.loader.load_trace(trace_file)
                is_correct, latency = self.measure_single_trace(trace_data, agent_name)
                
                results.append({
                    'trace_id': trace_data.get('trace_id', trace_file.name),
                    'is_correct': is_correct,
                    'latency_seconds': latency
                })
                
                if is_correct:
                    correct_count += 1
                
                total_time += latency
                
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing {trace_file}: {e}")
                results.append({
                    'trace_id': trace_file.name,
                    'is_correct': False,
                    'latency_seconds': 0.0,
                    'error': str(e)
                })
        
        total_traces = len(results)
        accuracy = correct_count / total_traces if total_traces > 0 else 0.0
        
        return {
            'total_traces': total_traces,
            'correct_count': correct_count,
            'accuracy': accuracy,
            'trace_results': results,
            'agent_name': agent_name,
            'avg_latency': total_time / total_traces if total_traces > 0 else 0.0
        }


def calculate_aggregate_metrics(baseline_results: Dict[str, Any], 
                                compressed_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate aggregate metrics comparing baseline and compressed agents.
    
    Args:
        baseline_results: Results from baseline agent measurement.
        compressed_results: Results from compressed agent measurement.
                        
    Returns:
        Dictionary containing comparative metrics.
    """
    baseline_acc = baseline_results.get('accuracy', 0.0)
    compressed_acc = compressed_results.get('accuracy', 0.0)
    
    delta_acc = baseline_acc - compressed_acc
    
    return {
        'baseline_accuracy': baseline_acc,
        'compressed_accuracy': compressed_acc,
        'edit_accuracy_difference': delta_acc,
        'baseline_correct_count': baseline_results.get('correct_count', 0),
        'compressed_correct_count': compressed_results.get('correct_count', 0),
        'baseline_total_traces': baseline_results.get('total_traces', 0),
        'compressed_total_traces': compressed_results.get('total_traces', 0),
        'baseline_avg_latency': baseline_results.get('avg_latency', 0.0),
        'compressed_avg_latency': compressed_results.get('avg_latency', 0.0)
    }


def main():
    """
    Main entry point for measuring edit accuracy.
    
    This function:
    1. Loads held-out traces
    2. Measures edit accuracy for both baseline and compressed agents
    3. Saves per-trace results and aggregate metrics
    """
    config = get_config()
    
    # Paths
    held_out_dir = Path(config.get('held_out_dir', 'data/held_out'))
    output_dir = Path(config.get('output_dir', 'data/processed'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get trace files
    trace_files = list(held_out_dir.glob('session_*.json'))
    
    if not trace_files:
        raise FileNotFoundError(f"No trace files found in {held_out_dir}")
    
    print(f"Found {len(trace_files)} trace files in {held_out_dir}")
    
    # Initialize measurer
    measurer = EditAccuracyMeasurer(config)
    
    # Measure baseline agent accuracy
    print("Measuring baseline agent edit accuracy...")
    baseline_results = measurer.measure_batch(trace_files, 'baseline')
    print(f"Baseline accuracy: {baseline_results['accuracy']:.4f} "
          f"({baseline_results['correct_count']}/{baseline_results['total_traces']})")
    
    # Measure compressed agent accuracy
    print("Measuring compressed agent edit accuracy...")
    compressed_results = measurer.measure_batch(trace_files, 'compressed')
    print(f"Compressed accuracy: {compressed_results['accuracy']:.4f} "
          f"({compressed_results['correct_count']}/{compressed_results['total_traces']})")
    
    # Calculate aggregate metrics
    aggregate_metrics = calculate_aggregate_metrics(baseline_results, compressed_results)
    
    # Save per-trace results
    baseline_output_path = output_dir / 'baseline_edit_accuracy_results.json'
    with open(baseline_output_path, 'w') as f:
        json.dump(baseline_results, f, indent=2)
    print(f"Saved baseline results to {baseline_output_path}")
    
    compressed_output_path = output_dir / 'compressed_edit_accuracy_results.json'
    with open(compressed_output_path, 'w') as f:
        json.dump(compressed_results, f, indent=2)
    print(f"Saved compressed results to {compressed_output_path}")
    
    # Save aggregate metrics
    aggregate_output_path = output_dir / 'edit_accuracy_aggregate.json'
    with open(aggregate_output_path, 'w') as f:
        json.dump(aggregate_metrics, f, indent=2)
    print(f"Saved aggregate metrics to {aggregate_output_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("EDIT ACCURACY MEASUREMENT SUMMARY")
    print("="*60)
    print(f"Baseline Accuracy:    {aggregate_metrics['baseline_accuracy']:.4f}")
    print(f"Compressed Accuracy:  {aggregate_metrics['compressed_accuracy']:.4f}")
    print(f"Accuracy Difference:  {aggregate_metrics['edit_accuracy_difference']:.4f}")
    print("="*60)
    
    return aggregate_metrics


if __name__ == '__main__':
    main()