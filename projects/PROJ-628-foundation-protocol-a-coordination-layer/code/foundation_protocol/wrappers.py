"""
Wrappers for legacy protocols (MCP, A2A) to provide FoundationProtocol API compatibility.

These wrappers enable API compatibility testing but are NOT used for statistical
baseline execution. They translate legacy protocol messages into the FoundationProtocol
MessageEnvelope format and vice versa.
"""
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .middleware import MessageEnvelope, FoundationMiddleware
from .checkpoint import serialize_state, deserialize_state, CheckpointError

logger = logging.getLogger(__name__)


@dataclass
class LegacyMessage:
    """Represents a message from a legacy protocol."""
    sender_id: str
    receiver_id: str
    payload: Dict[str, Any]
    timestamp: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class LegacyProtocolWrapper(ABC):
    """
    Abstract base class for wrapping legacy protocols with FoundationProtocol API.
    
    This provides a common interface for MCP, A2A, and other legacy protocols,
    allowing them to be tested for API compatibility with the Foundation Protocol.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the legacy protocol connection."""
        pass
    
    @abstractmethod
    def send_message(self, message: LegacyMessage) -> bool:
        """Send a message via the legacy protocol."""
        pass
    
    @abstractmethod
    def receive_message(self, timeout: float = 1.0) -> Optional[LegacyMessage]:
        """Receive a message via the legacy protocol."""
        pass
    
    @abstractmethod
    def wrap_to_envelope(self, legacy_msg: LegacyMessage) -> MessageEnvelope:
        """Convert a legacy message to a FoundationProtocol MessageEnvelope."""
        pass
    
    @abstractmethod
    def unwrap_from_envelope(self, envelope: MessageEnvelope) -> LegacyMessage:
        """Convert a MessageEnvelope to a legacy message."""
        pass
    
    def close(self):
        """Close the legacy protocol connection."""
        self._initialized = False
        logger.info(f"{self.agent_id}: Legacy protocol wrapper closed")


class MCPWrapper(LegacyProtocolWrapper):
    """
    Wrapper for the Model Control Protocol (MCP) legacy protocol.
    
    MCP uses a different message format that needs translation to/from
    FoundationProtocol MessageEnvelope format.
    """
    
    def __init__(self, agent_id: str, endpoint: str = "mcp://localhost:8080"):
        super().__init__(agent_id)
        self.endpoint = endpoint
        self._connection_state = "disconnected"
    
    def initialize(self) -> bool:
        """Simulate MCP connection initialization."""
        try:
            # In a real implementation, this would establish a connection
            # For API compatibility testing, we simulate the connection
            self._connection_state = "connected"
            self._initialized = True
            logger.info(f"MCPWrapper {self.agent_id}: Connected to {self.endpoint}")
            return True
        except Exception as e:
            logger.error(f"MCPWrapper {self.agent_id}: Initialization failed: {e}")
            self._connection_state = "disconnected"
            return False
    
    def send_message(self, message: LegacyMessage) -> bool:
        """Send a message via simulated MCP."""
        if not self._initialized:
            logger.warning(f"MCPWrapper {self.agent_id}: Not initialized, cannot send")
            return False
        
        try:
            # Simulate sending - in real impl, this would use MCP protocol
            payload_json = json.dumps(message.payload)
            logger.debug(f"MCPWrapper {self.agent_id}: Sending to {message.receiver_id}")
            logger.debug(f"  Payload size: {len(payload_json)} bytes")
            return True
        except Exception as e:
            logger.error(f"MCPWrapper {self.agent_id}: Send failed: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[LegacyMessage]:
        """Receive a message via simulated MCP."""
        if not self._initialized:
            logger.warning(f"MCPWrapper {self.agent_id}: Not initialized, cannot receive")
            return None
        
        # For API compatibility testing, we don't actually receive
        # Real implementation would block until message available
        logger.debug(f"MCPWrapper {self.agent_id}: Waiting for message (timeout={timeout}s)")
        return None
    
    def wrap_to_envelope(self, legacy_msg: LegacyMessage) -> MessageEnvelope:
        """Convert MCP message to FoundationProtocol MessageEnvelope."""
        # Compute signature for the payload
        payload_json = json.dumps(legacy_msg.payload, sort_keys=True)
        signature = hashlib.sha256(
            f"{legacy_msg.sender_id}:{legacy_msg.receiver_id}:{legacy_msg.timestamp}:{payload_json}".encode()
        ).hexdigest()
        
        # Create MessageEnvelope with MCP-specific metadata
        envelope = MessageEnvelope(
            sender_id=legacy_msg.sender_id,
            receiver_id=legacy_msg.receiver_id,
            timestamp=datetime.fromtimestamp(legacy_msg.timestamp).isoformat(),
            signature=signature,
            payload_size=len(payload_json),
            checkpoint_ref=legacy_msg.metadata.get("checkpoint_ref", ""),
            payload=legacy_msg.payload,
            protocol="mcp",
            metadata={
                "legacy_protocol": "mcp",
                "endpoint": self.endpoint,
                "original_metadata": legacy_msg.metadata
            }
        )
        return envelope
    
    def unwrap_from_envelope(self, envelope: MessageEnvelope) -> LegacyMessage:
        """Convert MessageEnvelope to MCP message."""
        if envelope.protocol != "mcp":
            logger.warning(f"MCPWrapper {self.agent_id}: Expected MCP protocol, got {envelope.protocol}")
        
        # Extract timestamp from ISO format
        try:
            ts = datetime.fromisoformat(envelope.timestamp).timestamp()
        except (ValueError, TypeError):
            ts = time.time()
        
        legacy_msg = LegacyMessage(
            sender_id=envelope.sender_id,
            receiver_id=envelope.receiver_id,
            payload=envelope.payload or {},
            timestamp=ts,
            metadata=envelope.metadata.get("original_metadata", {})
        )
        return legacy_msg


class A2AWrapper(LegacyProtocolWrapper):
    """
    Wrapper for the Agent-to-Agent (A2A) legacy protocol.
    
    A2A uses a different message format that needs translation to/from
    FoundationProtocol MessageEnvelope format.
    """
    
    def __init__(self, agent_id: str, network_id: str = "a2a-network-1"):
        super().__init__(agent_id)
        self.network_id = network_id
        self._connection_state = "disconnected"
    
    def initialize(self) -> bool:
        """Simulate A2A connection initialization."""
        try:
            # In a real implementation, this would join the A2A network
            self._connection_state = "connected"
            self._initialized = True
            logger.info(f"A2AWrapper {self.agent_id}: Joined network {self.network_id}")
            return True
        except Exception as e:
            logger.error(f"A2AWrapper {self.agent_id}: Initialization failed: {e}")
            self._connection_state = "disconnected"
            return False
    
    def send_message(self, message: LegacyMessage) -> bool:
        """Send a message via simulated A2A."""
        if not self._initialized:
            logger.warning(f"A2AWrapper {self.agent_id}: Not initialized, cannot send")
            return False
        
        try:
            # Simulate sending - in real impl, this would use A2A protocol
            payload_json = json.dumps(message.payload)
            logger.debug(f"A2AWrapper {self.agent_id}: Broadcasting to {message.receiver_id}")
            logger.debug(f"  Payload size: {len(payload_json)} bytes")
            return True
        except Exception as e:
            logger.error(f"A2AWrapper {self.agent_id}: Send failed: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[LegacyMessage]:
        """Receive a message via simulated A2A."""
        if not self._initialized:
            logger.warning(f"A2AWrapper {self.agent_id}: Not initialized, cannot receive")
            return None
        
        # For API compatibility testing, we don't actually receive
        # Real implementation would listen for broadcast messages
        logger.debug(f"A2AWrapper {self.agent_id}: Listening on network (timeout={timeout}s)")
        return None
    
    def wrap_to_envelope(self, legacy_msg: LegacyMessage) -> MessageEnvelope:
        """Convert A2A message to FoundationProtocol MessageEnvelope."""
        # Compute signature for the payload
        payload_json = json.dumps(legacy_msg.payload, sort_keys=True)
        signature = hashlib.sha256(
            f"{legacy_msg.sender_id}:{legacy_msg.receiver_id}:{legacy_msg.timestamp}:{payload_json}".encode()
        ).hexdigest()
        
        # Create MessageEnvelope with A2A-specific metadata
        envelope = MessageEnvelope(
            sender_id=legacy_msg.sender_id,
            receiver_id=legacy_msg.receiver_id,
            timestamp=datetime.fromtimestamp(legacy_msg.timestamp).isoformat(),
            signature=signature,
            payload_size=len(payload_json),
            checkpoint_ref=legacy_msg.metadata.get("checkpoint_ref", ""),
            payload=legacy_msg.payload,
            protocol="a2a",
            metadata={
                "legacy_protocol": "a2a",
                "network_id": self.network_id,
                "original_metadata": legacy_msg.metadata
            }
        )
        return envelope
    
    def unwrap_from_envelope(self, envelope: MessageEnvelope) -> LegacyMessage:
        """Convert MessageEnvelope to A2A message."""
        if envelope.protocol != "a2a":
            logger.warning(f"A2AWrapper {self.agent_id}: Expected A2A protocol, got {envelope.protocol}")
        
        # Extract timestamp from ISO format
        try:
            ts = datetime.fromisoformat(envelope.timestamp).timestamp()
        except (ValueError, TypeError):
            ts = time.time()
        
        legacy_msg = LegacyMessage(
            sender_id=envelope.sender_id,
            receiver_id=envelope.receiver_id,
            payload=envelope.payload or {},
            timestamp=ts,
            metadata=envelope.metadata.get("original_metadata", {})
        )
        return legacy_msg


class FoundationProtocolAdapter:
    """
    Adapter that wraps a legacy protocol wrapper to provide FoundationProtocol API.
    
    This allows legacy protocol implementations to be used as drop-in replacements
    for FoundationProtocol agents in API compatibility tests.
    """
    
    def __init__(self, wrapper: LegacyProtocolWrapper):
        self.wrapper = wrapper
        self.agent_id = wrapper.agent_id
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the legacy protocol via the wrapper."""
        success = self.wrapper.initialize()
        if success:
            self._initialized = True
        return success
    
    def send(self, receiver_id: str, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Send a message using the legacy protocol, wrapped in MessageEnvelope."""
        if not self._initialized:
            logger.warning(f"FoundationProtocolAdapter {self.agent_id}: Not initialized")
            return False
        
        legacy_msg = LegacyMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            payload=payload,
            metadata=metadata or {}
        )
        
        # Convert to envelope for validation
        envelope = self.wrapper.wrap_to_envelope(legacy_msg)
        logger.debug(f"FoundationProtocolAdapter {self.agent_id}: Sending envelope to {receiver_id}")
        logger.debug(f"  Signature: {envelope.signature[:16]}...")
        
        # Send via legacy protocol
        return self.wrapper.send_message(legacy_msg)
    
    def receive(self, timeout: float = 1.0) -> Optional[MessageEnvelope]:
        """Receive a message and convert it to MessageEnvelope."""
        if not self._initialized:
            logger.warning(f"FoundationProtocolAdapter {self.agent_id}: Not initialized")
            return None
        
        legacy_msg = self.wrapper.receive_message(timeout=timeout)
        if legacy_msg is None:
            return None
        
        # Convert to MessageEnvelope
        envelope = self.wrapper.wrap_to_envelope(legacy_msg)
        logger.debug(f"FoundationProtocolAdapter {self.agent_id}: Received envelope from {legacy_msg.sender_id}")
        return envelope
    
    def close(self):
        """Close the connection."""
        self.wrapper.close()
        self._initialized = False


def create_mcp_adapter(agent_id: str, endpoint: str = "mcp://localhost:8080") -> FoundationProtocolAdapter:
    """Create a FoundationProtocol adapter for MCP."""
    wrapper = MCPWrapper(agent_id, endpoint)
    return FoundationProtocolAdapter(wrapper)


def create_a2a_adapter(agent_id: str, network_id: str = "a2a-network-1") -> FoundationProtocolAdapter:
    """Create a FoundationProtocol adapter for A2A."""
    wrapper = A2AWrapper(agent_id, network_id)
    return FoundationProtocolAdapter(wrapper)


def run_api_compatibility_test():
    """
    Run API compatibility tests for legacy protocol wrappers.
    
    This function tests that MCP and A2A wrappers can be instantiated,
    initialized, and can properly convert messages to/from MessageEnvelope format.
    These tests are for API compatibility only and do not execute statistical
    baseline comparisons.
    """
    logger.info("Starting API compatibility tests for legacy protocol wrappers")
    
    # Test MCP wrapper
    logger.info("Testing MCP wrapper...")
    mcp_adapter = create_mcp_adapter("test-agent-mcp")
    assert mcp_adapter.initialize(), "MCP adapter initialization failed"
    
    test_payload = {"action": "test", "value": 42, "data": [1, 2, 3]}
    success = mcp_adapter.send("receiver-1", test_payload, {"test_id": "mcp-001"})
    assert success, "MCP send failed"
    
    # Test A2A wrapper
    logger.info("Testing A2A wrapper...")
    a2a_adapter = create_a2a_adapter("test-agent-a2a")
    assert a2a_adapter.initialize(), "A2A adapter initialization failed"
    
    success = a2a_adapter.send("receiver-2", test_payload, {"test_id": "a2a-001"})
    assert success, "A2A send failed"
    
    # Test MessageEnvelope conversion round-trip
    logger.info("Testing MessageEnvelope conversion...")
    legacy_msg = LegacyMessage(
        sender_id="sender-1",
        receiver_id="receiver-1",
        payload={"key": "value"},
        metadata={"checkpoint": "chk-123"}
    )
    
    mcp_wrapper = MCPWrapper("test-agent")
    envelope = mcp_wrapper.wrap_to_envelope(legacy_msg)
    assert envelope.sender_id == "sender-1"
    assert envelope.receiver_id == "receiver-1"
    assert envelope.protocol == "mcp"
    assert envelope.checkpoint_ref == "chk-123"
    
    recovered_msg = mcp_wrapper.unwrap_from_envelope(envelope)
    assert recovered_msg.sender_id == "sender-1"
    assert recovered_msg.payload == {"key": "value"}
    
    logger.info("All API compatibility tests passed!")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_api_compatibility_test()