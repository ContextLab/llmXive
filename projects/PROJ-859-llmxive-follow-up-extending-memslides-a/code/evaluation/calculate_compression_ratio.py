"""
Calculate per-trace compression ratio and fidelity loss data points.

This module computes the trade-off curve data required for SC-002 by analyzing
the relationship between the compression achieved (rule set size vs trace length)
and the fidelity loss (accuracy drop) for each trace.

Deliverable: CSV mapping each trace to its compression ratio and fidelity loss.
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from project API surface
from config import Config, get_config
from utils.loaders import TraceLoader, MetricsLoader


class CompressionRatioCalculator:
    """
    Calculates compression ratio and fidelity loss for each trace.
    
    Compression Ratio = RuleSetSize / TraceLength
    Fidelity Loss = 1 - (CompressedAccuracy / OriginalAccuracy)
    
    Note: For per-trace analysis, we assume the rule induction process
    provides a compressed representation (rule set) and we measure how
    well it reproduces the original trace behavior.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.raw_data_dir = Path(config.data_raw_dir)
        self.processed_dir = Path(config.data_processed_dir)
        self.rules_dir = self.processed_dir / "rules"
        
    def load_trace_data(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Load trace data by ID from raw directory."""
        trace_file = self.raw_data_dir / f"session_{trace_id}.json"
        if not trace_file.exists():
            return None
        
        with open(trace_file, 'r') as f:
            return json.load(f)
    
    def load_rule_set(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Load rule set for a specific trace from processed/rules directory."""
        rule_file = self.rules_dir / f"rules_{trace_id}.json"
        if not rule_file.exists():
            return None
        
        with open(rule_file, 'r') as f:
            return json.load(f)
    
    def calculate_compression_ratio(self, trace_data: Dict[str, Any], 
                                  rule_set: Dict[str, Any]) -> float:
        """
        Calculate compression ratio for a trace.
        
        Compression Ratio = Number of rules in compressed representation / 
                            Number of steps in original trace
        
        Args:
            trace_data: Original trace data with exact_tool_sequence
            rule_set: Induced rule set for this trace
        
        Returns:
            Compression ratio (0.0 to 1.0, where lower is better compression)
        """
        if not trace_data or not rule_set:
            return 1.0  # No compression if missing data
        
        # Get original trace length
        trace_length = len(trace_data.get('exact_tool_sequence', []))
        if trace_length == 0:
            return 1.0
        
        # Get compressed representation size (number of rules)
        rule_count = len(rule_set.get('rules', []))
        
        # Calculate ratio
        ratio = rule_count / trace_length
        return min(ratio, 1.0)  # Cap at 1.0
    
    def calculate_fidelity_loss(self, trace_data: Dict[str, Any],
                              rule_set: Dict[str, Any]) -> float:
        """
        Calculate fidelity loss for a trace.
        
        Fidelity Loss = 1 - (CompressedAccuracy / OriginalAccuracy)
        
        For per-trace analysis, we use the fidelity metric from the rule induction
        process which measures how well the rules reproduce the original trace.
        
        Args:
            trace_data: Original trace data
            rule_set: Induced rule set with fidelity information
        
        Returns:
            Fidelity loss (0.0 to 1.0, where 0.0 means perfect fidelity)
        """
        if not trace_data or not rule_set:
            return 1.0  # Maximum loss if missing data
        
        # Extract fidelity from rule set (stored as 'fidelity' or 'accuracy')
        fidelity = rule_set.get('fidelity', rule_set.get('accuracy', 1.0))
        
        # Fidelity loss = 1 - fidelity
        fidelity_loss = 1.0 - fidelity
        return max(0.0, min(1.0, fidelity_loss))  # Clamp to [0, 1]
    
    def process_all_traces(self) -> List[Dict[str, Any]]:
        """
        Process all traces and calculate compression metrics.
        
        Returns:
            List of dictionaries containing trace_id, compression_ratio, and fidelity_loss
        """
        results = []
        
        # Find all trace files
        trace_files = list(self.raw_data_dir.glob("session_*.json"))
        
        if not trace_files:
            raise FileNotFoundError(
                f"No trace files found in {self.raw_data_dir}. "
                "Please run trace generation first."
            )
        
        for trace_file in trace_files:
            # Extract trace ID from filename
            trace_id = trace_file.stem.replace("session_", "")
            
            # Load trace data
            trace_data = self.load_trace_data(trace_id)
            if not trace_data:
                continue
            
            # Load corresponding rule set
            rule_set = self.load_rule_set(trace_id)
            if not rule_set:
                # If no rule set exists, skip or use defaults
                # This might happen if rule induction wasn't run for this trace
                continue
            
            # Calculate metrics
            compression_ratio = self.calculate_compression_ratio(trace_data, rule_set)
            fidelity_loss = self.calculate_fidelity_loss(trace_data, rule_set)
            
            results.append({
                'trace_id': trace_id,
                'compression_ratio': round(compression_ratio, 6),
                'fidelity_loss': round(fidelity_loss, 6),
                'trace_length': len(trace_data.get('exact_tool_sequence', [])),
                'rule_count': len(rule_set.get('rules', [])),
                'fidelity': round(rule_set.get('fidelity', rule_set.get('accuracy', 1.0)), 6)
            })
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_path: Optional[str] = None):
        """
        Save compression ratio results to CSV.
        
        Args:
            results: List of result dictionaries
            output_path: Path for output CSV (defaults to config setting)
        """
        if output_path is None:
            output_path = self.processed_dir / "compression_trade_off.csv"
        else:
            output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write CSV
        fieldnames = ['trace_id', 'compression_ratio', 'fidelity_loss', 
                    'trace_length', 'rule_count', 'fidelity']
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        return output_path


def calculate_compression_ratios(config: Optional[Config] = None) -> Tuple[List[Dict[str, Any]], Path]:
    """
    Main function to calculate compression ratios for all traces.
    
    Args:
        config: Optional Config object. If None, loads from default location.
    
    Returns:
        Tuple of (results_list, output_file_path)
    """
    if config is None:
        config = get_config()
    
    calculator = CompressionRatioCalculator(config)
    
    # Process all traces
    results = calculator.process_all_traces()
    
    if not results:
        raise ValueError(
            "No results generated. Ensure that trace generation (T012) "
            "and rule induction (T023) have been completed successfully."
        )
    
    # Save results
    output_file = calculator.save_results(results)
    
    return results, output_file


def main():
    """Main entry point for script execution."""
    print("Starting compression ratio calculation...")
    
    try:
        results, output_file = calculate_compression_ratios()
        
        print(f"Successfully processed {len(results)} traces.")
        print(f"Results saved to: {output_file}")
        
        # Print summary statistics
        if results:
            compression_ratios = [r['compression_ratio'] for r in results]
            fidelity_losses = [r['fidelity_loss'] for r in results]
            
            avg_compression = sum(compression_ratios) / len(compression_ratios)
            avg_fidelity_loss = sum(fidelity_losses) / len(fidelity_losses)
            
            print(f"Average Compression Ratio: {avg_compression:.4f}")
            print(f"Average Fidelity Loss: {avg_fidelity_loss:.4f}")
            print(f"Min Compression Ratio: {min(compression_ratios):.4f}")
            print(f"Max Compression Ratio: {max(compression_ratios):.4f}")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure trace generation and rule induction are complete.")
        sys.exit(1)
    except Exception as e:
        print(f"Error during compression ratio calculation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
