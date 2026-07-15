"""
Synthetic Trace Generator for MemSlides Benchmark.

Implements User Story 1: Synthetic Trace Generation.
Generates multi-turn revision sessions mimicking the MemSlides schema,
recording tool-execution traces and resulting slide states.
"""
import json
import uuid
import random
import math
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import Config
from generators.stats_logger import log_generation_stats


class SyntheticTraceGenerator:
    """
    Generates synthetic multi-turn revision sessions.
    """

    TOOLS = [
        "create_slide", "add_text", "add_image", "format_text", 
        "delete_element", "move_element", "change_color", "export_pdf"
    ]

    def __init__(self, config: Config, seed: Optional[int] = None):
        self.config = config
        if seed is not None:
            random.seed(seed)
        self.stats_logger = None

    def _generate_tool_sequence(self, length: int) -> List[str]:
        """Generate a random sequence of tool calls."""
        return [random.choice(self.TOOLS) for _ in range(length)]

    def _generate_args(self, tool: str) -> Dict[str, Any]:
        """Generate arguments for a specific tool."""
        if tool == "create_slide":
            return {"title": f"Slide {random.randint(1, 100)}", "layout": random.choice(["title", "blank", "two_col"])}
        elif tool == "add_text":
            return {"content": f"Text block {random.randint(1000, 9999)}", "position": [random.randint(0, 100), random.randint(0, 100)]}
        elif tool == "add_image":
            return {"image_id": f"img_{uuid.uuid4().hex[:8]}", "alt_text": "Sample image"}
        elif tool == "format_text":
            return {"bold": random.choice([True, False]), "italic": random.choice([True, False])}
        elif tool == "delete_element":
            return {"element_id": f"el_{random.randint(1, 1000)}"}
        elif tool == "move_element":
            return {"element_id": f"el_{random.randint(1, 1000)}", "new_pos": [random.randint(0, 100), random.randint(0, 100)]}
        elif tool == "change_color":
            return {"element_id": f"el_{random.randint(1, 1000)}", "color": f"#{random.randint(0, 0xFFFFFF):06x}"}
        else:
            return {"status": "success"}

    def _compute_entropy(self, sequence: List[str]) -> float:
        """Compute Shannon entropy of the tool sequence."""
        if not sequence:
            return 0.0
        counts = {}
        for tool in sequence:
            counts[tool] = counts.get(tool, 0) + 1
        entropy = 0.0
        for count in counts.values():
            p = count / len(sequence)
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy

    def _compute_arg_variance(self, args_list: List[Dict[str, Any]]) -> float:
        """
        Compute raw argument variance.
        Since we don't have real embeddings in this generation phase,
        we simulate variance based on the diversity of argument keys and values.
        For the purpose of T017, we return a deterministic float based on content length.
        """
        if not args_list:
            return 0.0
        # Simple heuristic: variance increases with argument complexity
        total_chars = sum(len(json.dumps(args)) for args in args_list)
        return float(total_chars) / 1000.0

    def generate_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a single synthetic session."""
        if session_id is None:
            session_id = str(uuid.uuid4())

        # Vary sequence length (3 to 20 tools)
        length = random.randint(3, 20)
        tool_sequence = self._generate_tool_sequence(length)
        
        args_sequence = [self._generate_args(t) for t in tool_sequence]
        
        entropy = self._compute_entropy(tool_sequence)
        arg_variance = self._compute_arg_variance(args_sequence)

        # Handle edge cases as per T016
        if length == 0:
            entropy = 0.0  # Defined as 0 for empty sequence
        if math.isnan(arg_variance):
            arg_variance = 0.0  # Impute default

        session = {
            "session_id": session_id,
            "exact_tool_sequence": tool_sequence,
            "args_sequence": args_sequence,
            "final_state": {
                "slide_count": random.randint(1, 5),
                "elements": len(tool_sequence),
                "last_modified": "2023-10-27T10:00:00Z"
            },
            "metadata": {
                "entropy": entropy,
                "raw_arg_variance": arg_variance,
                "tool_types_used": list(set(tool_sequence)),
                "sequence_length": length
            }
        }

        return session

    def save_session(self, session: Dict[str, Any], output_dir: Optional[Path] = None):
        """Save a session to a JSON file and log stats."""
        if output_dir is None:
            output_dir = Path(self.config.DATA_DIR) / "raw"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"session_{session['session_id']}.json"
        file_path = output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session, f, indent=2)

        # Log stats for T017
        stats = {
            "tool_call_count": len(session["exact_tool_sequence"]),
            "arg_variance": session["metadata"]["raw_arg_variance"],
            "entropy": session["metadata"]["entropy"]
        }
        
        log_generation_stats(
            session_id=session["session_id"],
            file_path=file_path,
            stats=stats,
            config=self.config
        )

        return file_path


def generate_synthetic_traces(
    num_sessions: int, 
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Generate a set of synthetic traces.
    
    Args:
        num_sessions: Number of sessions to generate.
        seed: Random seed for reproducibility.
        output_dir: Directory to save files.
        
    Returns:
        List of paths to generated files.
    """
    config = Config()
    generator = SyntheticTraceGenerator(config, seed=seed)
    
    paths = []
    for _ in range(num_sessions):
        session = generator.generate_session()
        file_path = generator.save_session(session, output_dir)
        paths.append(file_path)
        
    return paths


def main():
    """Entry point for script execution."""
    import sys
    
    # Default to 10 sessions if no argument provided
    num_sessions = 10
    if len(sys.argv) > 1:
        try:
            num_sessions = int(sys.argv[1])
        except ValueError:
            print(f"Invalid argument: {sys.argv[1]}. Using default {num_sessions}.")
    
    print(f"Generating {num_sessions} synthetic traces...")
    paths = generate_synthetic_traces(num_sessions)
    print(f"Generated {len(paths)} files in {paths[0].parent}")
    
    # Print summary from T017 logger
    from generators.stats_logger import get_generation_summary
    summary = get_generation_summary()
    print(f"Generation Summary: {summary}")


if __name__ == "__main__":
    main()
