import os
import torch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class Config:
    """
    Central configuration for the llmXive project.
    Handles paths, hyperparameters, device detection, and seeds.
    """
    # Project paths
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    data_dir: Path = field(default_factory=lambda: Path("data"))
    code_dir: Path = field(default_factory=lambda: Path("code"))
    tests_dir: Path = field(default_factory=lambda: Path("tests"))
    
    # Sub-directories
    raw_data_dir: Path = field(default_factory=lambda: Path("data/raw"))
    processed_data_dir: Path = field(default_factory=lambda: Path("data/processed"))
    figures_dir: Path = field(default_factory=lambda: Path("figures"))
    
    # Hyperparameters
    seed: int = 42
    batch_size: int = 1
    max_prompt_length: int = 512
    
    # Model settings
    model_name: str = "FLUX.1-dev"
    cpu_fallback_model: str = "stabilityai/stable-diffusion-2-1"
    
    # Clustering settings
    n_clusters: int = 16
    
    # Device detection
    device: Optional[str] = None

    def __post_init__(self):
        """Initialize absolute paths and detect device."""
        # Make paths absolute relative to project root
        self.data_dir = self.project_root / self.data_dir
        self.code_dir = self.project_root / self.code_dir
        self.tests_dir = self.project_root / self.tests_dir
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"
        self.figures_dir = self.project_root / "figures"
        
        # Ensure directories exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        
        # Device detection
        if self.device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"

    def get_coco_path(self) -> Path:
        """Return path to MS-COCO dataset."""
        return self.raw_data_dir / "coco"

    def get_processed_prompts_path(self) -> Path:
        """Return path to processed prompts CSV."""
        return self.processed_data_dir / "prompts.csv"

    def get_clustering_report_path(self) -> Path:
        """Return path to clustering report JSON."""
        return self.processed_data_dir / "clustering_report.json"

    def get_correlation_results_path(self) -> Path:
        """Return path to correlation results JSON."""
        return self.processed_data_dir / "correlation_results.json"

    def get_quantized_activations_path(self) -> Path:
        """Return path to quantized activations JSON."""
        return self.processed_data_dir / "quantized_activations.json"

# Global config instance
config = Config()