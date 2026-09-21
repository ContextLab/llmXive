"""
Configuration management for the llmXive pipeline.
"""
import os
import torch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Config:
    """
    Central configuration object for the project.
    """
    # Paths
    root_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(init=False)
    processed_dir: Path = field(init=False)
    code_dir: Path = field(init=False)
    tests_dir: Path = field(init=False)
    figures_dir: Path = field(init=False)
    specs_dir: Path = field(init=False)

    # Model settings
    device: str = "cpu"
    dtype: str = "float32"
    seed: int = 42

    # Hyperparameters
    batch_size: int = 32
    num_workers: int = 4
    max_epochs: int = 10

    # Quantization settings
    w_bits: int = 4
    a_bits: int = 4
    use_rotation: bool = True

    def __post_init__(self):
        """Initialize derived paths."""
        self.code_dir = self.root_dir / "code"
        self.data_dir = self.root_dir / "data"
        self.processed_dir = self.data_dir / "processed"
        self.tests_dir = self.root_dir / "tests"
        self.figures_dir = self.data_dir / "figures"
        self.specs_dir = self.root_dir / "specs"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.tests_dir.mkdir(parents=True, exist_ok=True)

        # Device detection
        if self.device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            device=os.getenv("LLMXIVE_DEVICE", "auto"),
            seed=int(os.getenv("LLMXIVE_SEED", "42")),
            batch_size=int(os.getenv("LLMXIVE_BATCH_SIZE", "32")),
        )

    def save(self, path: Optional[Path] = None):
        """Save configuration to a JSON file."""
        if path is None:
            path = self.root_dir / "config.json"
        
        import json
        data = {
            "device": self.device,
            "dtype": self.dtype,
            "seed": self.seed,
            "batch_size": self.batch_size,
            "num_workers": self.num_workers,
            "max_epochs": self.max_epochs,
            "w_bits": self.w_bits,
            "a_bits": self.a_bits,
            "use_rotation": self.use_rotation,
        }
        
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "Config":
        """Load configuration from a JSON file."""
        import json
        
        with open(path, "r") as f:
            data = json.load(f)
        
        return cls(
            device=data.get("device", "auto"),
            dtype=data.get("dtype", "float32"),
            seed=data.get("seed", 42),
            batch_size=data.get("batch_size", 32),
            num_workers=data.get("num_workers", 4),
            max_epochs=data.get("max_epochs", 10),
            w_bits=data.get("w_bits", 4),
            a_bits=data.get("a_bits", 4),
            use_rotation=data.get("use_rotation", True),
        )
