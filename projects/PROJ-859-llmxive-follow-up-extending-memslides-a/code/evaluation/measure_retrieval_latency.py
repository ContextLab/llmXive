import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from config import get_config
from utils.loaders import TraceLoader

class RetrievalLatencyMeasurer:
    """
    Measures the time required for both BaselineAgent and CompressedAgent
    to prepare their context (retrieval phase) for a given trace.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.loader = TraceLoader()
        # Import agents locally to avoid circular deps if any, 
        # but ensure we use the classes defined in the API surface
        from agents.baseline import BaselineAgent
        from agents.compressed import CompressedAgent
        self.BaselineAgent = BaselineAgent
        self.CompressedAgent = CompressedAgent

    def measure_baseline_latency(self, trace: Dict[str, Any]) -> float:
        """
        Measures retrieval latency for the BaselineAgent.
        Returns time in seconds.
        """
        agent = self.BaselineAgent(self.config)
        start_time = time.perf_counter()
        # The agent prepares context based on the trace
        _ = agent.prepare_context(trace)
        end_time = time.perf_counter()
        return end_time - start_time

    def measure_compressed_latency(self, trace: Dict[str, Any]) -> float:
        """
        Measures retrieval latency for the CompressedAgent.
        Returns time in seconds.
        """
        agent = self.CompressedAgent(self.config)
        start_time = time.perf_counter()
        # The agent prepares context using the global rule set
        _ = agent.prepare_context(trace)
        end_time = time.perf_counter()
        return end_time - start_time

    def process_trace(self, trace_id: str, trace: Dict[str, Any]) -> Dict[str, Any]:
        """
        Measures latency for both agents on a single trace.
        """
        baseline_latency = self.measure_baseline_latency(trace)
        compressed_latency = self.measure_compressed_latency(trace)

        return {
            "trace_id": trace_id,
            "baseline_latency": baseline_latency,
            "compressed_latency": compressed_latency,
            "latency_delta": baseline_latency - compressed_latency
        }

def calculate_retrieval_latencies(input_dir: str, output_path: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Iterates over all trace files in input_dir, measures retrieval latency,
    and saves the results to output_path.
    """
    measurer = RetrievalLatencyMeasurer(config)
    results = []
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input directory {input_dir} does not exist.")

    trace_files = sorted(input_path.glob("*.json"))
    if not trace_files:
        raise ValueError(f"No JSON trace files found in {input_dir}.")

    for trace_file in trace_files:
        trace_id = trace_file.stem
        try:
            trace_data = json.loads(trace_file.read_text())
            result = measurer.process_trace(trace_id, trace_data)
            results.append(result)
        except Exception as e:
            # Fail loudly as per constraints
            raise RuntimeError(f"Failed to process trace {trace_file}: {e}")

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    return results

def main():
    config = get_config()
    # Determine input directory based on config or default to held_out
    input_dir = config.get('held_out_dir', 'data/held_out')
    output_path = config.get('latency_output_path', 'data/processed/retrieval_latencies.json')

    print(f"Measuring retrieval latency for traces in: {input_dir}")
    print(f"Saving results to: {output_path}")

    try:
        results = calculate_retrieval_latencies(input_dir, output_path, config)
        print(f"Successfully measured {len(results)} traces.")
        print(f"Results saved to {output_path}")
    except Exception as e:
        print(f"ERROR: Retrieval latency measurement failed: {e}")
        raise

if __name__ == "__main__":
    main()
