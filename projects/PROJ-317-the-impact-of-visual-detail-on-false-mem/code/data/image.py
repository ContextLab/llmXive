from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Image:
    """
    Entity representing a stimulus image.
    """
    id: str
    path: str
    complexity_score: float
    metadata_path: Optional[str] = None
