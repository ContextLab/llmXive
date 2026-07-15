"""
Calculate Compressibility Score for each trace based on per-trace rule induction results.

Definition: Compressibility Score = RuleSetSize / TraceLength
Condition: Only calculated if Fidelity >= 90%

This module processes the per-trace rule induction results from T023
and generates the final compressibility scores.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from config import Config
from models.rule_induction import PerTraceRuleInducer


class CompressibilityCalculator:
    """
    Calculator for trace compressibility scores based on rule induction results.
    
    The compressibility score is defined as:
        Score = RuleSetSize / TraceLength
    
    This is only computed for traces where the rule induction achieved
    Fidelity >= 90%.
    """
    
    def __init__(self, config: Optional[Config] = None, fidelity_threshold: float = 0.90):
        """
        Initialize the calculator.
        
        Args:
            config: Project configuration object. If None, creates a default Config.
            fidelity_threshold: Minimum fidelity required to compute score (default: 0.90).
        """
        self.config = config or Config()
        self.fidelity_threshold = fidelity_threshold
        
    def _load_rule_induction_results(self, induction_results_path: Path) -> Dict[str, Any]:
        """
        Load per-trace rule induction results.
        
        Args:
            induction_results_path: Path to the JSON file containing induction results.
            
        Returns:
            Dictionary containing induction results keyed by trace_id.
        """
        if not induction_results_path.exists():
            raise FileNotFoundError(
                f"Rule induction results file not found: {induction_results_path}. "
                "Run T023 (rule_induction.py) first."
            )
        
        with open(induction_results_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_trace_lengths(self, traces_dir: Path) -> Dict[str, int]:
        """
        Load trace lengths from raw trace files.
        
        Args:
            traces_dir: Directory containing raw trace JSON files.
            
        Returns:
            Dictionary mapping trace_id to trace length (number of tool calls).
        """
        trace_lengths = {}
        
        for trace_file in traces_dir.glob("session_*.json"):
            with open(trace_file, 'r', encoding='utf-8') as f:
                trace_data = json.load(f)
            
            trace_id = trace_file.stem
            # Trace length is the number of tool calls in the sequence
            tool_sequence = trace_data.get('exact_tool_sequence', [])
            trace_lengths[trace_id] = len(tool_sequence)
        
        return trace_lengths
    
    def calculate_score(self, ruleset_size: int, trace_length: int) -> float:
        """
        Calculate compressibility score for a single trace.
        
        Args:
            ruleset_size: Number of rules in the induced rule set.
            trace_length: Number of tool calls in the original trace.
            
        Returns:
            Compressibility score (ruleset_size / trace_length).
        """
        if trace_length == 0:
            return float('inf')  # Avoid division by zero
        
        return ruleset_size / trace_length
    
    def process_trace(self, trace_id: str, induction_result: Dict[str, Any], 
                     trace_length: int) -> Optional[Dict[str, Any]]:
        """
        Process a single trace to compute its compressibility score.
        
        Args:
            trace_id: Unique identifier for the trace.
            induction_result: Rule induction result for this trace.
            trace_length: Length of the original trace (number of tool calls).
            
        Returns:
            Dictionary with compressibility score if fidelity >= threshold,
            None otherwise.
        """
        fidelity = induction_result.get('fidelity', 0.0)
        
        # Only compute score if fidelity meets threshold
        if fidelity < self.fidelity_threshold:
            return None
        
        ruleset_size = induction_result.get('ruleset_size', 0)
        
        if trace_length == 0:
            return None  # Cannot compute score for empty trace
        
        score = self.calculate_score(ruleset_size, trace_length)
        
        return {
            'trace_id': trace_id,
            'trace_length': trace_length,
            'ruleset_size': ruleset_size,
            'fidelity': fidelity,
            'compressibility_score': score,
            'meets_fidelity_threshold': True
        }
    
    def process_all_traces(self, traces_dir: Path, induction_results_path: Path,
                          output_path: Path) -> List[Dict[str, Any]]:
        """
        Process all traces and generate compressibility scores.
        
        Args:
            traces_dir: Directory containing raw trace JSON files.
            induction_results_path: Path to rule induction results JSON.
            output_path: Path where the output CSV will be written.
            
        Returns:
            List of dictionaries containing compressibility scores for all valid traces.
        """
        # Load data
        induction_results = self._load_rule_induction_results(induction_results_path)
        trace_lengths = self._load_trace_lengths(traces_dir)
        
        results = []
        
        # Process each trace
        for trace_id, induction_result in induction_results.items():
            trace_length = trace_lengths.get(trace_id, 0)
            
            if trace_length == 0:
                continue
            
            score_data = self.process_trace(trace_id, induction_result, trace_length)
            
            if score_data is not None:
                results.append(score_data)
        
        # Sort by compressibility score (ascending - more compressible first)
        results.sort(key=lambda x: x['compressibility_score'])
        
        # Write output CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if results:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'trace_id', 'trace_length', 'ruleset_size', 
                    'fidelity', 'compressibility_score', 'meets_fidelity_threshold'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
        
        return results


def main():
    """
    Main entry point for calculating compressibility scores.
    
    Reads per-trace rule induction results from T023 and generates
    per-trace compressibility scores to data/processed/per_trace_scores.csv.
    """
    config = Config()
    
    traces_dir = config.data_raw_dir
    induction_results_path = config.data_processed_dir / "rule_induction_results.json"
    output_path = config.data_processed_dir / "per_trace_scores.csv"
    
    print(f"Calculating compressibility scores...")
    print(f"  Traces directory: {traces_dir}")
    print(f"  Induction results: {induction_results_path}")
    print(f"  Output file: {output_path}")
    
    calculator = CompressibilityCalculator(config)
    
    try:
        results = calculator.process_all_traces(
            traces_dir, 
            induction_results_path, 
            output_path
        )
        
        print(f"\nSuccessfully processed {len(results)} traces.")
        print(f"Output written to: {output_path}")
        
        if results:
            scores = [r['compressibility_score'] for r in results]
            fidelities = [r['fidelity'] for r in results]
            
            print(f"\nStatistics:")
            print(f"  Compressibility Score - Min: {min(scores):.4f}, Max: {max(scores):.4f}, Mean: {np.mean(scores):.4f}")
            print(f"  Fidelity - Min: {min(fidelities):.4f}, Max: {max(fidelities):.4f}, Mean: {np.mean(fidelities):.4f}")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure T023 (rule_induction.py) has been run first.")
        raise
    except Exception as e:
        print(f"Error during compressibility score calculation: {e}")
        raise


if __name__ == "__main__":
    main()
