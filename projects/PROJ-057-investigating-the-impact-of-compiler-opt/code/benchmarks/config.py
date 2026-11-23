import os
import json
import argparse
import yaml
from typing import List, Dict, Tuple, Any, Optional, Iterator
from dataclasses import dataclass, field, asdict
from pathlib import Path
import itertools

@dataclass
class BenchmarkConfig:
    """Configuration for a specific benchmark run."""
    config_id: str
    kernel: str
    compiler: str
    flags: List[str]
    tensor_dim: Tuple[int, int]
    iterations: int
    seed: int

class ConfigManager:
    """Manages compiler flag configurations and combination generation."""

    DEFAULT_FLAGS = [
        "-O0", "-O1", "-O2", "-O3", "-Os",
        "-march=native", "-ffast-math", "-funroll-loops"
    ]

    def __init__(self, flags_file: Optional[str] = None):
        self.flags_file = flags_file
        self._flags = self._load_flags()

    def _load_flags(self) -> List[str]:
        """Load flags from YAML/JSON file or use defaults."""
        if self.flags_file and os.path.exists(self.flags_file):
            with open(self.flags_file, 'r') as f:
                if self.flags_file.endswith('.yaml') or self.flags_file.endswith('.yml'):
                    data = yaml.safe_load(f)
                elif self.flags_file.endswith('.json'):
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {self.flags_file}")
            
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'flags' in data:
                    return data['flags']
                else:
                    raise ValueError("Invalid format in flags file. Expected a list or a dict with 'flags' key.")
        else:
            return self.DEFAULT_FLAGS

    def validate_flags(self, flags: List[str]) -> List[str]:
        """Validate that all flags start with '-'."""
        invalid = [f for f in flags if not f.startswith('-')]
        if invalid:
            raise ValueError(f"Invalid flags detected (must start with '-'): {invalid}")
        return flags

    def generate_combinations(self) -> List[List[str]]:
        """Generate all combinations of optimization flags."""
        # For this implementation, we treat the list as a set of independent flags
        # and generate combinations of all possible subsets (excluding empty set).
        # However, typically in compiler benchmarks, we want specific combinations
        # provided by the user or specific levels.
        
        # If the user provides a list like ["-O2", "-march=native"], we generate:
        # ["-O2"], ["-march=native"], ["-O2", "-march=native"]
        
        combinations = []
        flags = self._flags
        
        # Generate all non-empty subsets
        for r in range(1, len(flags) + 1):
            for combo in itertools.combinations(flags, r):
                combinations.append(list(combo))
        
        return combinations

    def generate_configurations(self, kernel: str = "matmul", 
                                compiler: str = "g++", 
                                tensor_dim: Tuple[int, int] = (512, 512),
                                iterations: int = 1000,
                                seed: int = 12345) -> Iterator[BenchmarkConfig]:
        """Generate full benchmark configurations."""
        combos = self.generate_combinations()
        
        for idx, flags in enumerate(combos):
            # Create a unique config ID
            flag_str = "_".join(f.replace("-", "").replace("=", "_") for f in flags)
            config_id = f"{kernel}_{compiler}_{flag_str}_{idx}"
            
            yield BenchmarkConfig(
                config_id=config_id,
                kernel=kernel,
                compiler=compiler,
                flags=flags,
                tensor_dim=tensor_dim,
                iterations=iterations,
                seed=seed
            )

def main():
    parser = argparse.ArgumentParser(description="Generate compiler flag combinations")
    parser.add_argument("--generate-combinations", action="store_true", 
                      help="Generate combinations and save to JSON")
    parser.add_argument("--input", type=str, default=None,
                      help="Path to YAML/JSON file with user-defined flags")
    parser.add_argument("--output", type=str, default="data/raw/combinations.json",
                      help="Output path for combinations JSON")
    
    args = parser.parse_args()
    
    if args.generate_combinations:
        manager = ConfigManager(flags_file=args.input)
        combinations = manager.generate_combinations()
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON
        with open(output_path, 'w') as f:
            json.dump(combinations, f, indent=2)
        
        print(f"Generated {len(combinations)} combinations.")
        print(f"Saved to {args.output}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
