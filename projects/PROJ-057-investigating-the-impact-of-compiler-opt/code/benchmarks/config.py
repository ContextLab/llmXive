"""
Configuration management for compiler optimization benchmarks.

Handles dynamic generation of flag combinations from user-supplied YAML/JSON
or defaults. Validates flags and outputs combinations to JSON.
"""
import os
import json
import argparse
import yaml
from typing import List, Dict, Tuple, Any, Optional, Iterator
from dataclasses import dataclass, field, asdict
from pathlib import Path
import itertools

# Default compiler flags if no user list is provided
DEFAULT_FLAGS = [
    "-O0", "-O1", "-O2", "-O3", "-Os",
    "-march=native",
    "-ffast-math",
    "-funroll-loops"
]

@dataclass
class BenchmarkConfig:
    """Represents a single benchmark configuration."""
    config_id: str
    flags: List[str]
    compiler: str = "g++"
    kernel_type: str = "matmul"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ConfigManager:
    """Manages compiler flag configurations and combination generation."""
    flags: List[str] = field(default_factory=list)
    output_dir: Path = field(default_factory=lambda: Path("data/raw"))
    
    def __post_init__(self):
        if not self.flags:
            self.flags = DEFAULT_FLAGS.copy()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_flags(self) -> List[str]:
        """
        Validate that all flags start with '-' and are non-empty.
        Returns list of valid flags.
        """
        valid_flags = []
        for flag in self.flags:
            if not isinstance(flag, str) or not flag.startswith('-') or len(flag) < 2:
                raise ValueError(f"Invalid flag format: '{flag}'. Must start with '-' and be non-empty.")
            valid_flags.append(flag)
        return valid_flags

    def generate_combinations(self) -> List[BenchmarkConfig]:
        """
        Generate all combinations of flags.
        If a user-supplied list is provided, it REPLACES defaults.
        Returns list of BenchmarkConfig objects.
        """
        valid_flags = self.validate_flags()
        configs = []
        
        # Generate combinations: single flags, pairs, triples, etc.
        # For this implementation, we'll generate all possible non-empty subsets
        # But typically we want specific combinations (e.g., -O2 + -ffast-math)
        # We'll generate combinations of size 1 to len(flags)
        
        config_id_counter = 0
        for r in range(1, len(valid_flags) + 1):
            for combo in itertools.combinations(valid_flags, r):
                config_id_counter += 1
                config = BenchmarkConfig(
                    config_id=f"config_{config_id_counter:04d}",
                    flags=list(combo)
                )
                configs.append(config)
        
        return configs

    def load_from_yaml(self, yaml_path: Path) -> List[str]:
        """Load flags from a YAML file."""
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_path}")
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, list):
            raise ValueError("YAML file must contain a list of flags")
        
        return data

    def load_from_json(self, json_path: Path) -> List[str]:
        """Load flags from a JSON file."""
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list of flags")
        
        return data

    def save_combinations_to_json(self, configs: List[BenchmarkConfig], output_path: Path) -> None:
        """Save generated configurations to a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = [config.to_dict() for config in configs]
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def create_default_manager(self) -> 'ConfigManager':
        """Create a ConfigManager with default flags."""
        return ConfigManager(flags=DEFAULT_FLAGS.copy(), output_dir=self.output_dir)

def validate_flags(flags: List[str]) -> List[str]:
    """
    Standalone function to validate flags.
    Raises ValueError if any flag is invalid.
    """
    manager = ConfigManager(flags=flags)
    return manager.validate_flags()

def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Generate compiler flag combinations for benchmarks"
    )
    parser.add_argument(
        '--generate-combinations',
        action='store_true',
        help='Generate all flag combinations and save to JSON'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Path to YAML or JSON file containing user-supplied flags'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/raw/combinations.json',
        help='Output path for combinations JSON (default: data/raw/combinations.json)'
    )
    parser.add_argument(
        '--default',
        action='store_true',
        help='Use default flags if no input file provided'
    )
    
    args = parser.parse_args()
    
    # Determine flags to use
    flags = None
    
    if args.input:
        input_path = Path(args.input)
        if input_path.suffix.lower() == '.yaml' or input_path.suffix.lower() == '.yml':
            flags = ConfigManager().load_from_yaml(input_path)
        elif input_path.suffix.lower() == '.json':
            flags = ConfigManager().load_from_json(input_path)
        else:
            raise ValueError("Input file must be YAML (.yaml/.yml) or JSON (.json)")
    elif args.default:
        flags = DEFAULT_FLAGS.copy()
    else:
        # If no input and no default flag, check if file exists or use defaults
        # Default behavior: use defaults if no input specified
        flags = DEFAULT_FLAGS.copy()
    
    if not flags:
        print("No flags provided and no input file. Using defaults.")
        flags = DEFAULT_FLAGS.copy()
    
    # Create manager and generate combinations
    manager = ConfigManager(flags=flags)
    configs = manager.generate_combinations()
    
    # Save to JSON
    output_path = Path(args.output)
    manager.save_combinations_to_json(configs, output_path)
    
    print(f"Generated {len(configs)} configurations")
    print(f"Saved to: {output_path.absolute()}")
    
    # Print summary
    print("\nFlag combinations:")
    for config in configs[:10]:  # Show first 10
        print(f"  {config.config_id}: {' '.join(config.flags)}")
    if len(configs) > 10:
        print(f"  ... and {len(configs) - 10} more")

if __name__ == "__main__":
    main()