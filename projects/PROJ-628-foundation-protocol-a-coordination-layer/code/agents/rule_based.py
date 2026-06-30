"""
Rule-based agent for Hanabi. Implements a deterministic policy based on
simple heuristics (play playable cards, discard unplayable ones).
This agent serves as a baseline for comparison with PPO and heuristic agents.
"""
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class RuleBasedHanabiAgent:
    """
    A deterministic rule-based agent for the Hanabi environment.
    
    Strategy:
    1. If a playable card is in hand (matches the next needed color/rank), play it.
    2. If no playable card, discard the card with the lowest "value" (highest rank, 
       or oldest if ranks equal) to save better cards for later.
    """
    
    def __init__(self, agent_id: int, seed: Optional[int] = None):
        self.agent_id = agent_id
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.name = f"RuleBasedAgent-{agent_id}"
        self.stats = {
            "cards_played": 0,
            "cards_discarded": 0,
            "hints_used": 0,
            "hints_given": 0
        }
        
    def reset(self, seed: Optional[int] = None):
        """Reset agent state for a new episode."""
        if seed is not None:
            self.seed = seed
            self.rng = np.random.default_rng(seed)
        self.stats = {
            "cards_played": 0,
            "cards_discarded": 0,
            "hints_used": 0,
            "hints_given": 0
        }
        
    def get_action(
        self, 
        observation: Dict[str, Any],
        info: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, int]:
        """
        Decide action based on current observation.
        
        Args:
            observation: Dict containing 'hand' (list of cards) and 
                        'playable_indices' (list of indices of playable cards)
                        'fireworks' (dict of color -> next rank needed)
                        'discards' (list of discarded cards)
                        'hints_left' (int)
                        'lives_left' (int)
                        'other_agents_hand_info' (list of dicts with known card info)
                        
        Returns:
            Tuple (action_type, card_index)
            action_type: 0=play, 1=discard, 2=give_hint_color, 3=give_hint_rank
            card_index: index of card to play/discard or target agent index for hint
        """
        hand = observation.get("hand", [])
        playable_indices = observation.get("playable_indices", [])
        fireworks = observation.get("fireworks", {})
        hints_left = observation.get("hints_left", 0)
        lives_left = observation.get("lives_left", 3)
        
        # Strategy 1: Play any playable card
        if playable_indices:
            # Play the first playable card (deterministic)
            card_idx = playable_indices[0]
            logger.debug(f"Agent {self.agent_id}: Playing card at index {card_idx}")
            self.stats["cards_played"] += 1
            return (0, card_idx)
        
        # Strategy 2: If no playable cards, check if we can give a hint
        # Only give hints if we have hints left and lives are safe
        if hints_left > 0 and lives_left > 1:
            other_agents = observation.get("other_agents_hand_info", [])
            if other_agents:
                # Find an agent with unknown cards
                for i, agent_info in enumerate(other_agents):
                    if agent_info.get("has_unknown_cards", False):
                        # Give a hint about a color that appears in their hand
                        known_colors = agent_info.get("known_colors", [])
                        if known_colors:
                            # Pick the first known color to hint
                            target_agent = i
                            hint_color = known_colors[0]
                            logger.debug(
                                f"Agent {self.agent_id}: Giving hint color {hint_color} to agent {target_agent}"
                            )
                            self.stats["hints_given"] += 1
                            return (2, target_agent)
        
        # Strategy 3: Discard the least valuable card
        # Priority: discard highest rank cards first, then oldest cards
        if hand:
            # Calculate "value" for each card (higher rank = lower value for keeping)
            discard_candidates = []
            for i, card in enumerate(hand):
                rank = card.get("rank", 0)  # 1-5, higher is worse to keep
                # Add some randomness to break ties deterministically based on seed
                value = rank + (i * 0.01)
                discard_candidates.append((value, i))
            
            # Sort by value (ascending) - lowest value (highest rank) first
            discard_candidates.sort(key=lambda x: x[0])
            card_idx = discard_candidates[0][1]
            
            logger.debug(f"Agent {self.agent_id}: Discarding card at index {card_idx}")
            self.stats["cards_discarded"] += 1
            return (1, card_idx)
        
        # Fallback (should not happen in normal game)
        logger.warning(f"Agent {self.agent_id}: No valid action found, defaulting to discard index 0")
        return (1, 0)
        
    def receive_hint(self, hint: Dict[str, Any]):
        """Process a hint received from another agent."""
        logger.debug(f"Agent {self.agent_id}: Received hint {hint}")
        self.stats["hints_used"] += 1
        
    def get_state(self) -> Dict[str, Any]:
        """Return current agent state for checkpointing."""
        return {
            "agent_id": self.agent_id,
            "seed": self.seed,
            "stats": self.stats
        }
        
    def load_state(self, state: Dict[str, Any]):
        """Load agent state from checkpoint."""
        self.agent_id = state.get("agent_id", self.agent_id)
        self.seed = state.get("seed", self.seed)
        self.stats = state.get("stats", self.stats)
        if self.seed is not None:
            self.rng = np.random.default_rng(self.seed)


def create_rule_based_agent(agent_id: int, seed: Optional[int] = None) -> RuleBasedHanabiAgent:
    """Factory function to create a rule-based agent."""
    return RuleBasedHanabiAgent(agent_id=agent_id, seed=seed)


def main():
    """Demo of the rule-based agent."""
    logging.basicConfig(level=logging.INFO)
    
    # Create a mock observation for testing
    mock_observation = {
        "hand": [
            {"color": "red", "rank": 1},
            {"color": "blue", "rank": 3},
            {"color": "green", "rank": 5}
        ],
        "playable_indices": [],  # No playable cards
        "fireworks": {"red": 2, "blue": 1, "green": 1, "yellow": 1, "white": 1},
        "hints_left": 3,
        "lives_left": 3,
        "other_agents_hand_info": [
            {
                "has_unknown_cards": True,
                "known_colors": ["red", "yellow"],
                "known_ranks": []
            }
        ]
    }
    
    agent = create_rule_based_agent(agent_id=0, seed=42)
    action = agent.get_action(mock_observation)
    print(f"Agent action: {action}")
    print(f"Agent stats: {agent.stats}")


if __name__ == "__main__":
    main()
