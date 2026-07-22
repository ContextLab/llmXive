"""
Synthetic Trace Generator for MemSlides-like sessions.

Generates 5000 multi-turn revision sessions mimicking the MemSlides schema.
Outputs are split into training and held-out sets.
"""
import json
import uuid
import random
import math
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import from project API
from config import get_config
from utils.validators import TraceValidator
from generators.stats_logger import GenerationStatsLogger

class DataGenerationError(Exception):
    """Raised when synthetic data generation fails due to schema or seed issues."""
    pass

class SyntheticTraceGenerator:
    """Generates synthetic tool-execution traces mimicking MemSlides benchmark schema."""
    
    TOOLS = [
        "create_slide", "update_slide", "delete_slide", 
        "add_text", "add_image", "add_chart", 
        "format_text", "reorder_slides", "export_presentation"
    ]
    
    ARGUMENT_TYPES = [
        "text_content", "image_url", "chart_data", 
        "slide_index", "format_style", "position_coords"
    ]

    def __init__(self, seed: int = 42):
        """Initialize generator with a fixed seed for reproducibility."""
        self.seed = seed
        random.seed(seed)
        self.config = get_config()
        self.validator = TraceValidator()
        self.logger = GenerationStatsLogger()
        self.generated_count = 0
        self.failed_count = 0
        self.variance_stats = []
        self.length_stats = []
        self.tool_counts = {tool: 0 for tool in self.TOOLS}

    def _generate_tool_sequence(self, length: int) -> List[Dict[str, Any]]:
        """Generate a sequence of tool calls with varying lengths."""
        sequence = []
        for i in range(length):
            tool = random.choice(self.TOOLS)
            args = {}
            
            # Generate arguments based on tool type
            if tool in ["add_text", "format_text"]:
                args["text_content"] = f"Sample text content {random.randint(1, 1000)}"
                args["format_style"] = random.choice(["bold", "italic", "underline", "normal"])
            elif tool in ["add_image"]:
                args["image_url"] = f"https://example.com/image_{random.randint(1, 10000)}.png"
                args["position_coords"] = [random.randint(0, 100), random.randint(0, 100)]
            elif tool in ["add_chart"]:
                args["chart_data"] = [random.random() for _ in range(5)]
                args["position_coords"] = [random.randint(0, 100), random.randint(0, 100)]
            elif tool in ["update_slide", "delete_slide", "reorder_slides"]:
                args["slide_index"] = random.randint(0, 10)
            else:
                args["generic_param"] = f"value_{random.randint(1, 100)}"
            
            sequence.append({
                "tool_name": tool,
                "arguments": args,
                "timestamp": datetime.now().isoformat(),
                "turn_id": i
            })
            
            self.tool_counts[tool] += 1
        
        return sequence

    def _calculate_arg_variance(self, sequence: List[Dict[str, Any]]) -> float:
        """
        Calculate raw argument variance.
        
        Variance is computed as the mean pairwise cosine distance of all argument values
        across the sequence. For simplicity in this synthetic generator, we simulate
        this by analyzing the diversity of argument values.
        """
        if not sequence:
            return 0.0
        
        # Collect all argument values
        all_args = []
        for step in sequence:
            for key, value in step["arguments"].items():
                if isinstance(value, (int, float)):
                    all_args.append(float(value))
                elif isinstance(value, list):
                    all_args.extend([float(x) for x in value if isinstance(x, (int, float))])
                elif isinstance(value, str):
                    # Hash string to numeric for variance calculation
                    hash_val = int(hashlib.md5(value.encode()).hexdigest()[:8], 16)
                    all_args.append(hash_val % 1000)
        
        if len(all_args) < 2:
            return 0.0  # Undefined variance, impute default
        
        # Calculate variance using a simple statistical approach
        mean_val = sum(all_args) / len(all_args)
        variance = sum((x - mean_val) ** 2 for x in all_args) / len(all_args)
        
        # Normalize to (0, 1) range for the synthetic metric
        normalized_variance = min(1.0, variance / 100000.0)
        
        return normalized_variance

    def _generate_session(self) -> Dict[str, Any]:
        """Generate a single multi-turn session."""
        # Vary sequence length (5 to 50 turns)
        sequence_length = random.randint(5, 50)
        
        # Generate tool sequence
        tool_sequence = self._generate_tool_sequence(sequence_length)
        
        # Calculate argument variance
        arg_variance = self._calculate_arg_variance(tool_sequence)
        
        # Generate ground-truth slide state (simplified representation)
        slide_state = {
            "total_slides": random.randint(1, 20),
            "content_types": list(set(
                step["tool_name"] for step in tool_sequence 
                if step["tool_name"] in ["add_text", "add_image", "add_chart"]
            )),
            "final_edit_index": len(tool_sequence) - 1
        }
        
        session = {
            "session_id": str(uuid.uuid4()),
            "exact_tool_sequence": tool_sequence,
            "raw_arg_variance": arg_variance,
            "ground_truth_state": slide_state,
            "metadata": {
                "sequence_length": sequence_length,
                "unique_tools": len(set(s["tool_name"] for s in tool_sequence)),
                "generated_at": datetime.now().isoformat(),
                "seed": self.seed
            }
        }
        
        return session

    def _validate_session(self, session: Dict[str, Any]) -> bool:
        """Validate session against schema."""
        try:
            if not self.validator.validate(session):
                return False
            
            # Additional checks
            if "exact_tool_sequence" not in session:
                return False
            if "raw_arg_variance" not in session:
                return False
            if not isinstance(session["raw_arg_variance"], (int, float)):
                return False
            
            return True
        except Exception as e:
            self.logger.log_warning(f"Validation failed for session {session.get('session_id')}: {e}")
            return False

    def generate_traces(self, num_traces: int = 5000, output_dir: Path = None) -> Dict[str, str]:
        """
        Generate multiple synthetic traces and save them.
        
        Args:
            num_traces: Number of traces to generate (default 5000)
            output_dir: Base output directory (uses config if None)
        
        Returns:
            Dict with paths to generated files
        """
        if output_dir is None:
            output_dir = Path(self.config.data_training_path)
        
        # Ensure directories exist
        training_dir = output_dir / "training"
        heldout_dir = output_dir / "held_out"
        training_dir.mkdir(parents=True, exist_ok=True)
        heldout_dir.mkdir(parents=True, exist_ok=True)
        
        # Reset stats
        self.generated_count = 0
        self.failed_count = 0
        self.variance_stats = []
        self.length_stats = []
        
        train_count = int(num_traces * 0.8)
        heldout_count = num_traces - train_count
        
        total_generated = 0
        
        # Generate training set
        for i in range(train_count):
            session = self._generate_session()
            if self._validate_session(session):
                filename = f"session_{session['session_id']}.json"
                filepath = training_dir / filename
                with open(filepath, 'w') as f:
                    json.dump(session, f, indent=2)
                
                self.variance_stats.append(session["raw_arg_variance"])
                self.length_stats.append(session["metadata"]["sequence_length"])
                self.generated_count += 1
                total_generated += 1
            else:
                self.failed_count += 1
        
        # Generate held-out set
        for i in range(heldout_count):
            session = self._generate_session()
            if self._validate_session(session):
                filename = f"session_{session['session_id']}.json"
                filepath = heldout_dir / filename
                with open(filepath, 'w') as f:
                    json.dump(session, f, indent=2)
                
                self.variance_stats.append(session["raw_arg_variance"])
                self.length_stats.append(session["metadata"]["sequence_length"])
                self.generated_count += 1
                total_generated += 1
            else:
                self.failed_count += 1
        
        # Log statistics
        stats = {
            "total_requested": num_traces,
            "total_generated": self.generated_count,
            "total_failed": self.failed_count,
            "training_count": train_count,
            "heldout_count": heldout_count,
            "variance_mean": sum(self.variance_stats) / len(self.variance_stats) if self.variance_stats else 0,
            "variance_std": (sum((x - sum(self.variance_stats)/len(self.variance_stats))**2 for x in self.variance_stats) / len(self.variance_stats))**0.5 if self.variance_stats else 0,
            "length_mean": sum(self.length_stats) / len(self.length_stats) if self.length_stats else 0,
            "tool_distribution": self.tool_counts,
            "training_path": str(training_dir),
            "heldout_path": str(heldout_dir)
        }
        
        self.logger.log_generation_stats(stats)
        
        # Check for failures
        if self.failed_count > 0:
            raise DataGenerationError(
                f"Failed to generate {self.failed_count} traces. "
                f"Generated {self.generated_count}/{num_traces} successfully."
            )
        
        if self.generated_count == 0:
            raise DataGenerationError("No valid traces were generated. Check schema and seed configuration.")
        
        return {
            "training_path": str(training_dir),
            "heldout_path": str(heldout_dir),
            "stats": stats
        }

def generate_synthetic_traces(num_traces: int = 5000, seed: int = 42) -> Dict[str, Any]:
    """
    Main entry point for generating synthetic traces.
    
    Args:
        num_traces: Number of traces to generate
        seed: Random seed for reproducibility
    
    Returns:
        Dictionary containing generation results and paths
    """
    generator = SyntheticTraceGenerator(seed=seed)
    return generator.generate_traces(num_traces=num_traces)

def main():
    """CLI entry point."""
    config = get_config()
    num_traces = config.get("num_traces", 5000)
    seed = config.get("random_seed", 42)
    
    print(f"Starting synthetic trace generation: {num_traces} traces, seed={seed}")
    
    try:
        results = generate_synthetic_traces(num_traces=num_traces, seed=seed)
        print(f"Generation complete!")
        print(f"Training set: {results['stats']['training_count']} traces")
        print(f"Held-out set: {results['stats']['heldout_count']} traces")
        print(f"Training path: {results['training_path']}")
        print(f"Held-out path: {results['heldout_path']}")
        print(f"Variance mean: {results['stats']['variance_mean']:.4f}")
        print(f"Length mean: {results['stats']['length_mean']:.2f}")
    except DataGenerationError as e:
        print(f"Generation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
