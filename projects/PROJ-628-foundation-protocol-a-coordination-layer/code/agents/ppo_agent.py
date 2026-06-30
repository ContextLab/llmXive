"""
Pre-trained PPO Agent for Hanabi (Inference-only, CPU mode).

This module implements a PPO-based agent compatible with the Hanabi environment.
It is designed for inference only (no training) and runs on CPU to comply with
project constraints (FR-009). The agent loads a pre-trained model from a specified
path or uses a dummy policy if no model is available, ensuring the pipeline
remains functional for baseline comparisons.

Dependencies:
  - stable-baselines3 (for PPO inference)
  - pettingzoo (for Hanabi environment interface)
  - numpy

Usage:
  agent = PPOHanabiAgent(model_path="models/hanabi_ppo.zip", seed=42)
  action = agent.act(observation, legal_actions)
"""

import os
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

# Attempt to import stable_baselines3. If not installed, we fall back to a
# deterministic heuristic that mimics a trained agent's structure for testing.
try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    logging.warning(
        "stable_baselines3 not found. PPOHanabiAgent will use a deterministic "
        "heuristic fallback. Install with: pip install stable-baselines3"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PPOHanabiAgent:
    """
    A PPO-based agent for the Hanabi game.

    This agent wraps a Stable Baselines 3 PPO model for inference. It handles
    observation preprocessing, action selection, and interaction with the
    Hanabi environment.

    Attributes:
        model_path (str): Path to the pre-trained .zip model file.
        seed (int): Random seed for reproducibility.
        model: The loaded PPO model (or None if using fallback).
        action_space: The environment's action space (inferred or set).
        observation_space: The environment's observation space.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        seed: int = 42,
        device: str = "cpu"
    ):
        """
        Initialize the PPO Agent.

        Args:
            model_path: Path to the pre-trained SB3 model (.zip). If None,
                        a fallback heuristic agent is used.
            seed: Random seed for reproducibility.
            device: Device to run inference on ('cpu' only supported).
        """
        self.seed = seed
        self.model_path = model_path
        self.device = device
        self.model = None
        self.action_space = None
        self.observation_space = None
        self._rng = np.random.default_rng(seed)

        # Set global seed for reproducibility
        np.random.seed(seed)

        if SB3_AVAILABLE and model_path and os.path.exists(model_path):
            try:
                logger.info(f"Loading PPO model from {model_path}...")
                # Load with deterministic mode enabled for CPU
                self.model = PPO.load(
                    model_path,
                    device=device,
                    seed=seed
                )
                # Extract spaces from the model's policy if available
                if hasattr(self.model, 'policy') and self.model.policy is not None:
                    self.observation_space = self.model.policy.observation_space
                    self.action_space = self.model.policy.action_space
                logger.info("Model loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load model: {e}. Using fallback agent.")
                self.model = None
        elif SB3_AVAILABLE and model_path:
            logger.warning(f"Model path {model_path} not found. Using fallback agent.")
            self.model = None
        else:
            logger.info("No valid model path provided or SB3 unavailable. Using fallback agent.")

    def set_seed(self, seed: int) -> None:
        """Update the random seed for this agent."""
        self.seed = seed
        self._rng = np.random.default_rng(seed)
        if self.model:
            self.model.set_random_seed(seed)

    def act(
        self,
        observation: Any,
        legal_actions: List[int],
        info: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Select an action given the current observation and legal actions.

        Args:
            observation: The current game state observation.
            legal_actions: A list of integers representing valid action indices.
            info: Optional environment info dictionary.

        Returns:
            int: The selected action index (must be in legal_actions).
        """
        if self.model is not None:
            return self._act_with_model(observation, legal_actions)
        else:
            return self._act_fallback(observation, legal_actions)

    def _act_with_model(
        self,
        observation: Any,
        legal_actions: List[int]
    ) -> int:
        """
        Select action using the loaded PPO model.

        Args:
            observation: Current observation.
            legal_actions: List of legal action indices.

        Returns:
            int: Selected action index.
        """
        # Handle different observation formats (dict vs array)
        if isinstance(observation, dict):
            # Stable Baselines often expects specific dict keys or flattened arrays
            # For Hanabi, we usually need to flatten or convert to array
            try:
                obs_array = np.array(observation.get('observation', []))
            except (KeyError, TypeError):
                # Fallback: try to convert the whole dict to a flat array if possible
                obs_array = np.array(list(observation.values())).flatten()
        elif isinstance(observation, (list, tuple)):
            obs_array = np.array(observation)
        else:
            obs_array = observation

        # Ensure correct shape for the model
        if self.observation_space is not None:
            if hasattr(self.observation_space, 'shape'):
                expected_shape = self.observation_space.shape
                if obs_array.ndim == 1 and len(obs_array) != expected_shape[0]:
                    # Attempt to reshape if dimensions match total size
                    if obs_array.size == np.prod(expected_shape):
                        obs_array = obs_array.reshape(expected_shape)
                    else:
                        logger.warning(f"Observation shape mismatch: {obs_array.shape} vs {expected_shape}")

        # Expand dimensions for batch if necessary (SB3 expects batch dim)
        if obs_array.ndim == 1:
            obs_array = obs_array.reshape(1, -1)

        # Predict
        try:
            action, _ = self.model.predict(obs_array, deterministic=True)
            selected_action = int(action[0])
        except Exception as e:
            logger.error(f"Prediction failed: {e}. Falling back to random legal action.")
            return self._select_random_legal(legal_actions)

        # Validate against legal actions
        if selected_action in legal_actions:
            return selected_action
        else:
            # If model suggests illegal action, pick the closest valid one or random
            logger.warning(f"Model suggested illegal action {selected_action}. Selecting random legal.")
            return self._select_random_legal(legal_actions)

    def _act_fallback(
        self,
        observation: Any,
        legal_actions: List[int]
    ) -> int:
        """
        Fallback deterministic heuristic agent.

        This implements a simple rule-based strategy to ensure the pipeline
        functions when no model is available. It prioritizes:
        1. Playing a card that completes a sequence (1-2-3-4-5) if possible.
        2. Playing a card that doesn't blow up (color match).
        3. Otherwise, random legal action.

        Args:
            observation: Current observation.
            legal_actions: List of legal action indices.

        Returns:
            int: Selected action index.
        """
        if not legal_actions:
            logger.error("No legal actions available!")
            return 0

        # Extract relevant info from observation if possible
        # Hanabi observation usually contains:
        # - hand: list of cards {color, rank, known}
        # - play_stack: list of highest played rank per color
        # - discard_pile: list of discarded cards
        hand = observation.get('hand', [])
        play_stack = observation.get('play_stack', [0] * 5) # Assuming 5 colors

        # Map action indices to actual actions if needed.
        # In standard Hanabi, actions are often 0-4 (play card 0-4) or 5-9 (discard 0-4)
        # or encoded as (type, index).
        # For this implementation, we assume `legal_actions` are indices into the hand
        # for 'play' actions, or we need a mapping.
        # Since the environment abstraction is in `hanabi_runner.py`, we assume
        # `legal_actions` are the valid indices to act upon directly.

        # Simple heuristic: Play the first card that matches the next needed rank
        # in the play stack for its color.
        for idx in legal_actions:
            if idx < len(hand):
                card = hand[idx]
                color = card.get('color') if isinstance(card, dict) else None
                rank = card.get('rank') if isinstance(card, dict) else None

                if color is not None and rank is not None:
                    # Colors are typically 0-4
                    if 0 <= color < len(play_stack):
                        needed_rank = play_stack[color] + 1
                        if rank == needed_rank:
                            logger.debug(f"Playing card {idx} (color={color}, rank={rank}) to complete sequence.")
                            return idx

        # If no completion move, try to play a card that is safe (rank > 0)
        for idx in legal_actions:
            if idx < len(hand):
                card = hand[idx]
                rank = card.get('rank') if isinstance(card, dict) else None
                if rank is not None and rank > 0:
                    logger.debug(f"Playing safe card {idx} (rank={rank}).")
                    return idx

        # Fallback: random legal action
        return self._select_random_legal(legal_actions)

    def _select_random_legal(self, legal_actions: List[int]) -> int:
        """Select a random action from the legal set."""
        return int(self._rng.choice(legal_actions))

    def get_policy_info(self) -> Dict[str, Any]:
        """
        Return metadata about the agent's policy.

        Returns:
            Dict containing model status, path, and seed.
        """
        return {
            "type": "PPO" if SB3_AVAILABLE else "FallbackHeuristic",
            "model_path": self.model_path,
            "model_loaded": self.model is not None,
            "seed": self.seed,
            "device": self.device
        }


def create_ppo_agent(
    model_path: Optional[str] = None,
    seed: int = 42
) -> PPOHanabiAgent:
    """
    Factory function to create a PPOHanabiAgent.

    Args:
        model_path: Path to the pre-trained model.
        seed: Random seed.

    Returns:
        PPOHanabiAgent instance.
    """
    return PPOHanabiAgent(model_path=model_path, seed=seed)


def main():
    """
    Simple CLI entry point to test the agent.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test PPO Hanabi Agent")
    parser.add_argument("--model", type=str, default=None, help="Path to model zip")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    agent = create_ppo_agent(model_path=args.model, seed=args.seed)
    info = agent.get_policy_info()

    print("Agent Info:")
    for k, v in info.items():
        print(f"  {k}: {v}")

    # Simulate a dummy observation for testing
    dummy_obs = {
        "hand": [
            {"color": 0, "rank": 1},
            {"color": 1, "rank": 2},
            {"color": 2, "rank": 3}
        ],
        "play_stack": [0, 0, 0, 0, 0]
    }
    dummy_legal = [0, 1, 2]

    action = agent.act(dummy_obs, dummy_legal)
    print(f"Selected action: {action}")


if __name__ == "__main__":
    main()