"""
Native Direct Communication Baseline Implementation.

This module implements the baseline communication protocol where agents
communicate directly without the middleware overhead (signing, routing, etc.).
It imports the shared checkpoint module for state management.
"""
import time
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Import shared checkpoint logic
from foundation_protocol.checkpoint import save_checkpoint, load_checkpoint, serialize_state, deserialize_state

logger = logging.getLogger(__name__)

class DirectCommAgent:
    """
    An agent using Native Direct Communication.
    
    Communicates by directly calling methods on other agents or passing
    raw data structures without the MessageEnvelope wrapper.
    """
    def __init__(self, agent_id: str, seed: int = 0):
        self.agent_id = agent_id
        self.seed = seed
        self.state = {}
        self.message_log = []
        
        # Initialize state
        self._init_state()

    def _init_state(self):
        """Initialize agent state."""
        self.state = {
            "agent_id": self.agent_id,
            "seed": self.seed,
            "messages_sent": 0,
            "messages_received": 0,
            "last_action": None
        }

    def act(self, observation: Dict[str, Any]) -> int:
        """
        Determine an action based on observation.
        
        In this baseline, the action is deterministic or random based on seed.
        """
        # Simple heuristic: play card 1 if score is low, else random
        # This is a placeholder logic to simulate decision making
        if observation.get("score", 0) < 5:
            action = 1
        else:
            action = (self.seed + observation.get("turn", 0)) % 5
        
        self.state["last_action"] = action
        self.state["messages_sent"] += 1
        return action

    def receive_message(self, message: Any) -> None:
        """
        Receive a message directly.
        
        In the baseline, the message is expected to be a dict or simple object,
        not a signed envelope.
        """
        self.state["messages_received"] += 1
        self.message_log.append({
            "from": "unknown", # In direct comm, sender might not be explicit in the same way
            "content": message,
            "timestamp": time.time()
        })

    def send_direct(self, target_agent: 'DirectCommAgent', payload: Dict[str, Any]) -> bool:
        """
        Send a message directly to another agent.
        
        Args:
            target_agent: The recipient agent instance
            payload: The data to send
            
        Returns:
            True if successful
        """
        # Simulate direct method call
        target_agent.receive_message(payload)
        self.state["messages_sent"] += 1
        return True

    def save_checkpoint(self, path: str) -> bool:
        """Save agent state using shared checkpoint module."""
        state_dict = serialize_state(self.state)
        return save_checkpoint(state_dict, path)

    def load_checkpoint(self, path: str) -> bool:
        """Load agent state using shared checkpoint module."""
        try:
            loaded_state = load_checkpoint(path)
            self.state = deserialize_state(loaded_state)
            return True
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return False

def create_direct_comm_agent(agent_id: str, seed: int = 0) -> DirectCommAgent:
    """Factory function to create a DirectCommAgent."""
    return DirectCommAgent(agent_id, seed)

# Ensure logic equivalence with middleware for testing
# The core decision logic (act) should be identical when given same inputs