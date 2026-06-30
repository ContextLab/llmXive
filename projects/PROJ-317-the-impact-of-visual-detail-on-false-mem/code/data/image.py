from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Image:
    id: str
    path: Path
    complexity_score: float
    metadata_path: Optional[Path] = None
