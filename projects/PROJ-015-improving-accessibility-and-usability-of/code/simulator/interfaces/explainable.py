"""
ExplainableInterface renderer for the gene regulation usability study.

Implements rule-based XAI overlay logic to visualize decision factors
during task execution. This renderer extends the TraditionalInterface
by adding overlay elements based on task difficulty and model confidence.
"""
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Import from project API surface
from utils.logger import get_logger
from utils.seed import set_seed, seeded_generator
from config.settings import get_settings

logger = get_logger(__name__)


@dataclass
class XAIOverlay:
    """Represents a single XAI overlay element."""
    element_id: str
    type: str  # 'heatmap', 'bar', 'text', 'highlight'
    position: Tuple[float, float]  # (x, y) normalized 0-1
    size: Tuple[float, float]  # (width, height) normalized
    opacity: float  # 0.0 to 1.0
    color: str  # Hex color code
    label: str
    value: float
    confidence: float
    rule_applied: str

@dataclass
class ExplainableInterfaceState:
    """State of the explainable interface for a given task."""
    session_id: str
    task_id: str
    interface_type: str = "explainable"
    overlays: List[XAIOverlay] = None
    base_task_difficulty: float = 0.0
    model_confidence: float = 0.0
    explanation_generated: bool = False

    def __post_init__(self):
        if self.overlays is None:
            self.overlays = []

class ExplainableInterface:
    """
    Renderer for the Explainable Interface variant with XAI overlays.
    
    This class generates UI states that include rule-based XAI overlays
    based on task difficulty and simulated model confidence.
    
    Rules:
    - Low difficulty (< 0.3): Simple text explanation, low opacity
    - Medium difficulty (0.3 - 0.7): Heatmap + text, medium opacity
    - High difficulty (> 0.7): Full heatmap + confidence bars + detailed text
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the ExplainableInterface.
        
        Args:
            seed: Optional random seed for reproducibility.
        """
        self.seed = seed if seed is not None else get_settings().random_seed
        set_seed(self.seed)
        self.generator = seeded_generator(self.seed)
        logger.info(f"Initialized ExplainableInterface with seed={self.seed}")

    def _calculate_overlay_opacity(self, difficulty: float, confidence: float) -> float:
        """
        Calculate overlay opacity based on task difficulty and model confidence.
        
        Rule: Higher difficulty and lower confidence -> higher opacity to draw attention.
        """
        base_opacity = 0.3
        difficulty_factor = difficulty * 0.4
        confidence_factor = (1.0 - confidence) * 0.3
        opacity = min(1.0, base_opacity + difficulty_factor + confidence_factor)
        return round(opacity, 2)

    def _generate_heatmap_overlay(self, task_id: str, difficulty: float, confidence: float) -> XAIOverlay:
        """Generate a heatmap overlay element."""
        opacity = self._calculate_overlay_opacity(difficulty, confidence)
        # Position based on task ID hash for determinism
        pos_x = (hash(task_id) % 100) / 100.0
        pos_y = (hash(task_id + "y") % 100) / 100.0
        
        return XAIOverlay(
            element_id=f"heatmap_{task_id}",
            type="heatmap",
            position=(pos_x, pos_y),
            size=(0.4, 0.4),
            opacity=opacity,
            color="#FF5733" if difficulty > 0.5 else "#33FF57",
            label="Key Decision Factors",
            value=difficulty,
            confidence=confidence,
            rule_applied="difficulty_heatmap"
        )

    def _generate_confidence_bar(self, task_id: str, confidence: float) -> XAIOverlay:
        """Generate a confidence bar overlay element."""
        return XAIOverlay(
            element_id=f"conf_bar_{task_id}",
            type="bar",
            position=(0.1, 0.85),
            size=(0.3, 0.1),
            opacity=0.8,
            color="#3366FF",
            label=f"Model Confidence: {confidence:.1%}",
            value=confidence,
            confidence=confidence,
            rule_applied="confidence_display"
        )

    def _generate_text_explanation(self, task_id: str, difficulty: float, confidence: float) -> XAIOverlay:
        """Generate a text explanation overlay element."""
        if difficulty < 0.3:
            text = "Simple task. Primary factor: Base gene expression."
        elif difficulty < 0.7:
            text = "Moderate complexity. Consider interaction effects between gene A and B."
        else:
            text = "High complexity. Multiple regulatory pathways active. Review all confidence scores."
        
        return XAIOverlay(
            element_id=f"text_{task_id}",
            type="text",
            position=(0.1, 0.1),
            size=(0.8, 0.15),
            opacity=0.9,
            color="#000000",
            label=text,
            value=difficulty,
            confidence=confidence,
            rule_applied="text_explanation_by_difficulty"
        )

    def render_task(self, session_id: str, task_id: str, difficulty: float, confidence: float) -> Dict[str, Any]:
        """
        Render the explainable interface for a specific task.
        
        Args:
            session_id: The current session identifier.
            task_id: The specific task identifier.
            difficulty: Task difficulty score (0.0 to 1.0).
            confidence: Model confidence score (0.0 to 1.0).
        
        Returns:
            A dictionary representing the rendered UI state with XAI overlays.
        """
        # Validate inputs
        if not 0.0 <= difficulty <= 1.0:
            raise ValueError(f"Difficulty must be between 0.0 and 1.0, got {difficulty}")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {confidence}")

        logger.debug(f"Rendering explainable interface for session={session_id}, task={task_id}")

        overlays: List[XAIOverlay] = []
        
        # Always add text explanation
        overlays.append(self._generate_text_explanation(task_id, difficulty, confidence))
        
        # Add heatmap for medium/high difficulty
        if difficulty >= 0.3:
            overlays.append(self._generate_heatmap_overlay(task_id, difficulty, confidence))
        
        # Add confidence bar for all tasks
        overlays.append(self._generate_confidence_bar(task_id, confidence))

        state = ExplainableInterfaceState(
            session_id=session_id,
            task_id=task_id,
            base_task_difficulty=difficulty,
            model_confidence=confidence,
            overlays=overlays,
            explanation_generated=True
        )

        # Convert to dictionary for serialization
        result = asdict(state)
        logger.info(f"Rendered explainable interface with {len(overlays)} overlays")
        return result

    def get_interface_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the explainable interface implementation.
        
        Returns:
            Dictionary containing interface type and rule descriptions.
        """
        return {
            "interface_type": "explainable",
            "version": "1.0.0",
            "xai_rules": [
                "difficulty_heatmap: Shows heatmap intensity based on task difficulty",
                "confidence_display: Visual bar showing model confidence score",
                "text_explanation_by_difficulty: Dynamic text explanation based on difficulty level"
            ],
            "overlay_types": ["heatmap", "bar", "text", "highlight"]
        }

def main():
    """
    Main entry point for testing the ExplainableInterface.
    Generates a sample render and saves it to data/processed/.
    """
    logger.info("Starting ExplainableInterface test run")
    
    # Initialize
    interface = ExplainableInterface(seed=42)
    
    # Simulate a task
    session_id = "test_session_001"
    task_id = "task_gene_regulation_001"
    difficulty = 0.65  # Medium-high difficulty
    confidence = 0.78  # Moderate confidence
    
    # Render
    result = interface.render_task(session_id, task_id, difficulty, confidence)
    
    # Save to data/processed/
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"xai_render_{task_id}.json"
    
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Successfully rendered explainable interface to {output_file}")
    print(f"Output written to: {output_file}")
    
    # Print metadata
    metadata = interface.get_interface_metadata()
    print("\nInterface Metadata:")
    print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    main()
