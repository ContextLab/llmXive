from typing import Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class TraditionalInterfaceState:
    current_step: int = 0
    resource_level: float = 1.0

class TraditionalInterface:
    def __init__(self):
        self.state = TraditionalInterfaceState()

    def render(self) -> Dict[str, Any]:
        return {
            "type": "traditional",
            "state": asdict(self.state),
            "overlays": []
        }

def main():
    print("Traditional interface module loaded.")
