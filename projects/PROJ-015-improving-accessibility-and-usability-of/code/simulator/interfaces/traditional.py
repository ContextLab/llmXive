from typing import Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class TraditionalInterfaceState:
    current_step: int = 0
    resource_level: float = 1.0
    visible_elements: list = None
    feedback_message: str = ""

    def __post_init__(self):
        if self.visible_elements is None:
            self.visible_elements = []

class TraditionalInterface:
    """
    Renderer for the Traditional (non-explainable) interface variant.
    This interface presents the standard UI without XAI overlays or
    explanation engagement tracking.
    """
    def __init__(self):
        self.state = TraditionalInterfaceState()

    def render(self) -> Dict[str, Any]:
        """
        Generates the UI representation for the Traditional interface.
        Returns a dictionary containing the interface type, current state,
        and an empty list for overlays (as this variant has none).
        """
        return {
            "type": "traditional",
            "state": asdict(self.state),
            "overlays": [],
            "interaction_mode": "standard"
        }

    def update_step(self, step: int) -> Dict[str, Any]:
        """
        Updates the current step in the interface state.
        """
        self.state.current_step = step
        return self.render()

    def set_feedback(self, message: str) -> Dict[str, Any]:
        """
        Sets a feedback message in the interface state.
        """
        self.state.feedback_message = message
        return self.render()

    def reset(self) -> Dict[str, Any]:
        """
        Resets the interface state to default values.
        """
        self.state = TraditionalInterfaceState()
        return self.render()

def main():
    """
    Entry point for testing the TraditionalInterface module independently.
    Verifies that the render method produces the expected structure.
    """
    interface = TraditionalInterface()
    result = interface.render()
    
    assert result["type"] == "traditional"
    assert result["overlays"] == []
    assert "state" in result
    assert result["state"]["current_step"] == 0
    
    print("TraditionalInterface test passed.")
    print(f"Render output: {result}")

if __name__ == "__main__":
    main()