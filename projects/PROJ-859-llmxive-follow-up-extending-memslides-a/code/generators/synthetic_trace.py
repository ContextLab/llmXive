import json
import uuid
import random
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Import from existing API surface
from config import get_config

class DataGenerationError(Exception):
    """Custom exception for data generation errors."""
    pass

class SyntheticTraceGenerator:
    """
    Generates synthetic multi-turn revision sessions (traces) for research.
    Implements the Structural Diversity Strategy by accepting seed and distribution parameters.
    """

    def __init__(self, seed: int, variance_multiplier: float = 1.0, tool_types: Optional[List[str]] = None):
        self.seed = seed
        self.variance_multiplier = variance_multiplier
        self.tool_types = tool_types or ["edit", "format", "comment", "review", "revert"]
        random.seed(self.seed)
        self._log_entries: List[Dict[str, Any]] = []

    def _generate_tool_sequence(self, min_length: int = 5, max_length: int = 20) -> List[str]:
        """Generate a sequence of tool calls with potential repetition based on variance."""
        length = random.randint(min_length, max_length)
        # Introduce tool repetition based on variance multiplier
        repetition_prob = 0.3 * self.variance_multiplier
        sequence = []
        for i in range(length):
            if i > 0 and random.random() < repetition_prob:
                # Repeat previous tool
                sequence.append(sequence[-1])
            else:
                sequence.append(random.choice(self.tool_types))
        return sequence

    def _generate_arguments(self, tool: str, variance: float) -> Dict[str, Any]:
        """Generate arguments for a tool call, introducing semantic variance."""
        base_args = {
            "edit": {"target": f"slide_{random.randint(1, 100)}", "content": f"Content version {random.randint(1, 50)}"},
            "format": {"style": random.choice(["bold", "italic", "underline"]), "target": "text"},
            "comment": {"text": f"Review note {random.randint(1, 1000)}", "author": f"user_{random.randint(1, 50)}"},
            "review": {"status": random.choice(["approved", "pending", "rejected"])},
            "revert": {"target": "slide", "version": random.randint(1, 10)}
        }
        
        args = base_args.get(tool, {}).copy()
        
        # Introduce semantic variance in text content based on variance multiplier
        if "text" in args or "content" in args:
            key = "text" if "text" in args else "content"
            # Add variance to text length/content
            original_len = len(args[key])
            variance_len = int(original_len * variance)
            args[key] = args[key] + f" (v{random.randint(1, variance_len)})"
        
        return args

    def _calculate_sequence_entropy(self, sequence: List[str]) -> float:
        """Calculate Shannon entropy of the tool sequence."""
        if not sequence:
            return 0.0
        counts = {}
        for tool in sequence:
            counts[tool] = counts.get(tool, 0) + 1
        
        entropy = 0.0
        total = len(sequence)
        for count in counts.values():
            prob = count / total
            if prob > 0:
                entropy -= prob * math.log2(prob)
        return entropy

    def _calculate_tool_repetition_freq(self, sequence: List[str]) -> float:
        """Calculate frequency of tool repetitions in the sequence."""
        if len(sequence) < 2:
            return 0.0
        repetitions = sum(1 for i in range(1, len(sequence)) if sequence[i] == sequence[i-1])
        return repetitions / (len(sequence) - 1)

    def _calculate_arg_semantic_variance(self, args_list: List[Dict[str, Any]]) -> float:
        """Calculate semantic variance across argument sets."""
        if not args_list:
            return 0.0
        
        # Simple variance proxy: count unique argument values across all keys
        unique_values = set()
        for args in args_list:
            for v in args.values():
                unique_values.add(str(v))
        
        # Normalize by total possible (approximate)
        total_args = sum(len(a) for a in args_list)
        if total_args == 0:
            return 0.0
        
        # Variance proxy: ratio of unique values to total arguments
        return len(unique_values) / total_args

    def generate_trace(self, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a single synthetic trace session."""
        if trace_id is None:
            trace_id = str(uuid.uuid4())
        
        # Generate tool sequence
        min_len = 5
        max_len = 20
        # Apply variance to length distribution
        if self.variance_multiplier > 1.0:
            min_len = int(min_len * (1 + (self.variance_multiplier - 1) * 0.5))
            max_len = int(max_len * self.variance_multiplier)
        
        tool_sequence = self._generate_tool_sequence(min_len, max_len)
        
        # Generate arguments for each tool
        args_list = []
        for tool in tool_sequence:
            args = self._generate_arguments(tool, self.variance_multiplier)
            args_list.append(args)
        
        # Calculate metrics for logging
        seq_entropy = self._calculate_sequence_entropy(tool_sequence)
        rep_freq = self._calculate_tool_repetition_freq(tool_sequence)
        arg_var = self._calculate_arg_semantic_variance(args_list)
        
        # Construct final state (simplified representation)
        final_state = {
            "slide_count": random.randint(1, 20),
            "last_edited": tool_sequence[-1] if tool_sequence else None,
            "version": random.randint(1, 100)
        }
        
        trace = {
            "trace_id": trace_id,
            "session_start": datetime.now().isoformat(),
            "tool_sequence": tool_sequence,
            "arguments": args_list,
            "final_state": final_state,
            "metadata": {
                "seed": self.seed,
                "variance_multiplier": self.variance_multiplier,
                "generated_at": datetime.now().isoformat()
            }
        }
        
        # Log for trace integrity
        self._log_entries.append({
            "trace_id": trace_id,
            "tool_sequence": tool_sequence,
            "sequence_entropy": seq_entropy,
            "tool_repetition_freq": rep_freq,
            "arg_semantic_variance": arg_var,
            "timestamp": datetime.now().isoformat()
        })
        
        return trace

    def get_integrity_log(self) -> List[Dict[str, Any]]:
        """Return the accumulated integrity log entries."""
        return self._log_entries

def generate_synthetic_traces(
    count: int,
    output_dir: str,
    seed: int,
    variance_multiplier: float = 1.0,
    tool_types: Optional[List[str]] = None,
    log_path: Optional[str] = None
) -> str:
    """
    Generate multiple synthetic traces and save them to disk.
    
    Args:
        count: Number of traces to generate
        output_dir: Directory to save trace JSON files
        seed: Random seed for reproducibility
        variance_multiplier: Multiplier for distribution perturbation
        tool_types: List of tool types to use
        log_path: Path to write trace integrity log
        
    Returns:
        Path to the log file
    """
    config = get_config()
    generator = SyntheticTraceGenerator(
        seed=seed,
        variance_multiplier=variance_multiplier,
        tool_types=tool_types
    )
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Ensure log directory exists
    if log_path:
        log_dir = Path(log_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(count):
        trace = generator.generate_trace()
        file_path = output_path / f"{trace['trace_id']}.json"
        with open(file_path, 'w') as f:
            json.dump(trace, f, indent=2)
        
        if i % 500 == 0 and i > 0:
            print(f"Generated {i}/{count} traces...")
    
    # Write integrity log if path provided
    if log_path:
        log_entries = generator.get_integrity_log()
        with open(log_path, 'w') as f:
            for entry in log_entries:
                f.write(json.dumps(entry) + '\n')
        return str(log_path)
    
    return ""

def main():
    """Main entry point for generating training data (T001)."""
    config = get_config()
    
    # T001 Specific parameters
    count = 5000
    seed = config.TRAINING_SEED
    variance_multiplier = 1.0  # Standard parameters for training
    output_dir = config.TRAINING_DATA_PATH
    log_path = config.TRACE_INTEGRITY_LOG_PATH
    
    print(f"Starting T001: Generating {count} training traces with seed={seed}...")
    
    try:
        log_file = generate_synthetic_traces(
            count=count,
            output_dir=output_dir,
            seed=seed,
            variance_multiplier=variance_multiplier,
            log_path=log_path
        )
        print(f"Successfully generated {count} traces to {output_dir}")
        print(f"Integrity log written to {log_file}")
    except Exception as e:
        print(f"Error generating traces: {e}", file=sys.stderr)
        raise DataGenerationError(f"Trace generation failed: {e}")

if __name__ == "__main__":
    main()
