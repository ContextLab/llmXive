"""
Project configuration module.

Provides directory paths and common settings used across the
data acquisition and preprocessing scripts. All paths are expressed
as :class:`pathlib.Path` objects relative to the repository root.
"""
from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    """
    Simple immutable configuration holder.

    Attributes
    ----------
    raw_data_dir: Path
        Base directory for raw downloaded artifacts.
    processed_data_dir: Path
        Directory for processed CSV/JSON outputs.
    seed: int
        Random seed for any stochastic operations (e.g., train/test split).
    """
    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")
    seed: int = 42

    # Convenience properties used by other modules
    @property
    def coco_captions_dir(self) -> Path:
        """Directory where COCO caption files are stored."""
        return self.raw_data_dir / "coco_captions"

    @property
    def diverse_prompts_path(self) -> Path:
        """Default output path for the diverse prompts CSV."""
        return self.processed_data_dir / "diverse_prompts.csv"

    @property
    def prompts_csv_path(self) -> Path:
        """Path for the merged prompts CSV produced by preprocessing."""
        return self.processed_data_dir / "prompts.csv"
