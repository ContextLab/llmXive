"""
Heuristic agent for Hanabi. Implements a more sophisticated policy than the
rule-based agent, using domain knowledge about card values, hint efficiency,
and team coordination.

This agent uses a scoring system to evaluate actions and choose the best one.
"""
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HeuristicHanabiAgent:
    """
    A heuristic-based agent for Hanabi that uses card scoring and
    strategic hint-giving to maximize team score.
    
    Key heuristics:
    1. Card value scoring based on rank and color availability
    2. Hint efficiency: prioritize hints that reveal playable cards
    3. Safety-first: avoid discarding potentially playable cards
    4. Coordination: remember hints given and avoid redundant hints
    """
    
    def __init__(self, agent_id: int, seed: Optional[int] = None):
        self.agent_id = agent_id
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.name = f"HeuristicAgent-{agent_id}"
        self.stats = {
            "cards_played": 0,
            "cards_discarded": 0,
            "hints_used": 0,
            "hints_given": 0,
            "redundant_hints_avoided": 0
        }
        # Track hints given to avoid redundancy
        self.hints_given_history: List[Dict[str, Any]] = []
        
    def reset(self, seed: Optional[int] = None):
        """Reset agent state for a new episode."""
        if seed is not None:
            self.seed = seed
            self.rng = np.random.default_rng(seed)
        self.stats = {
            "cards_played": 0,
            "cards_discarded": 0,
            "hints_used": 0,
            "hints_given": 0,
            "redundant_hints_avoided": 0
        }
        self.hints_given_history = []
        
    def _calculate_card_value(self, card: Dict[str, Any], fireworks: Dict[str, int], 
                             discards: List[Dict[str, Any]], hand_size: int) -> float:
        """
        Calculate the value of keeping a card.
        
        Higher value = more important to keep.
        Factors:
        - Rank: Lower ranks are more valuable early game
        - Color availability: Colors with lower fireworks progress are more valuable
        - Discard history: Cards already discarded are less valuable
        - Hand position: Cards closer to being played are more valuable
        """
        color = card.get("color")
        rank = card.get("rank", 0)
        
        # Base value from rank (1 is most valuable, 5 is least)
        base_value = 6 - rank
        
        # Color progress multiplier
        color_progress = fireworks.get(color, 0)
        if color_progress == 5:
            # Color is complete, card is worthless
            return 0.0
        elif color_progress == 0:
            # Color hasn't started, card is very valuable
            color_multiplier = 2.0
        else:
            # Intermediate progress
            color_multiplier = 1.5 - (color_progress * 0.1)
        
        # Discard penalty
        is_discarded = any(d.get("color") == color and d.get("rank") == rank 
                         for d in discards)
        if is_discarded:
            return 0.0  # Card cannot be played if all copies are discarded
        
        # Position bonus (cards that can be played sooner are more valuable)
        position_bonus = (hand_size - 1) * 0.1
        
        total_value = base_value * color_multiplier + position_bonus
        return total_value
        
    def _calculate_hint_value(self, target_agent_idx: int, target_hand: List[Dict[str, Any]], 
                             fireworks: Dict[str, int], hint_type: str) -> Tuple[float, str]:
        """
        Calculate the value of giving a specific hint.
        
        Returns:
            Tuple of (hint_value, hint_detail)
        """
        if not target_hand:
            return 0.0, ""
        
        # Count how many cards would be revealed as playable
        playable_count = 0
        useful_cards = 0
        
        for card in target_hand:
            color = card.get("color")
            rank = card.get("rank", 0)
            
            # Check if this card would be playable if hinted
            if hint_type == "color":
                next_rank = fireworks.get(color, 0) + 1
                if rank == next_rank:
                    playable_count += 1
                elif rank > next_rank:
                    useful_cards += 1
            elif hint_type == "rank":
                # Count cards of this rank
                pass  # Simplified for now
        
        # Hint value is proportional to playable cards revealed
        hint_value = playable_count * 10.0 + useful_cards * 2.0
        
        # Bonus for hinting colors that are not yet started
        if hint_type == "color":
            for card in target_hand:
                color = card.get("color")
                if fireworks.get(color, 0) == 0:
                    hint_value += 5.0  # Bonus for starting a new color
        
        return hint_value, f"{hint_type}_hint"
        
    def get_action(
        self, 
        observation: Dict[str, Any],
        info: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, int]:
        """
        Decide action using heuristic scoring.
        
        Args:
            observation: Dict containing hand info, fireworks, discards, hints, etc.
                        
        Returns:
            Tuple (action_type, card_index/target_agent)
        """
        hand = observation.get("hand", [])
        playable_indices = observation.get("playable_indices", [])
        fireworks = observation.get("fireworks", {})
        discards = observation.get("discards", [])
        hints_left = observation.get("hints_left", 0)
        lives_left = observation.get("lives_left", 3)
        other_agents = observation.get("other_agents_hand_info", [])
        
        # Strategy 1: Play any playable card (highest priority)
        if playable_indices:
            # Among playable cards, prefer the one with highest value
            best_idx = playable_indices[0]
            best_value = -float('inf')
            
            for idx in playable_indices:
                if idx < len(hand):
                    card_value = self._calculate_card_value(
                        hand[idx], fireworks, discards, len(hand)
                    )
                    if card_value > best_value:
                        best_value = card_value
                        best_idx = idx
            
            logger.debug(f"Agent {self.agent_id}: Playing card at index {best_idx} (value={best_value:.2f})")
            self.stats["cards_played"] += 1
            return (0, best_idx)
        
        # Strategy 2: Give a hint if beneficial
        if hints_left > 0 and lives_left > 1 and other_agents:
            best_hint_value = -float('inf')
            best_hint_action = None
            
            for i, agent_info in enumerate(other_agents):
                target_hand = agent_info.get("hand", [])
                if not target_hand:
                    continue
                
                # Evaluate color hints
                color_counts = {}
                for card in target_hand:
                    color = card.get("color")
                    color_counts[color] = color_counts.get(color, 0) + 1
                
                for color, count in color_counts.items():
                    hint_val, _ = self._calculate_hint_value(i, target_hand, fireworks, "color")
                    if hint_val > best_hint_value:
                        best_hint_value = hint_val
                        best_hint_action = (2, i)  # Give color hint
                
                # Evaluate rank hints (simplified)
                rank_counts = {}
                for card in target_hand:
                    rank = card.get("rank", 0)
                    rank_counts[rank] = rank_counts.get(rank, 0) + 1
                
                for rank, count in rank_counts.items():
                    hint_val, _ = self._calculate_hint_value(i, target_hand, fireworks, "rank")
                    if hint_val > best_hint_value:
                        best_hint_value = hint_val
                        best_hint_action = (3, i)  # Give rank hint
            
            # Only give hint if it has positive value
            if best_hint_value > 0 and best_hint_action:
                logger.debug(f"Agent {self.agent_id}: Giving hint (value={best_hint_value:.2f})")
                self.stats["hints_given"] += 1
                return best_hint_action
            else:
                self.stats["redundant_hints_avoided"] += 1
        
        # Strategy 3: Discard the least valuable card
        if hand:
            discard_candidates = []
            for i, card in enumerate(hand):
                card_value = self._calculate_card_value(
                    card, fireworks, discards, len(hand)
                )
                # Add small random noise for tie-breaking
                noise = self.rng.uniform(-0.01, 0.01)
                discard_candidates.append((card_value + noise, i))
            
            # Sort by value (ascending) - lowest value first
            discard_candidates.sort(key=lambda x: x[0])
            card_idx = discard_candidates[0][1]
            
            logger.debug(f"Agent {self.agent_id}: Discarding card at index {card_idx} (value={discard_candidates[0][0]:.2f})")
            self.stats["cards_discarded"] += 1
            return (1, card_idx)
        
        # Fallback
        logger.warning(f"Agent {self.agent_id}: No valid action found, defaulting to discard index 0")
        return (1, 0)
        
    def receive_hint(self, hint: Dict[str, Any]):
        """Process a hint received from another agent."""
        logger.debug(f"Agent {self.agent_id}: Received hint {hint}")
        self.stats["hints_used"] += 1
        self.hints_given_history.append(hint)
        
    def get_state(self) -> Dict[str, Any]:
        """Return current agent state for checkpointing."""
        return {
            "agent_id": self.agent_id,
            "seed": self.seed,
            "stats": self.stats,
            "hints_given_history": self.hints_given_history
        }
        
    def load_state(self, state: Dict[str, Any]):
        """Load agent state from checkpoint."""
        self.agent_id = state.get("agent_id", self.agent_id)
        self.seed = state.get("seed", self.seed)
        self.stats = state.get("stats", self.stats)
        self.hints_given_history = state.get("hints_given_history", [])
        if self.seed is not None:
            self.rng = np.random.default_rng(self.seed)


def create_heuristic_agent(agent_id: int, seed: Optional[int] = None) -> HeuristicHanabiAgent:
    """Factory function to create a heuristic agent."""
    return HeuristicHanabiAgent(agent_id=agent_id, seed=seed)


def main():
    """Demo of the heuristic agent."""
    logging.basicConfig(level=logging.INFO)
    
    # Create a mock observation for testing
    mock_observation = {
        "hand": [
            {"color": "red", "rank": 1},
            {"color": "blue", "rank": 3},
            {"color": "green", "rank": 5}
        ],
        "playable_indices": [],
        "fireworks": {"red": 2, "blue": 1, "green": 1, "yellow": 1, "white": 1},
        "discards": [],
        "hints_left": 3,
        "lives_left": 3,
        "other_agents_hand_info": [
            {
                "hand": [
                    {"color": "red", "rank": 3},
                    {"color": "yellow", "rank": 1}
                ],
                "has_unknown_cards": True,
                "known_colors": [],
                "known_ranks": []
            }
        ]
    }
    
    agent = create_heuristic_agent(agent_id=0, seed=42)
    action = agent.get_action(mock_observation)
    print(f"Heuristic agent action: {action}")
    print(f"Agent stats: {agent.stats}")


if __name__ == "__main__":
    main()
