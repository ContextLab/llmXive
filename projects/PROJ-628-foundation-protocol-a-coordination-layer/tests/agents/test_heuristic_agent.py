"""
Tests for the heuristic Hanabi agent.
"""
import pytest
from agents.heuristic import HeuristicHanabiAgent, create_heuristic_agent


class TestHeuristicAgent:
    """Test suite for HeuristicHanabiAgent."""
    
    def test_agent_creation(self):
        """Test that agent can be created with valid parameters."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        assert agent.agent_id == 0
        assert agent.seed == 42
        assert agent.name == "HeuristicAgent-0"
        
    def test_agent_creation_no_seed(self):
        """Test agent creation without seed."""
        agent = create_heuristic_agent(agent_id=1)
        assert agent.agent_id == 1
        assert agent.seed is None
        
    def test_reset_with_seed(self):
        """Test that reset updates the seed."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        agent.reset(seed=123)
        assert agent.seed == 123
        
    def test_play_action(self):
        """Test that agent plays a card when playable cards exist."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        
        observation = {
            "hand": [
                {"color": "red", "rank": 1},
                {"color": "blue", "rank": 3}
            ],
            "playable_indices": [0],
            "fireworks": {"red": 2, "blue": 1},
            "discards": [],
            "hints_left": 3,
            "lives_left": 3,
            "other_agents_hand_info": []
        }
        
        action_type, card_idx = agent.get_action(observation)
        assert action_type == 0  # Play action
        assert card_idx == 0
        assert agent.stats["cards_played"] == 1
        
    def test_discard_action(self):
        """Test that agent discards the least valuable card."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        
        observation = {
            "hand": [
                {"color": "red", "rank": 5},  # High rank, low value
                {"color": "blue", "rank": 1}  # Low rank, high value
            ],
            "playable_indices": [],
            "fireworks": {"red": 2, "blue": 1},
            "discards": [],
            "hints_left": 3,
            "lives_left": 3,
            "other_agents_hand_info": []
        }
        
        action_type, card_idx = agent.get_action(observation)
        assert action_type == 1  # Discard action
        # Should discard the highest rank card (index 0)
        assert card_idx == 0
        assert agent.stats["cards_discarded"] == 1
        
    def test_hint_action_color(self):
        """Test that agent gives a color hint when beneficial."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        
        observation = {
            "hand": [
                {"color": "red", "rank": 5},
                {"color": "blue", "rank": 1}
            ],
            "playable_indices": [],
            "fireworks": {"red": 2, "blue": 1, "yellow": 0},
            "discards": [],
            "hints_left": 3,
            "lives_left": 3,
            "other_agents_hand_info": [
                {
                    "hand": [
                        {"color": "yellow", "rank": 1},  # Playable if hinted
                        {"color": "red", "rank": 3}
                    ],
                    "has_unknown_cards": True,
                    "known_colors": [],
                    "known_ranks": []
                }
            ]
        }
        
        action_type, target = agent.get_action(observation)
        # Should give a hint (type 2 = color hint)
        assert action_type == 2
        assert target == 0
        assert agent.stats["hints_given"] == 1
        
    def test_no_hint_when_no_lives(self):
        """Test that agent does not give hints when lives are low."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        
        observation = {
            "hand": [
                {"color": "red", "rank": 5}
            ],
            "playable_indices": [],
            "fireworks": {"red": 2},
            "discards": [],
            "hints_left": 3,
            "lives_left": 1,  # Only 1 life left
            "other_agents_hand_info": [
                {
                    "hand": [{"color": "red", "rank": 1}],
                    "has_unknown_cards": True,
                    "known_colors": [],
                    "known_ranks": []
                }
            ]
        }
        
        action_type, _ = agent.get_action(observation)
        # Should not give hint, should discard instead
        assert action_type == 1
        
    def test_card_value_calculation(self):
        """Test card value calculation logic."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        
        # Low rank card with incomplete color should have high value
        card1 = {"color": "red", "rank": 1}
        fireworks = {"red": 2}
        discards = []
        value1 = agent._calculate_card_value(card1, fireworks, discards, 5)
        
        # High rank card should have lower value
        card2 = {"color": "red", "rank": 5}
        value2 = agent._calculate_card_value(card2, fireworks, discards, 5)
        
        assert value1 > value2
        
    def test_card_value_zero_when_discarded(self):
        """Test that discarded cards have zero value."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        
        card = {"color": "red", "rank": 1}
        fireworks = {"red": 2}
        discards = [{"color": "red", "rank": 1}]  # All copies discarded
        
        value = agent._calculate_card_value(card, fireworks, discards, 5)
        assert value == 0.0
        
    def test_state_save_load(self):
        """Test checkpoint save and load functionality."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        
        # Perform some actions
        observation = {
            "hand": [{"color": "red", "rank": 5}],
            "playable_indices": [],
            "fireworks": {"red": 2},
            "discards": [],
            "hints_left": 3,
            "lives_left": 3,
            "other_agents_hand_info": []
        }
        agent.get_action(observation)
        
        # Save state
        state = agent.get_state()
        assert state["agent_id"] == 0
        assert state["seed"] == 42
        assert state["stats"]["cards_discarded"] == 1
        assert "hints_given_history" in state
        
        # Create new agent and load state
        new_agent = create_heuristic_agent(agent_id=99, seed=99)
        new_agent.load_state(state)
        
        assert new_agent.agent_id == 0
        assert new_agent.seed == 42
        assert new_agent.stats["cards_discarded"] == 1
        
    def test_receive_hint(self):
        """Test hint reception updates stats and history."""
        agent = create_heuristic_agent(agent_id=0, seed=42)
        
        hint = {
            "type": "color",
            "color": "red",
            "target_indices": [0, 2]
        }
        
        agent.receive_hint(hint)
        assert agent.stats["hints_used"] == 1
        assert len(agent.hints_given_history) == 1
        assert agent.hints_given_history[0] == hint