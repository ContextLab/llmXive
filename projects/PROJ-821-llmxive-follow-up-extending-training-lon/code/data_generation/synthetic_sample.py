"""
SyntheticSample entity definition.

Represents a single data sample for the needle-in-a-haystack experiment,
containing metadata about text length, image count, visual tokens, and
the specific 'needle' injected for retrieval verification.
"""
from dataclasses import dataclass, asdict
from typing import List, Optional, Any
import json
import hashlib
from pathlib import Path

# Import config utilities to ensure paths align with project root
# We assume config.py is in the root 'code' package relative to this module
import sys
from pathlib import Path as PathLib

# Add parent to path if running as script, though package import should handle it
# This ensures we can import config if this file is run directly
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(PathLib(__file__).parent.parent))

from config import get_project_root


@dataclass
class SyntheticSample:
    """
    Represents a single synthetic data sample for the experiment.

    Attributes:
        sample_id: Unique identifier for the sample (e.g., "sample_001").
        text_token_count: Number of text tokens in the context.
        image_count: Number of images included in the context.
        visual_token_count: Total number of visual tokens (approx image_count * 576).
        needle_location: Index (0-based) of the image or text segment where the needle is placed.
        needle_value: The actual string value of the needle (e.g., "SECRET_CODE_X").
        arm_type: String indicating the experimental arm ("A" or "B").
        total_context_tokens: Sum of text_token_count and visual_token_count.
        image_paths: List of relative paths to the image files used.
        text_content: The generated synthetic text content.
    """
    sample_id: str
    text_token_count: int
    image_count: int
    visual_token_count: int
    needle_location: int
    needle_value: str
    arm_type: str
    total_context_tokens: int
    image_paths: Optional[List[str]] = None
    text_content: Optional[str] = None

    def __post_init__(self):
        """Validate and calculate derived fields if missing."""
        if self.image_paths is None:
            self.image_paths = []
        if self.text_content is None:
            self.text_content = ""

        # Ensure total_context_tokens is consistent if not explicitly set or if recalculating
        # If the user passed a specific total, we trust it, but we can also enforce consistency
        # For this entity, we treat total_context_tokens as the source of truth for the sum,
        # but we calculate it from components if it seems uninitialized (0) or inconsistent.
        expected_total = self.text_token_count + self.visual_token_count
        if self.total_context_tokens == 0 or self.total_context_tokens != expected_total:
            # In strict mode, we might raise, but for data loading flexibility, we correct it
            # unless it was explicitly set to something else (which implies a discrepancy).
            # Here, we prioritize the calculated sum for consistency with the other fields.
            self.total_context_tokens = expected_total

        # Ensure visual_token_count is consistent with image_count (approx 576 per image)
        # 576 comes from (336/24)^2 = 14*14 = 196 patches?
        # Wait, the task description says: "visual_tokens = image_count * 576".
        # Let's stick to the task spec: 576 tokens per image.
        expected_visual = self.image_count * 576
        if self.visual_token_count != expected_visual:
            self.visual_token_count = expected_visual
            # Recalculate total if we adjusted visual
            self.total_context_tokens = self.text_token_count + self.visual_token_count

    def to_dict(self) -> dict:
        """Convert the sample to a dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Serialize the sample to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, path: str) -> None:
        """Save the sample to a JSON file."""
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: dict) -> "SyntheticSample":
        """Create a SyntheticSample instance from a dictionary."""
        return cls(**data)

    @classmethod
    def load(cls, path: str) -> "SyntheticSample":
        """Load a sample from a JSON file."""
        file_path = Path(path)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def validate(self) -> bool:
        """
        Validate the sample integrity.
        Checks:
        - Image paths exist relative to project root
        - Needle location is within bounds
        - Counts are non-negative
        """
        if self.text_token_count < 0 or self.image_count < 0:
            return False
        
        if self.image_count > 0 and not self.image_paths:
            # If we have images, we should have paths
            return False

        if self.image_count > 0:
            # Check if needle location is valid (assuming it points to an image index or text segment)
            # For this task, we assume needle_location is an image index if image_count > 0
            if not (0 <= self.needle_location < self.image_count):
                # If it's a text-only sample, location might be 0 or N/A. 
                # Given the task says "images are fetched from fixed set", we assume mixed or image-heavy.
                # If image_count is 0, needle_location should be 0 or -1? 
                # Let's assume if image_count is 0, needle is in text, location 0 is valid.
                if self.image_count == 0 and self.needle_location == 0:
                    pass
                else:
                    return False

        # Check image existence if paths are provided
        project_root = get_project_root()
        for img_path in self.image_paths:
            full_path = project_root / img_path
            if not full_path.exists():
                return False

        return True

    def __repr__(self) -> str:
        return (f"SyntheticSample(id={self.sample_id}, "
                f"text_tokens={self.text_token_count}, "
                f"images={self.image_count}, "
                f"arm={self.arm_type})")