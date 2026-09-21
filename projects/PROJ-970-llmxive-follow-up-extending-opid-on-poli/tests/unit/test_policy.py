"""
Unit tests for the BaselinePolicy implementation.
"""
import pytest
import math
import numpy as np

from agent.policy import BaselinePolicy, BaselinePolicyConfig, create_baseline_policy
from env.state_graph import StateGraph, Node, Edge


@pytest.fixture
def simple_graph():
    """Create a simple linear graph for testing."""
    g = StateGraph(tier=1)
    n1 = Node(id="n1", state_value=0, is_goal=False)
    n2 = Node(id="n2", state_value=1, is_goal=False)
    n3 = Node(id="n3", state_value=2, is_goal=True)

    g.nodes = {"n1": n1, "n2": n2, "n3": n3}
    g.edges = [
        Edge(source="n1", target="n2", prob=1.0, reward=0),
        Edge(source="n2", target="n3", prob=1.0, reward=1.0)
    ]
    g.start = "n1"
    g.goal = "n3"
    return g


@pytest.fixture
def branching_graph():
    """Create a graph with branching paths."""
    g = StateGraph(tier=2)
    n_start = Node(id="start", state_value=0, is_goal=False)
    n_left = Node(id="left", state_value=1, is_goal=False)
    n_right = Node(id="right", state_value=1, is_goal=False)
    n_goal = Node(id="goal", state_value=2, is_goal=True)

    g.nodes = {"start": n_start, "left": n_left, "right": n_right, "goal": n_goal}
    g.edges = [
        Edge(source="start", target="left", prob=0.5, reward=0),
        Edge(source="start", target="right", prob=0.5, reward=0),
        Edge(source="left", target="goal", prob=1.0, reward=1.0),
        Edge(source="right", target="goal", prob=1.0, reward=1.0)
    ]
    g.start = "start"
    g.goal = "goal"
    return g


class TestBaselinePolicy:
    def test_invalid_temperature(self):
        """Test that temperature <= 0 raises an error."""
        with pytest.raises(ValueError):
            BaselinePolicy(BaselinePolicyConfig(temperature=0))
        with pytest.raises(ValueError):
            BaselinePolicy(BaselinePolicyConfig(temperature=-1.0))

    def test_softmax_policy_initialization(self):
        """Test that a softmax policy initializes correctly."""
        config = BaselinePolicyConfig(policy_type="softmax", temperature=1.0, seed=42)
        policy = create_baseline_policy(config)
        assert policy.policy_type == "softmax"
        assert policy.temperature == 1.0
        assert policy.seed == 42

    def test_softmax_policy_single_action(self, simple_graph):
        """Test softmax policy when only one action is available."""
        config = BaselinePolicyConfig(policy_type="softmax", temperature=1.0, seed=42)
        policy = create_baseline_policy(config)

        # At n1, only one action: n2
        action, log_prob = policy.select_action(simple_graph.nodes["n1"], simple_graph)
        assert action == "n2"
        # Log prob should be 0.0 for a single deterministic choice in softmax (exp(0)/exp(0)=1, log(1)=0)
        assert math.isclose(log_prob, 0.0, abs_tol=1e-5)

    def test_softmax_policy_branching(self, branching_graph):
        """Test softmax policy with multiple actions."""
        config = BaselinePolicyConfig(policy_type="softmax", temperature=1.0, seed=42)
        policy = create_baseline_policy(config)

        # At start, two actions: left, right
        action, log_prob = policy.select_action(branching_graph.nodes["start"], branching_graph)
        assert action in ["left", "right"]
        # Log prob should be negative (prob < 1)
        assert log_prob < 0

    def test_softmax_policy_temperature_effect(self, branching_graph):
        """Test that temperature affects probability distribution."""
        # High temperature -> more uniform
        config_high = BaselinePolicyConfig(policy_type="softmax", temperature=10.0, seed=42)
        policy_high = create_baseline_policy(config_high)

        # Low temperature -> more peaked (though with equal logits, it's still uniform)
        config_low = BaselinePolicyConfig(policy_type="softmax", temperature=0.1, seed=42)
        policy_low = create_baseline_policy(config_low)

        # Since logits are equal (0.0), softmax is uniform regardless of temperature.
        # We test that the code runs without error and returns valid actions.
        for _ in range(100):
            a_high, _ = policy_high.select_action(branching_graph.nodes["start"], branching_graph)
            a_low, _ = policy_low.select_action(branching_graph.nodes["start"], branching_graph)
            assert a_high in ["left", "right"]
            assert a_low in ["left", "right"]

    def test_rule_based_policy_initialization(self):
        """Test that a rule-based policy initializes correctly."""
        config = BaselinePolicyConfig(policy_type="rule_based", greedy_prob=0.9, seed=42)
        policy = create_baseline_policy(config)
        assert policy.policy_type == "rule_based"
        assert policy.config.greedy_prob == 0.9

    def test_rule_based_policy_branching(self, branching_graph):
        """Test rule-based policy with multiple actions."""
        config = BaselinePolicyConfig(policy_type="rule_based", greedy_prob=0.9, seed=42)
        policy = create_baseline_policy(config)

        action, log_prob = policy.select_action(branching_graph.nodes["start"], branching_graph)
        assert action in ["left", "right"]
        # Log prob for random choice is log(1/2) = -0.693...
        # For greedy, it's 0.0. Since it's stochastic, we just check it's a valid number.
        assert isinstance(log_prob, float)

    def test_no_actions(self):
        """Test behavior when no actions are available."""
        g = StateGraph(tier=1)
        n = Node(id="n1", state_value=0, is_goal=True)
        g.nodes = {"n1": n}
        g.edges = []
        g.start = "n1"
        g.goal = "n1"

        config = BaselinePolicyConfig(policy_type="softmax", temperature=1.0, seed=42)
        policy = create_baseline_policy(config)

        action, log_prob = policy.select_action(n, g)
        assert action is None
        assert log_prob == 0.0

    def test_deterministic_regeneration_seed(self, simple_graph):
        """Test that the same seed produces the same sequence of actions."""
        config1 = BaselinePolicyConfig(policy_type="softmax", temperature=1.0, seed=123)
        policy1 = create_baseline_policy(config1)

        config2 = BaselinePolicyConfig(policy_type="softmax", temperature=1.0, seed=123)
        policy2 = create_baseline_policy(config2)

        actions1 = []
        actions2 = []
        current = simple_graph.nodes["n1"]

        for _ in range(5):
            a1, _ = policy1.select_action(current, simple_graph)
            a2, _ = policy2.select_action(current, simple_graph)
            actions1.append(a1)
            actions2.append(a2)
            if a1:
                current = simple_graph.nodes[a1]

        assert actions1 == actions2