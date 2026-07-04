"""
Configuration manager for compiler optimization benchmarks.

Handles compiler flags and tensor dimensions for the LLM inference latency study.
"""

import os
import json
from typing import List, Dict, Tuple, Any, Optional, Iterator
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default directories
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
INTERMEDIATES_DIR = PROJECT_ROOT / "data" / "intermediates"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Compiler optimization flags
OPT_LEVELS = ["-O0", "-O1", "-O2", "-O3", "-Os"]
ARCH_FLAGS = ["-march=native"]
MATH_FLAGS = ["-ffast-math"]
LOOP_FLAGS = ["-funroll-loops"]

# Tensor dimensions (width x width for square matrices)
TENSOR_SIZES = [768, 512]

@dataclass
class BenchmarkConfig:
    """Represents a single benchmark configuration."""
    config_id: str
    opt_level: str
    arch_flag: Optional[str]
    math_flag: Optional[str]
    loop_flag: Optional[str]
    tensor_size: int
    flags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Build the full flag list
        self.flags = [self.opt_level]
        if self.arch_flag:
            self.flags.append(self.arch_flag)
        if self.math_flag:
            self.flags.append(self.math_flag)
        if self.loop_flag:
            self.flags.append(self.loop_flag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            "config_id": self.config_id,
            "opt_level": self.opt_level,
            "arch_flag": self.arch_flag,
            "math_flag": self.math_flag,
            "loop_flag": self.loop_flag,
            "tensor_size": self.tensor_size,
            "flags": self.flags,
            "flag_string": " ".join(self.flags)
        }
    
    def to_json(self) -> str:
        """Serialize config to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

@dataclass
class ConfigManager:
    """Manages all benchmark configurations."""
    configs: List[BenchmarkConfig] = field(default_factory=list)
    
    def generate_config_id(self, opt_level: str, arch: Optional[str], 
                           math: Optional[str], loop: Optional[str], 
                           size: int) -> str:
        """Generate a unique, deterministic config ID."""
        parts = [opt_level.replace("-", "")]
        if arch:
            parts.append(arch.replace("-", "").replace("=", "_"))
        if math:
            parts.append(math.replace("-", "").replace("=", "_"))
        if loop:
            parts.append(loop.replace("-", "").replace("=", "_"))
        parts.append(f"t{size}")
        return "_".join(parts)
    
    def add_config(self, opt_level: str, arch_flag: Optional[str] = None,
                   math_flag: Optional[str] = None, loop_flag: Optional[str] = None,
                   tensor_size: int = 768) -> BenchmarkConfig:
        """Add a new configuration to the manager."""
        config_id = self.generate_config_id(opt_level, arch_flag, math_flag, loop_flag, tensor_size)
        
        # Check for duplicates
        for existing in self.configs:
            if existing.config_id == config_id:
                return existing
        
        config = BenchmarkConfig(
            config_id=config_id,
            opt_level=opt_level,
            arch_flag=arch_flag,
            math_flag=math_flag,
            loop_flag=loop_flag,
            tensor_size=tensor_size
        )
        self.configs.append(config)
        return config
    
    def generate_all_combinations(self) -> List[BenchmarkConfig]:
        """Generate all combinations of flags and tensor sizes."""
        self.configs = []
        
        for size in TENSOR_SIZES:
            for opt in OPT_LEVELS:
                # Base config with just optimization level
                self.add_config(opt, tensor_size=size)
                
                # With arch flag
                self.add_config(opt, arch_flag="-march=native", tensor_size=size)
                
                # With math flag
                self.add_config(opt, math_flag="-ffast-math", tensor_size=size)
                
                # With loop flag
                self.add_config(opt, loop_flag="-funroll-loops", tensor_size=size)
                
                # Combinations
                self.add_config(opt, arch_flag="-march=native", math_flag="-ffast-math", tensor_size=size)
                self.add_config(opt, arch_flag="-march=native", loop_flag="-funroll-loops", tensor_size=size)
                self.add_config(opt, math_flag="-ffast-math", loop_flag="-funroll-loops", tensor_size=size)
                self.add_config(opt, arch_flag="-march=native", math_flag="-ffast-math", loop_flag="-funroll-loops", tensor_size=size)
        
        return self.configs
    
    def get_config_by_id(self, config_id: str) -> Optional[BenchmarkConfig]:
        """Retrieve a configuration by its ID."""
        for config in self.configs:
            if config.config_id == config_id:
                return config
        return None
    
    def filter_by_opt_level(self, opt_level: str) -> List[BenchmarkConfig]:
        """Filter configurations by optimization level."""
        return [c for c in self.configs if c.opt_level == opt_level]
    
    def filter_by_tensor_size(self, size: int) -> List[BenchmarkConfig]:
        """Filter configurations by tensor size."""
        return [c for c in self.configs if c.tensor_size == size]
    
    def save_configs_to_file(self, output_path: Optional[str] = None) -> str:
        """Save all configurations to a JSON file."""
        if output_path is None:
            output_path = str(RESULTS_DIR / "configurations.json")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        config_data = [c.to_dict() for c in self.configs]
        with open(output_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return output_path
    
    def load_configs_from_file(self, input_path: str) -> List[BenchmarkConfig]:
        """Load configurations from a JSON file."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Config file not found: {input_path}")
        
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        self.configs = []
        for item in data:
            config = BenchmarkConfig(
                config_id=item["config_id"],
                opt_level=item["opt_level"],
                arch_flag=item.get("arch_flag"),
                math_flag=item.get("math_flag"),
                loop_flag=item.get("loop_flag"),
                tensor_size=item["tensor_size"]
            )
            self.configs.append(config)
        
        return self.configs
    
    def __iter__(self) -> Iterator[BenchmarkConfig]:
        """Iterate over configurations."""
        return iter(self.configs)
    
    def __len__(self) -> int:
        """Return number of configurations."""
        return len(self.configs)
    
    def __repr__(self) -> str:
        return f"ConfigManager({len(self.configs)} configs)"

def create_default_manager() -> ConfigManager:
    """Create a ConfigManager with all default combinations."""
    manager = ConfigManager()
    manager.generate_all_combinations()
    return manager

def validate_flags(flags: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate a list of compiler flags.
    
    Returns:
        Tuple of (is_valid, list_of_invalid_flags)
    """
    valid_prefixes = ["-O", "-march", "-ffast", "-funroll", "-m", "-f"]
    invalid = []
    
    for flag in flags:
        if not flag.startswith("-"):
            invalid.append(flag)
            continue
        
        # Check against known valid flags or prefixes
        is_valid = False
        if flag in OPT_LEVELS:
            is_valid = True
        elif flag in ARCH_FLAGS:
            is_valid = True
        elif flag in MATH_FLAGS:
            is_valid = True
        elif flag in LOOP_FLAGS:
            is_valid = True
        else:
            # Check if it starts with a valid prefix
            for prefix in valid_prefixes:
                if flag.startswith(prefix):
                    is_valid = True
                    break
        
        if not is_valid:
            invalid.append(flag)
    
    return len(invalid) == 0, invalid

def main():
    """Main entry point for testing the config manager."""
    print("Initializing Benchmark Configuration Manager...")
    
    # Create manager with all combinations
    manager = create_default_manager()
    print(f"Generated {len(manager)} configurations")
    
    # Save to file
    output_path = manager.save_configs_to_file()
    print(f"Saved configurations to: {output_path}")
    
    # Test filtering
    o3_configs = manager.filter_by_opt_level("-O3")
    print(f"Found {len(o3_configs)} configurations with -O3")
    
    # Test validation
    valid_flags = ["-O2", "-march=native", "-ffast-math"]
    is_valid, invalid = validate_flags(valid_flags)
    print(f"Validation of {valid_flags}: {is_valid} (invalid: {invalid})")
    
    invalid_flags = ["-O2", "-invalid-flag", "-O5"]
    is_valid, invalid = validate_flags(invalid_flags)
    print(f"Validation of {invalid_flags}: {is_valid} (invalid: {invalid})")
    
    # List some configs
    print("\nSample configurations:")
    for i, config in enumerate(manager):
        if i < 5:
            print(f"  {config.config_id}: {' '.join(config.flags)} (size: {config.tensor_size})")
    
    return manager

if __name__ == "__main__":
    main()
