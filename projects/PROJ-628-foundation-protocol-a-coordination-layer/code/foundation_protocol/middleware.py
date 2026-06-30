"""
Foundation Protocol Middleware

Implements the coordination layer for agentic society, providing:
- Message routing and dispatching
- Cryptographic signing and verification
- Checkpointing and state recovery
- Protocol compliance enforcement

This module imports checkpoint logic from the shared checkpoint module
to ensure consistency with the Native Direct Communication baseline.
"""

import json
import hashlib
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable, List, Tuple
from dataclasses import dataclass, asdict

from .checkpoint import (
    CheckpointError,
    serialize_state,
    deserialize_state,
    save_checkpoint,
    load_checkpoint,
    verify_checkpoint_integrity,
    create_empty_checkpoint,
    merge_checkpoints
)
from .utils import get_hash

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MessageEnvelope:
    """
    Standard message envelope for the Foundation Protocol.

    Fields per T004 schema:
    - sender_id: Unique identifier of the sending agent
    - receiver_id: Unique identifier of the receiving agent (or 'broadcast')
    - timestamp: ISO 8601 timestamp of message creation
    - signature: Cryptographic signature of the payload
    - payload_size: Size of the payload in bytes
    - checkpoint_ref: Optional reference to a checkpoint for recovery
    """
    sender_id: str
    receiver_id: str
    timestamp: str
    signature: str
    payload_size: int
    payload: Dict[str, Any]
    checkpoint_ref: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert envelope to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageEnvelope':
        """Create envelope from dictionary."""
        return cls(**data)

    def compute_payload_hash(self) -> str:
        """Compute SHA-256 hash of the payload for signing."""
        payload_bytes = json.dumps(self.payload, sort_keys=True).encode('utf-8')
        return hashlib.sha256(payload_bytes).hexdigest()

    def verify_signature(self, public_key: bytes) -> bool:
        """
        Verify the message signature using the sender's public key.

        Note: For this implementation, we use a simplified signature verification.
        In production, this would use the ed25519 library with proper key management.
        """
        try:
            import ed25519
            # Reconstruct the signed message for verification
            payload_hash = self.compute_payload_hash()
            signature_bytes = bytes.fromhex(self.signature)
            # Verify signature matches the payload hash
            # This is a simplified check; real implementation uses ed25519.verify
            return self.signature == self._compute_signature(payload_hash, public_key)
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return False

    def _compute_signature(self, payload_hash: str, private_key: bytes) -> str:
        """
        Compute signature for the payload hash.

        In production, this would use proper ed25519 signing.
        """
        try:
            import ed25519
            # Create a signature from the hash
            # This is a simplified implementation for testing
            combined = (private_key + payload_hash.encode()).encode()
            return hashlib.sha256(combined).hexdigest()
        except ImportError:
            # Fallback for environments without ed25519
            return hashlib.sha256((private_key + payload_hash.encode()).encode()).hexdigest()

    def sign(self, private_key: bytes) -> None:
        """Sign the message with the sender's private key."""
        payload_hash = self.compute_payload_hash()
        self.signature = self._compute_signature(payload_hash, private_key)


class FoundationMiddleware:
    """
    Foundation Protocol Middleware for agent coordination.

    This class implements the routing, signing, and checkpointing logic
    required by the Foundation Protocol specification. It serves as the
    intervention protocol in comparative experiments.

    Key responsibilities:
    - Route messages between agents based on receiver_id
    - Sign outgoing messages with agent's private key
    - Verify incoming message signatures
    - Maintain checkpoints for state recovery
    - Log metrics for analysis
    """

    def __init__(
        self,
        agent_id: str,
        private_key: bytes,
        checkpoint_dir: Optional[Union[str, Path]] = None,
        log_dir: Optional[Union[str, Path]] = None
    ):
        """
        Initialize the Foundation Middleware.

        Args:
            agent_id: Unique identifier for this agent
            private_key: Private key for signing messages
            checkpoint_dir: Directory for storing checkpoints
            log_dir: Directory for storing logs
        """
        self.agent_id = agent_id
        self.private_key = private_key
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path("data/checkpoints")
        self.log_dir = Path(log_dir) if log_dir else Path("data/logs")

        # Ensure directories exist
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Message queue for routing
        self.message_queue: List[MessageEnvelope] = []

        # Checkpoint state
        self.current_checkpoint: Optional[str] = None
        self.checkpoint_counter = 0

        # Metrics tracking
        self.metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'signatures_verified': 0,
            'signature_failures': 0,
            'checkpoints_created': 0,
            'recovery_attempts': 0,
            'recovery_successes': 0
        }

        logger.info(f"FoundationMiddleware initialized for agent {agent_id}")

    def create_message(
        self,
        receiver_id: str,
        payload: Dict[str, Any],
        checkpoint_ref: Optional[str] = None
    ) -> MessageEnvelope:
        """
        Create a new signed message envelope.

        Args:
            receiver_id: Target agent ID or 'broadcast'
            payload: Message content
            checkpoint_ref: Optional checkpoint reference

        Returns:
            Signed MessageEnvelope
        """
        timestamp = datetime.utcnow().isoformat()
        envelope = MessageEnvelope(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            timestamp=timestamp,
            signature="",  # Will be signed below
            payload_size=len(json.dumps(payload).encode('utf-8')),
            payload=payload,
            checkpoint_ref=checkpoint_ref
        )

        # Sign the message
        envelope.sign(self.private_key)

        # Update metrics
        self.metrics['messages_sent'] += 1
        self.metrics['bytes_sent'] += envelope.payload_size

        logger.debug(f"Created message to {receiver_id} with size {envelope.payload_size}")
        return envelope

    def receive_message(
        self,
        envelope: MessageEnvelope,
        public_key: bytes
    ) -> Optional[MessageEnvelope]:
        """
        Receive and verify a message.

        Args:
            envelope: Incoming MessageEnvelope
            public_key: Sender's public key for verification

        Returns:
            Verified MessageEnvelope or None if verification fails
        """
        # Verify signature
        if not envelope.verify_signature(public_key):
            self.metrics['signature_failures'] += 1
            logger.warning(f"Signature verification failed for message from {envelope.sender_id}")
            return None

        self.metrics['messages_received'] += 1
        self.metrics['bytes_received'] += envelope.payload_size
        self.metrics['signatures_verified'] += 1

        # Add to message queue for processing
        self.message_queue.append(envelope)

        logger.debug(f"Received message from {envelope.sender_id}")
        return envelope

    def route_message(
        self,
        envelope: MessageEnvelope,
        agent_registry: Dict[str, bytes]
    ) -> List[MessageEnvelope]:
        """
        Route a message to appropriate agents.

        Args:
            envelope: Message to route
            agent_registry: Dictionary mapping agent IDs to public keys

        Returns:
            List of successfully delivered messages
        """
        delivered = []

        if envelope.receiver_id == 'broadcast':
            # Deliver to all agents except sender
            for agent_id, public_key in agent_registry.items():
                if agent_id != envelope.sender_id:
                    if self.receive_message(envelope, public_key):
                        delivered.append(envelope)
        else:
            # Deliver to specific agent
            if envelope.receiver_id in agent_registry:
                public_key = agent_registry[envelope.receiver_id]
                if self.receive_message(envelope, public_key):
                    delivered.append(envelope)
            else:
                logger.warning(f"Unknown receiver: {envelope.receiver_id}")

        return delivered

    def create_checkpoint(self, state: Dict[str, Any]) -> str:
        """
        Create a checkpoint of the current state.

        Args:
            state: State dictionary to checkpoint

        Returns:
            Checkpoint identifier
        """
        self.checkpoint_counter += 1
        checkpoint_id = f"{self.agent_id}_ckpt_{self.checkpoint_counter}_{int(time.time())}"
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        # Serialize state
        serialized = serialize_state(state)

        # Save checkpoint
        save_checkpoint(checkpoint_path, serialized, self.agent_id)

        # Verify integrity
        if verify_checkpoint_integrity(checkpoint_path):
            self.metrics['checkpoints_created'] += 1
            self.current_checkpoint = checkpoint_id
            logger.info(f"Created checkpoint {checkpoint_id}")
            return checkpoint_id
        else:
            raise CheckpointError(f"Checkpoint integrity verification failed for {checkpoint_id}")

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint identifier

        Returns:
            Deserialized state or None if not found
        """
        self.metrics['recovery_attempts'] += 1
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_path.exists():
            logger.warning(f"Checkpoint not found: {checkpoint_id}")
            return None

        try:
            if not verify_checkpoint_integrity(checkpoint_path):
                logger.warning(f"Checkpoint integrity failed: {checkpoint_id}")
                return None

            serialized = load_checkpoint(checkpoint_path)
            state = deserialize_state(serialized)
            self.metrics['recovery_successes'] += 1
            logger.info(f"Loaded checkpoint {checkpoint_id}")
            return state
        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        for key in self.metrics:
            self.metrics[key] = 0

    def process_message_queue(self, handler: Callable[[MessageEnvelope], Any]) -> int:
        """
        Process all messages in the queue.

        Args:
            handler: Function to process each message

        Returns:
            Number of messages processed
        """
        count = 0
        while self.message_queue:
            message = self.message_queue.pop(0)
            try:
                handler(message)
                count += 1
            except Exception as e:
                logger.error(f"Error processing message: {e}")
        return count


def create_middleware_agent(
    agent_id: str,
    private_key: bytes,
    checkpoint_dir: Optional[str] = None,
    log_dir: Optional[str] = None
) -> FoundationMiddleware:
    """
    Factory function to create a FoundationMiddleware instance.

    Args:
        agent_id: Unique agent identifier
        private_key: Private key for signing
        checkpoint_dir: Optional checkpoint directory
        log_dir: Optional log directory

    Returns:
        Initialized FoundationMiddleware instance
    """
    return FoundationMiddleware(
        agent_id=agent_id,
        private_key=private_key,
        checkpoint_dir=checkpoint_dir,
        log_dir=log_dir
    )


# Expose public API
__all__ = [
    'MessageEnvelope',
    'FoundationMiddleware',
    'create_middleware_agent',
    'CheckpointError',
    'serialize_state',
    'deserialize_state',
    'save_checkpoint',
    'load_checkpoint',
    'verify_checkpoint_integrity',
    'create_empty_checkpoint',
    'merge_checkpoints'
]