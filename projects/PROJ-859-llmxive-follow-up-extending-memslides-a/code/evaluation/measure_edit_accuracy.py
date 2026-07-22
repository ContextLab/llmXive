"""
Measure Edit Accuracy for Baseline and Compressed agents.

Edit Accuracy is defined as the fraction of edits matching ground truth.
Method: Exact match on structured slide objects.

This module implements T033: Measure and record Edit Accuracy for both agents.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from config import get_config
from utils.loaders import TraceLoader

class EditAccuracyMeasurer:
    """
    Measures Edit Accuracy for agent outputs against ground truth traces.
    
    Edit Accuracy = (Number of exact matches between predicted and ground truth slides) 
                  / (Total number of slides in ground truth)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the measurer with configuration.
        
        Args:
            config: Configuration dictionary containing paths and parameters.
        """
        self.config = config
        self.loader = TraceLoader(config)
        
    def _normalize_slide(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a slide object for comparison.
        
        Args:
            slide: The slide dictionary to normalize.
        
        Returns:
            Normalized slide dictionary.
        """
        # Create a normalized copy with sorted keys for consistent comparison
        normalized = {}
        for key in sorted(slide.keys()):
            value = slide[key]
            if isinstance(value, dict):
                normalized[key] = self._normalize_slide(value)
            elif isinstance(value, list):
                # Sort lists of dicts by a stable key if possible
                if value and isinstance(value[0], dict):
                    normalized[key] = sorted(value, key=lambda x: tuple(sorted(x.items())))
                else:
                    normalized[key] = sorted(value) if all(isinstance(x, (str, int, float)) for x in value) else value
            else:
                normalized[key] = value
        return normalized
    
    def _slides_match(self, predicted: Dict[str, Any], ground_truth: Dict[str, Any]) -> bool:
        """
        Check if two slide objects match exactly.
        
        Args:
            predicted: The predicted slide.
            ground_truth: The ground truth slide.
        
        Returns:
            True if slides match exactly, False otherwise.
        """
        return self._normalize_slide(predicted) == self._normalize_slide(ground_truth)
    
    def calculate_edit_accuracy_for_trace(
        self, 
        trace_id: str, 
        predicted_slides: List[Dict[str, Any]], 
        ground_truth_slides: List[Dict[str, Any]]
    ) -> Tuple[float, int, int]:
        """
        Calculate edit accuracy for a single trace.
        
        Args:
            trace_id: The identifier for the trace.
            predicted_slides: List of predicted slide objects.
            ground_truth_slides: List of ground truth slide objects.
        
        Returns:
            Tuple of (accuracy, matches, total).
        """
        if not ground_truth_slides:
            return 0.0, 0, 0
        
        matches = 0
        total = len(ground_truth_slides)
        
        # Compare predicted slides to ground truth
        # We align by index, assuming the agent produces slides in the same order
        for i, gt_slide in enumerate(ground_truth_slides):
            if i < len(predicted_slides):
                pred_slide = predicted_slides[i]
                if self._slides_match(pred_slide, gt_slide):
                    matches += 1
            else:
                # Missing predicted slide counts as non-match
                break
        
        accuracy = matches / total if total > 0 else 0.0
        return accuracy, matches, total
    
    def measure_for_agent(
        self, 
        agent_name: str, 
        held_out_dir: Path,
        results_dir: Path
    ) -> Dict[str, Any]:
        """
        Measure edit accuracy for an agent across all held-out traces.
        
        Args:
            agent_name: Name of the agent ('baseline' or 'compressed').
            held_out_dir: Directory containing held-out trace files.
            results_dir: Directory to save results.
        
        Returns:
            Dictionary containing accuracy metrics.
        """
        config = get_config()
        trace_loader = TraceLoader(config)
        
        # Load all held-out traces
        traces = list(trace_loader.load_traces(held_out_dir))
        
        if not traces:
            raise ValueError(f"No traces found in {held_out_dir}")
        
        results = []
        total_matches = 0
        total_slides = 0
        
        for trace in traces:
            trace_id = trace.get('trace_id', str(trace.get('id', '')))
            
            # Get ground truth slides
            ground_truth_slides = trace.get('final_state', {}).get('slides', [])
            
            # Get predicted slides from agent output
            # The agent output should be stored in the results directory
            agent_output_path = results_dir / f"{agent_name}_{trace_id}.json"
            
            if not agent_output_path.exists():
                # Try alternative naming
                agent_output_path = results_dir / f"{agent_name}_output_{trace_id}.json"
            
            if not agent_output_path.exists():
                # If agent output doesn't exist, we need to run the agent
                # This is a fallback - normally agent outputs should exist
                raise FileNotFoundError(
                    f"Agent output not found for {trace_id}: {agent_output_path}"
                )
            
            with open(agent_output_path, 'r') as f:
                agent_output = json.load(f)
            
            predicted_slides = agent_output.get('final_state', {}).get('slides', [])
            
            # Calculate accuracy for this trace
            accuracy, matches, total = self.calculate_edit_accuracy_for_trace(
                trace_id, predicted_slides, ground_truth_slides
            )
            
            total_matches += matches
            total_slides += total
            
            results.append({
                'trace_id': trace_id,
                'agent': agent_name,
                'accuracy': accuracy,
                'matches': matches,
                'total_slides': total,
                'timestamp': time.time()
            })
        
        # Calculate aggregate accuracy
        aggregate_accuracy = total_matches / total_slides if total_slides > 0 else 0.0
        
        # Save results
        results_file = results_dir / f"{agent_name}_edit_accuracy.csv"
        self._save_results(results, results_file)
        
        return {
            'agent': agent_name,
            'aggregate_accuracy': aggregate_accuracy,
            'total_matches': total_matches,
            'total_slides': total_slides,
            'num_traces': len(traces),
            'per_trace_results': results
        }
    
    def _save_results(self, results: List[Dict[str, Any]], output_path: Path):
        """
        Save results to a CSV file.
        
        Args:
            results: List of result dictionaries.
            output_path: Path to save the CSV file.
        """
        import csv
        
        if not results:
            return
        
        fieldnames = list(results[0].keys())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

def calculate_aggregate_metrics(
    baseline_results: Dict[str, Any], 
    compressed_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate aggregate metrics comparing baseline and compressed agents.
    
    Args:
        baseline_results: Results from baseline agent measurement.
        compressed_results: Results from compressed agent measurement.
    
    Returns:
        Dictionary containing comparative metrics.
    """
    baseline_acc = baseline_results.get('aggregate_accuracy', 0.0)
    compressed_acc = compressed_results.get('aggregate_accuracy', 0.0)
    
    delta = baseline_acc - compressed_acc
    
    return {
        'baseline_accuracy': baseline_acc,
        'compressed_accuracy': compressed_acc,
        'accuracy_delta': delta,
        'baseline_matches': baseline_results.get('total_matches', 0),
        'baseline_total_slides': baseline_results.get('total_slides', 0),
        'compressed_matches': compressed_results.get('total_matches', 0),
        'compressed_total_slides': compressed_results.get('total_slides', 0),
        'num_traces': baseline_results.get('num_traces', 0)
    }

def main():
    """
    Main entry point for measuring edit accuracy.
    
    This function:
    1. Loads configuration
    2. Measures edit accuracy for baseline agent
    3. Measures edit accuracy for compressed agent
    4. Calculates aggregate metrics
    5. Saves results to data/processed/
    """
    config = get_config()
    measurer = EditAccuracyMeasurer(config)
    
    # Paths
    held_out_dir = Path(config['paths']['held_out'])
    results_dir = Path(config['paths']['processed']) / 'agent_results'
    output_dir = Path(config['paths']['processed'])
    
    # Ensure directories exist
    results_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Measuring Edit Accuracy for Baseline Agent...")
    baseline_results = measurer.measure_for_agent('baseline', held_out_dir, results_dir)
    print(f"Baseline Accuracy: {baseline_results['aggregate_accuracy']:.4f}")
    
    print("Measuring Edit Accuracy for Compressed Agent...")
    compressed_results = measurer.measure_for_agent('compressed', held_out_dir, results_dir)
    print(f"Compressed Accuracy: {compressed_results['aggregate_accuracy']:.4f}")
    
    # Calculate aggregate metrics
    aggregate = calculate_aggregate_metrics(baseline_results, compressed_results)
    
    # Save aggregate results
    aggregate_file = output_dir / 'edit_accuracy_aggregate.json'
    with open(aggregate_file, 'w') as f:
        json.dump(aggregate, f, indent=2)
    
    print(f"Aggregate results saved to {aggregate_file}")
    print(f"Accuracy Delta (Baseline - Compressed): {aggregate['accuracy_delta']:.4f}")
    
    return aggregate

if __name__ == '__main__':
    main()