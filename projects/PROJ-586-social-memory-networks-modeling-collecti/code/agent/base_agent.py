"""
BaseAgent abstraction for the Social Memory Networks project.

The original implementation depended on the real ``torch`` library.
To keep the repository lightweight and runnable on the CI platform (which
does not have PyTorch installed), the import is now guarded with a fallback
to the lightweight stub defined in ``code/torch/__init__.py``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Torch import – use the stub if the real package is unavailable.
# --------------------------------------------------------------------------- #
try:  # pragma: no cover
    import torch  # type: ignore
except Exception:  # pragma: no cover
    # The stub lives in the project under ``code/torch`` and will be found
    # because the repository root is added to ``sys.path`` during execution.
    from torch import *  # type: ignore  # noqa: F403,F401

# --------------------------------------------------------------------------- #
# Configuration dataclass used to initialise agents.
# --------------------------------------------------------------------------- #
@dataclass
class AgentConfig:
    """
    Configuration for an individual agent.

    Attributes
    ----------
    agent_id: Unique identifier for the agent.
    temperature: Sampling temperature for language‑model generation.
    max_length: Maximum number of tokens generated per turn.
    """
    agent_id: int
    temperature: float = 0.7
    max_length: int = 128

# --------------------------------------------------------------------------- #
# Simple in‑memory representation of an agent.
# --------------------------------------------------------------------------- #
@dataclass
class BaseAgent:
    """
    Minimal agent implementation that does **not** rely on heavy neural‑network
    libraries.  It provides the public API used by the experiment runner
    (`run_experiment.py`) and the unit tests.

    The agent stores a short “memory” list of strings.  In a full implementation
    this would be a transformer‑based language model; here we use random text
    generation to keep the runtime and dependency footprint small.
    """
    config: AgentConfig
    memory: List[str] = field(default_factory=list)

    def generate_observation(self) -> str:
        """
        Produce a pseudo‑observation for the current turn.  The content is
        randomly chosen from a short list of placeholder sentences.
        """
        observations = [
            "Agent sees a red ball.",
            "Agent hears a distant bell.",
            "Agent feels a gentle breeze.",
            "Agent notices a flashing light.",
            "Agent recalls a previous interaction.",
        ]
        return random.choice(observations)

    def act(self, observation: str) -> str:
        """
        Process an observation and produce an action string.  The action is a
        deterministic transformation that includes the agent's identifier,
        which makes later analysis (e.g., specialization) possible.
        """
        action = f"agent_{self.config.agent_id}_responds_to_{observation.replace(' ', '_')}"
        # Store the interaction in the agent's memory.
        self.memory.append(action)
        return action

    def reset_memory(self) -> None:
        """Clear the internal memory – used between games."""
        self.memory.clear()
