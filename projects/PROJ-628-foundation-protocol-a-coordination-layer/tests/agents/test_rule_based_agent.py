"""
Tests for the rule-based Hanabi agent.
"""
import pytest
from agents.rule_based import RuleBasedHanabiAgent, create_rule_based_agent


class TestRuleBasedAgent:
    """Test suite for RuleBasedHanabiAgent."""
    
    def test_agent_creation(self):
        """Test that agent can be created with valid parameters."""
        agent = create_rule_based_agent(agent_id=0, seed=42)
        assert agent.agent_id == 0
        assert agent.seed == 42
        assert agent.name == "RuleBasedAgent-0"
        
    def test_agent_creation_no_seed(self):
        """Test agent creation without seed."""
        agent = create_rule_based_agent(agent_id=1)
        assert agent.agent_id == 1
        assert agent.seed is None
        
    def test_reset_with_seed(self):
        """Test that reset updates the seed."""
        agent = create_rule_based_agent(agent_id=0, seed=42)
        agent.reset(seed=123)
        assert agent.seed == 123
        
    def test_play_action(self):
        """Test that agent plays a card when playable cards exist."""
        agent = create_rule_based_agent(agent_id=0, seed=42)
        
        observation = {
            "hand": [
                {"color": "red", "rank": 1},
                {"color": "blue", "rank": 3}
            ],
            "playable_indices": [0],
            "fireworks": {"red": 2, "blue": 1},
            "hints_left": 3,
            "lives_left": 3,
            "other_agents_hand_info": []
        }
        
        action_type, card_idx = agent.get_action(observation)
        assert action_type == 0  # Play action
        assert card_idx == 0
        assert agent.stats["cards_played"] == 1
        
    def test_discard_action(self):
        """Test that agent discards when no playable cards exist."""
        agent = create_rule_based_agent(agent_id=0, seed=42)
        
        observation = {
            "hand": [
                {"color": "red", "rank": 5},  # High rank, good to discard
                {"color": "blue", "rank": 1}
            ],
            "playable_indices": [],
            "fireworks": {"red": 2, "blue": 1},
            "hints_left": 3,
            "lives_left": 3,
            "other_agents_hand_info": []
        }
        
        action_type, card_idx = agent.get_action(observation)
        assert action_type == 1  # Discard action
        # Should discard the highest rank card (index 0)
        assert card_idx == 0
        assert agent.stats["cards_discarded"] == 1
        
    def test_hint_action(self):
        """Test that agent gives a hint when appropriate."""
        agent = create_rule_based_agent(agent_id=0, seed=42)
        
        observation = {
            "hand": [
                {"color": "red", "rank": 5},
                {"color": "blue", "rank": 1}
            ],
            "playable_indices": [],
            "fireworks": {"red": 2, "blue": 1},
            "hints_left": 3,
            "lives_left": 3,
            "other_agents_hand_info": [
                {
                    "has_unknown_cards": True,
                    "known_colors": ["red"],
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
        agent = create_rule_based_agent(agent_id=0, seed=42)
        
        observation = {
            "hand": [
                {"color": "red", "rank": 5}
            ],
            "playable_indices": [],
            "fireworks": {"red": 2},
            "hints_left": 3,
            "lives_left": 1,  # Only 1 life left
            "other_agents_hand_info": [
                {
                    "has_unknown_cards": True,
                    "known_colors": ["red"],
                    "known_ranks": []
                }
            ]
        }
        
        action_type, _ = agent.get_action(observation)
        # Should not give hint, should discard instead
        assert action_type == 1
        
    def test_state_save_load(self):
        """Test checkpoint save and load functionality."""
        agent = create_rule_based_agent(agent_id=0, seed=42)
        
        # Perform some actions to change stats
        observation = {
            "hand": [{"color": "red", "rank": 5}],
            "playable_indices": [],
            "fireworks": {"red": 2},
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
        
        # Create new agent and load state
        new_agent = create_rule_based_agent(agent_id=99, seed=99)
        new_agent.load_state(state)
        
        assert new_agent.agent_id == 0
        assert new_agent.seed == 42
        assert new_agent.stats["cards_discarded"] == 1
        
    def test_receive_hint(self):
        """Test hint reception updates stats."""
        agent = create_rule_based_agent(agent_id=0, seed=42)
        
        hint = {
            "type": "color",
            "color": "red",
            "target_indices": [0, 2]
        }
        
        agent.receive_hint(hint)
        assert agent.stats["hints_used"] == 1
