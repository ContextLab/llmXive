"""
XAI Overlay Generation Module.

Provides rule-based generation of XAI overlays (heatmaps, feature importance)
for the Explainable Interface.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import math
import random

@dataclass
class OverlayFeature:
    """Represents a single feature in an XAI overlay."""
    feature_id: str
    importance_score: float
    description: str

@dataclass
class XAIOverlay:
    """Represents a complete XAI overlay for a task."""
    task_id: str
    features: List[OverlayFeature]
    heatmap_data: Dict[str, float] # Map of UI element ID to intensity (0.0-1.0)

class RuleBasedXAIOverlayGenerator:
    """
    Generates deterministic, rule-based XAI overlays.

    Logic:
    - Based on task difficulty parameters.
    - Produces feature-level overlay data.
    - No external models or datasets required.
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_overlay(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an overlay based on task input parameters.

        Args:
            task_input: Dictionary containing task parameters (e.g., difficulty).

        Returns:
            Dictionary representing the XAI overlay data.
        """
        difficulty = task_input.get("difficulty", "medium")
        
        # Base importance scores based on difficulty
        if difficulty == "easy":
            base_scores = [0.2, 0.3, 0.5]
        elif difficulty == "medium":
            base_scores = [0.4, 0.4, 0.2]
        else: # hard
            base_scores = [0.1, 0.6, 0.3]

        # Normalize scores to sum to 1.0
        total = sum(base_scores)
        normalized_scores = [s / total for s in base_scores]

        # Generate features
        features = []
        heatmap_data = {}
        
        feature_names = ["UI_Element_A", "UI_Element_B", "UI_Element_C"]
        descriptions = [
            "Primary action button",
            "Secondary navigation link",
            "Status indicator"
        ]

        for i, (name, desc, score) in enumerate(zip(feature_names, descriptions, normalized_scores)):
            # Add small random noise for realism, but keep it deterministic if seed set
            noise = random.uniform(-0.05, 0.05)
            final_score = max(0.0, min(1.0, score + noise))
            
            feature = OverlayFeature(
                feature_id=f"feat_{i}",
                importance_score=round(final_score, 3),
                description=desc
            )
            features.append(feature)
            heatmap_data[name] = round(final_score, 3)

        overlay = XAIOverlay(
            task_id=task_input.get("task_id", "default_task"),
            features=features,
            heatmap_data=heatmap_data
        )

        return asdict(overlay)

def generate_overlay(task_input: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to generate an overlay."""
    generator = RuleBasedXAIOverlayGenerator()
    return generator.generate_overlay(task_input)

def main():
    """Test the overlay generator."""
    test_input = {"difficulty": "medium", "task_id": "test_1"}
    result = generate_overlay(test_input)
    print("Generated Overlay:")
    print(result)

if __name__ == "__main__":
    main()
