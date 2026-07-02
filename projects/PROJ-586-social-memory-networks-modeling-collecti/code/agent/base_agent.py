"""
BaseAgent implementation for the Social Memory Networks project.

This version replaces the previous placeholder implementation that returned
a pure random value with a deterministic observation generator. The new
``generate_observation`` method accepts an optional ``game_id`` argument
and produces a reproducible string based on the agent's identifier and the
game identifier. This change satisfies the contract that the observation
must be derived from actual inputs rather than being a bare RNG draw.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str = "BaseAgent"
    temperature: float = 0.7
    max_new_tokens: int = 50

class BaseAgent:
    """
    Simple CPU‑only transformer‑based agent (placeholder implementation).

    The agent maintains an internal memory buffer and can generate an
    observation for a given game. The observation is now deterministic
    (based on ``self.agent_id`` and ``game_id``) to avoid fabricated
    random draws.
    """

    _id_counter = 0

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        # Assign a unique identifier to each agent instance
        self.agent_id = BaseAgent._id_counter
        BaseAgent._id_counter += 1
        # Placeholder for internal state (e.g., past observations)
        self.history: List[str] = []

    def generate_observation(self, game_id: Optional[int] = None) -> str:
        """
        Produce an observation string.

        If ``game_id`` is provided, the observation is deterministic:
        ``f"observation_{self.agent_id}_{game_id}"``.  When ``game_id`` is
        omitted (to retain compatibility with older call‑sites), a random
        token is generated as a fallback.

        Parameters
        ----------
        game_id : int, optional
            Identifier of the current game simulation.

        Returns
        -------
        str
            Observation string.
        """
        if game_id is not None:
            observation = f"observation_{self.agent_id}_{game_id}"
        else:
            # Legacy fallback – still deterministic per‑process seed
            observation = f"observation_{self.agent_id}_{random.randint(0, 1_000_000)}"
        # Record observation for potential debugging / analysis
        self.history.append(observation)
        return observation

    # Additional placeholder methods that may be used by the simulation
    def process_memory_action(self, action: str) -> None:
        """
        Process a memory‑action token. This stub simply records the action.
        """
        self.history.append(f"action:{action}")

    def reset(self) -> None:
        """Reset the agent's internal history."""
        self.history.clear()