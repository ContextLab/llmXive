"""
Benchmark module for comparing BaselineAgent and CompressedAgent.

This module runs both agents on the held-out test set in a single execution pass
to ensure data alignment (FR-004, FR-005). It measures Edit Accuracy and 
Retrieval Latency for both agents and outputs a comprehensive JSON report.
"""
import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import from project API surface
from config import get_config
from utils.loaders import TraceLoader
from agents.baseline import BaselineAgent
from agents.compressed import CompressedAgent
from utils.validators import BenchmarkValidator

class BenchmarkError(Exception):
    """Custom exception for benchmarking errors."""
    pass

class BenchmarkRunner:
    """
    Orchestrates the benchmarking of BaselineAgent and CompressedAgent.
    
    Runs both agents on the held-out test set, measures performance metrics,
    and generates a structured report.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the BenchmarkRunner.
        
        Args:
            config: Configuration dictionary containing paths and parameters.
        """
        self.config = config
        self.held_out_path = Path(config.get('held_out_path', 'data/held_out'))
        self.output_path = Path(config.get('benchmark_output_path', 'data/processed/benchmark_results.json'))
        self.global_rules_path = Path(config.get('global_rules_path', 'data/processed/rules/global_rules.json'))
        
        # Initialize agents
        self.baseline_agent = BaselineAgent(config)
        self.compressed_agent = CompressedAgent(config)
        
        # Initialize loader and validator
        self.trace_loader = TraceLoader()
        self.validator = BenchmarkValidator()
        
        # Results storage
        self.results: List[Dict[str, Any]] = []

    def _load_held_out_traces(self) -> List[Dict[str, Any]]:
        """
        Load all traces from the held-out test set.
        
        Returns:
            List of trace dictionaries.
            
        Raises:
            BenchmarkError: If no traces are found or loading fails.
        """
        if not self.held_out_path.exists():
            raise BenchmarkError(f"Held-out directory not found: {self.held_out_path}")
        
        traces = []
        trace_files = list(self.held_out_path.glob('*.json'))
        
        if not trace_files:
            raise BenchmarkError(f"No trace files found in {self.held_out_path}")
        
        for trace_file in trace_files:
            try:
                trace = self.trace_loader.load_trace(trace_file)
                if trace:
                    traces.append(trace)
            except Exception as e:
                print(f"Warning: Failed to load {trace_file}: {e}", file=sys.stderr)
        
        return traces

    def _validate_global_rules(self) -> bool:
        """
        Validate that the global rules file exists and is valid.
        
        Returns:
            True if valid, raises BenchmarkError otherwise.
        """
        if not self.global_rules_path.exists():
            raise BenchmarkError(f"Global rules file not found: {self.global_rules_path}")
        
        try:
            with open(self.global_rules_path, 'r') as f:
                rules = json.load(f)
            if not isinstance(rules, dict) or 'rules' not in rules:
                raise BenchmarkError("Invalid global rules format: missing 'rules' key")
            return True
        except json.JSONDecodeError as e:
            raise BenchmarkError(f"Invalid JSON in global rules file: {e}")

    def _run_baseline_agent(self, trace: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Run the baseline agent on a single trace.
        
        Args:
            trace: The trace dictionary to process.
            
        Returns:
            Tuple of (edit_accuracy, retrieval_latency, error_message).
        """
        try:
            start_time = time.perf_counter()
            result = self.baseline_agent.process_trace(trace)
            end_time = time.perf_counter()
            
            retrieval_latency = end_time - start_time
            edit_accuracy = result.get('edit_accuracy')
            
            return edit_accuracy, retrieval_latency, None
        except Exception as e:
            return None, None, str(e)

    def _run_compressed_agent(self, trace: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Run the compressed agent on a single trace.
        
        Args:
            trace: The trace dictionary to process.
            
        Returns:
            Tuple of (edit_accuracy, retrieval_latency, error_message).
        """
        try:
            start_time = time.perf_counter()
            result = self.compressed_agent.process_trace(trace)
            end_time = time.perf_counter()
            
            retrieval_latency = end_time - start_time
            edit_accuracy = result.get('edit_accuracy')
            
            return edit_accuracy, retrieval_latency, None
        except Exception as e:
            return None, None, str(e)

    def run_benchmark(self) -> Dict[str, Any]:
        """
        Execute the full benchmark on the held-out test set.
        
        Returns:
            A dictionary containing the benchmark results summary and detailed metrics.
        """
        print(f"Starting benchmark on held-out set: {self.held_out_path}")
        
        # Validate prerequisites
        self._validate_global_rules()
        
        # Load traces
        traces = self._load_held_out_traces()
        print(f"Loaded {len(traces)} traces from held-out set")
        
        if not traces:
            raise BenchmarkError("No valid traces found to benchmark")
        
        # Run benchmark on each trace
        for idx, trace in enumerate(traces):
            trace_id = trace.get('trace_id', f'trace_{idx}')
            print(f"Processing trace {idx + 1}/{len(traces)}: {trace_id}")
            
            # Run baseline agent
            baseline_acc, baseline_latency, baseline_error = self._run_baseline_agent(trace)
            
            # Run compressed agent
            compressed_acc, compressed_latency, compressed_error = self._run_compressed_agent(trace)
            
            # Compile results
            result_entry = {
                'trace_id': trace_id,
                'baseline': {
                    'edit_accuracy': baseline_acc,
                    'retrieval_latency': baseline_latency,
                    'error': baseline_error
                },
                'compressed': {
                    'edit_accuracy': compressed_acc,
                    'retrieval_latency': compressed_latency,
                    'error': compressed_error
                },
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            }
            
            self.results.append(result_entry)
        
        # Calculate aggregate metrics
        baseline_accs = [r['baseline']['edit_accuracy'] for r in self.results if r['baseline']['edit_accuracy'] is not None]
        compressed_accs = [r['compressed']['edit_accuracy'] for r in self.results if r['compressed']['edit_accuracy'] is not None]
        baseline_latencies = [r['baseline']['retrieval_latency'] for r in self.results if r['baseline']['retrieval_latency'] is not None]
        compressed_latencies = [r['compressed']['retrieval_latency'] for r in self.results if r['compressed']['retrieval_latency'] is not None]
        
        summary = {
            'total_traces': len(traces),
            'successful_baseline': len(baseline_accs),
            'successful_compressed': len(compressed_accs),
            'baseline_metrics': {
                'avg_edit_accuracy': sum(baseline_accs) / len(baseline_accs) if baseline_accs else None,
                'avg_retrieval_latency': sum(baseline_latencies) / len(baseline_latencies) if baseline_latencies else None,
                'min_retrieval_latency': min(baseline_latencies) if baseline_latencies else None,
                'max_retrieval_latency': max(baseline_latencies) if baseline_latencies else None
            },
            'compressed_metrics': {
                'avg_edit_accuracy': sum(compressed_accs) / len(compressed_accs) if compressed_accs else None,
                'avg_retrieval_latency': sum(compressed_latencies) / len(compressed_latencies) if compressed_latencies else None,
                'min_retrieval_latency': min(compressed_latencies) if compressed_latencies else None,
                'max_retrieval_latency': max(compressed_latencies) if compressed_latencies else None
            }
        }
        
        # Prepare final report
        report = {
            'summary': summary,
            'per_trace_results': self.results,
            'config': {
                'held_out_path': str(self.held_out_path),
                'global_rules_path': str(self.global_rules_path),
                'output_path': str(self.output_path)
            }
        }
        
        return report

    def save_results(self, report: Dict[str, Any]) -> None:
        """
        Save the benchmark report to the output file.
        
        Args:
            report: The benchmark report dictionary.
        """
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Benchmark results saved to {self.output_path}")

def main():
    """Main entry point for the benchmark script."""
    config = get_config()
    
    try:
        runner = BenchmarkRunner(config)
        report = runner.run_benchmark()
        runner.save_results(report)
        
        # Print summary
        summary = report['summary']
        print("\n=== Benchmark Summary ===")
        print(f"Total traces processed: {summary['total_traces']}")
        print(f"Successful baseline runs: {summary['successful_baseline']}")
        print(f"Successful compressed runs: {summary['successful_compressed']}")
        
        if summary['baseline_metrics']['avg_edit_accuracy'] is not None:
            print(f"Baseline avg Edit Accuracy: {summary['baseline_metrics']['avg_edit_accuracy']:.4f}")
            print(f"Compressed avg Edit Accuracy: {summary['compressed_metrics']['avg_edit_accuracy']:.4f}")
        
        if summary['baseline_metrics']['avg_retrieval_latency'] is not None:
            print(f"Baseline avg Retrieval Latency: {summary['baseline_metrics']['avg_retrieval_latency']:.4f}s")
            print(f"Compressed avg Retrieval Latency: {summary['compressed_metrics']['avg_retrieval_latency']:.4f}s")
        
        print("========================")
        
    except BenchmarkError as e:
        print(f"Benchmark Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()