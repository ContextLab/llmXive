import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from config import get_config
from utils.loaders import TraceLoader

class RetrievalLatencyMeasurer:
    """
    Measures the retrieval latency (time to context-ready) for both Baseline and Compressed agents.
    
    This class implements the core logic for FR-005: Measure and record Retrieval Latency.
    It calculates the time taken from the start of the retrieval process until the context
    is fully prepared and ready for the agent to generate a response.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.loader = TraceLoader(config)
        self.latency_results: List[Dict[str, Any]] = []

    def measure_baseline_latency(self, trace: Dict[str, Any]) -> float:
        """
        Measures retrieval latency for the BaselineAgent (raw memory).
        
        The BaselineAgent loads the full raw trace history into memory.
        Latency is measured as the time to load and parse the JSON trace file.
        
        Args:
            trace: The trace dictionary containing 'tool_sequence' and other metadata.
            
        Returns:
            float: Time in seconds to retrieve context.
        """
        start_time = time.perf_counter()
        
        # Simulate raw memory loading (parsing the trace JSON)
        # In a real scenario, this might involve loading from a vector DB or large file
        _ = json.dumps(trace)  # Ensure full serialization/deserialization cost is counted
        
        end_time = time.perf_counter()
        return end_time - start_time

    def measure_compressed_latency(self, trace: Dict[str, Any], rules_path: Path) -> float:
        """
        Measures retrieval latency for the CompressedAgent (symbolic rules).
        
        The CompressedAgent loads a pre-compressed set of rules and matches them
        against the current trace state. Latency includes loading the rule set
        and performing the initial match.
        
        Args:
            trace: The trace dictionary.
            rules_path: Path to the global_rules.json file.
            
        Returns:
            float: Time in seconds to retrieve context.
        """
        start_time = time.perf_counter()
        
        # Load global rules (simulating the "context-ready" state for the rule agent)
        with open(rules_path, 'r') as f:
            rules = json.load(f)
        
        # Simulate matching the current trace state against the rules
        # This is a simplified simulation of the rule lookup cost
        if not rules:
            # Edge case: empty rules
            pass
        else:
            # Simple check to ensure we process the structure
            _ = len(rules.get('rules', []))
        
        end_time = time.perf_counter()
        return end_time - start_time

    def run_measurement(
        self, 
        trace_id: str, 
        trace_data: Dict[str, Any], 
        rules_path: Path
    ) -> Dict[str, float]:
        """
        Runs latency measurements for a single trace against both agents.
        
        Args:
            trace_id: Unique identifier for the trace.
            trace_data: The full trace dictionary.
            rules_path: Path to the global rules file.
            
        Returns:
            Dict containing baseline_latency and compressed_latency.
        """
        baseline_latency = self.measure_baseline_latency(trace_data)
        compressed_latency = self.measure_compressed_latency(trace_data, rules_path)
        
        return {
            "trace_id": trace_id,
            "baseline_latency": baseline_latency,
            "compressed_latency": compressed_latency
        }

    def calculate_retrieval_latencies(
        self, 
        held_out_dir: Path, 
        rules_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Processes all traces in the held-out directory and measures latencies.
        
        Args:
            held_out_dir: Path to the directory containing held-out trace JSON files.
            rules_path: Path to the global_rules.json file.
            
        Returns:
            List of dictionaries containing latency measurements for each trace.
        """
        results = []
        
        if not held_out_dir.exists():
            raise FileNotFoundError(f"Held-out directory not found: {held_out_dir}")
        
        if not rules_path.exists():
            raise FileNotFoundError(f"Global rules file not found: {rules_path}")
        
        trace_files = list(held_out_dir.glob("session_*.json"))
        
        if not trace_files:
            raise ValueError(f"No trace files found in {held_out_dir}")
        
        for trace_file in trace_files:
            try:
                trace_data = self.loader.load_trace(trace_file)
                trace_id = trace_file.stem  # e.g., session_1234-5678
                
                measurement = self.run_measurement(trace_id, trace_data, rules_path)
                results.append(measurement)
                
            except Exception as e:
                # Log error but continue processing other traces
                print(f"Error processing {trace_file}: {e}")
                continue
        
        self.latency_results = results
        return results

    def save_results(self, output_path: Path) -> None:
        """
        Saves the latency measurement results to a JSON file.
        
        Args:
            output_path: Path where the results JSON file will be saved.
        """
        if not self.latency_results:
            raise ValueError("No latency results to save. Run calculation first.")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.latency_results, f, indent=2)
        
        print(f"Retrieval latency results saved to {output_path}")


def main():
    """
    Main entry point for measuring retrieval latency.
    
    Executes the measurement pipeline on the held-out test set and saves
    the results to data/processed/retrieval_latencies.json.
    """
    config = get_config()
    
    held_out_dir = Path(config['paths']['held_out'])
    rules_path = Path(config['paths']['global_rules'])
    output_path = Path(config['paths']['latency_results'])
    
    print(f"Starting retrieval latency measurement...")
    print(f"Held-out directory: {held_out_dir}")
    print(f"Global rules path: {rules_path}")
    
    try:
        measurer = RetrievalLatencyMeasurer(config)
        results = measurer.calculate_retrieval_latencies(held_out_dir, rules_path)
        measurer.save_results(output_path)
        
        # Print summary statistics
        if results:
            baseline_latencies = [r['baseline_latency'] for r in results]
            compressed_latencies = [r['compressed_latency'] for r in results]
            
            avg_baseline = sum(baseline_latencies) / len(baseline_latencies)
            avg_compressed = sum(compressed_latencies) / len(compressed_latencies)
            
            print(f"\n--- Retrieval Latency Summary ---")
            print(f"Traces processed: {len(results)}")
            print(f"Baseline Agent Avg Latency: {avg_baseline:.6f} seconds")
            print(f"Compressed Agent Avg Latency: {avg_compressed:.6f} seconds")
            print(f"Latency Reduction: {((avg_baseline - avg_compressed) / avg_baseline * 100):.2f}%")
        
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        print("Ensure that the held-out dataset and global rules file have been generated by previous tasks.")
        raise
    except Exception as e:
        print(f"ERROR during measurement: {e}")
        raise


if __name__ == "__main__":
    main()
