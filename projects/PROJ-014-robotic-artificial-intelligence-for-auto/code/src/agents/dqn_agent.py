"""
DQN Agent implementation with pruned MobileNetV2 backbone for CPU-only training.
Designed for US3: DRL Training & Statistical Analysis.

Features:
- Pruned MobileNetV2 backbone (<1M params target)
- CPU-only execution (no CUDA)
- Compatible with gymnasium environments
- Configurable hyperparameters via project config
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass
import logging
from pathlib import Path

from src.utils.config import get_hyperparameter, get_path

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DQNConfig:
    """Configuration for DQN agent."""
    # Network architecture
    input_shape: Tuple[int, int, int] = (84, 84, 3)  # Default RGB
    hidden_dim: int = 512
    num_filters: int = 32
    kernel_size: int = 3
    # MobileNet pruning config
    prune_factor: float = 0.5  # 50% pruning for backbone
    # Training hyperparameters
    learning_rate: float = 1e-4
    gamma: float = 0.99
    target_update_freq: int = 100
    buffer_size: int = 10000
    batch_size: int = 32
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    # Device
    device: str = "cpu"
    
    @classmethod
    def from_config(cls) -> 'DQNConfig':
        """Load config from project hyperparameters."""
        return cls(
            input_shape=tuple(get_hyperparameter("dqn_input_shape", (84, 84, 3))),
            hidden_dim=get_hyperparameter("dqn_hidden_dim", 512),
            num_filters=get_hyperparameter("dqn_num_filters", 32),
            prune_factor=get_hyperparameter("dqn_prune_factor", 0.5),
            learning_rate=get_hyperparameter("dqn_learning_rate", 1e-4),
            gamma=get_hyperparameter("dqn_gamma", 0.99),
            target_update_freq=get_hyperparameter("dqn_target_update_freq", 100),
            batch_size=get_hyperparameter("dqn_batch_size", 32),
            epsilon_start=get_hyperparameter("dqn_epsilon_start", 1.0),
            epsilon_end=get_hyperparameter("dqn_epsilon_end", 0.01),
            epsilon_decay=get_hyperparameter("dqn_epsilon_decay", 0.995),
            device=get_hyperparameter("dqn_device", "cpu")
        )

class PrunedMobileNetBackbone(nn.Module):
    """
    Pruned MobileNetV2 backbone for efficient CPU inference.
    
    Implements depthwise separable convolutions with pruning to reduce
    parameter count below 1M while maintaining feature extraction capability.
    """
    
    def __init__(self, input_channels: int, output_dim: int, prune_factor: float = 0.5):
        super().__init__()
        self.prune_factor = prune_factor
        self.output_dim = output_dim
        
        # MobileNetV2 inverted residual blocks
        # Reduced width and depth for CPU efficiency
        self.features = nn.Sequential(
            # Initial conv
            nn.Conv2d(input_channels, 32, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU6(inplace=True),
            
            # Block 1: 32 -> 16
            self._make_inverted_residual(32, 16, 1, 1, prune_factor),
            
            # Block 2: 16 -> 24
            self._make_inverted_residual(16, 24, 2, 2, prune_factor),
            
            # Block 3: 24 -> 32
            self._make_inverted_residual(24, 32, 3, 2, prune_factor),
            
            # Block 4: 32 -> 64 (reduced from 64 to 32 for CPU)
            self._make_inverted_residual(32, 32, 4, 2, prune_factor),
            
            # Global average pooling
        )
        
        # Adaptive pooling to fixed size
        self.pool = nn.AdaptiveAvgPool2d(1)
        
        # Final fully connected layer
        self.classifier = nn.Linear(32, output_dim)
        
        self._initialize_weights()
    
    def _make_inverted_residual(
        self, 
        in_channels: int, 
        out_channels: int, 
        num_layers: int, 
        stride: int, 
        prune_factor: float
    ) -> nn.Sequential:
        """Create inverted residual block with optional pruning."""
        layers = []
        expanded_channels = int(in_channels * 6)  # Expansion factor for MobileNet
        
        # Prune expanded channels
        if prune_factor > 0:
            expanded_channels = max(8, int(expanded_channels * (1 - prune_factor)))
        
        # First layer (expansion)
        if num_layers > 1:
            layers.append(nn.Conv2d(in_channels, expanded_channels, 1, 1, 0, bias=False))
            layers.append(nn.BatchNorm2d(expanded_channels))
            layers.append(nn.ReLU6(inplace=True))
        else:
            expanded_channels = in_channels
        
        # Depthwise convolutions
        for i in range(num_layers):
            stride = stride if i == 0 else 1
            layers.append(nn.Conv2d(
                expanded_channels, 
                expanded_channels, 
                3, stride, 1, 
                groups=expanded_channels, 
                bias=False
            ))
            layers.append(nn.BatchNorm2d(expanded_channels))
            layers.append(nn.ReLU6(inplace=True))
            
            # Project to output channels (except last layer)
            if i == num_layers - 1:
                layers.append(nn.Conv2d(expanded_channels, out_channels, 1, 1, 0, bias=False))
                layers.append(nn.BatchNorm2d(out_channels))
        
        return nn.Sequential(*layers)
    
    def _initialize_weights(self):
        """Initialize weights for better convergence."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through backbone."""
        x = self.features(x)
        x = self.pool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

class DQN(nn.Module):
    """
    Deep Q-Network with pruned MobileNetV2 backbone.
    
    Architecture:
    - Pruned MobileNetV2 backbone for feature extraction
    - Fully connected head for Q-value estimation
    """
    
    def __init__(self, config: DQNConfig):
        super().__init__()
        self.config = config
        self.device = torch.device(config.device)
        
        # Calculate input size for FC layer
        input_channels = config.input_shape[-1]
        input_height, input_width = config.input_shape[:2]
        
        # MobileNet backbone
        self.backbone = PrunedMobileNetBackbone(
            input_channels=input_channels,
            output_dim=config.hidden_dim,
            prune_factor=config.prune_factor
        )
        
        # Q-value head
        self.q_head = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(config.hidden_dim // 2, config.hidden_dim // 4),
            nn.ReLU(),
            nn.Linear(config.hidden_dim // 4, 1)  # Single Q-value for continuous action or discrete
        )
        
        self.to(self.device)
        self._count_parameters()
    
    def _count_parameters(self):
        """Count and log total parameters."""
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        logger.info(f"DQN Model Parameters: {total_params:,} total, {trainable_params:,} trainable")
        logger.info(f"Target: <1M params for CPU efficiency")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass."""
        # Ensure input is on correct device
        if x.device != self.device:
            x = x.to(self.device)
        
        # Feature extraction
        features = self.backbone(x)
        
        # Q-value estimation
        q_values = self.q_head(features)
        return q_values
    
    def get_q_values(self, state: torch.Tensor) -> torch.Tensor:
        """Get Q-values for a state."""
        self.eval()
        with torch.no_grad():
            return self.forward(state)
    
    def select_action(
        self, 
        state: np.ndarray, 
        epsilon: float, 
        action_space: int
    ) -> int:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            state: Current state (numpy array)
            epsilon: Exploration rate
            action_space: Number of discrete actions
        
        Returns:
            Selected action index
        """
        if np.random.rand() < epsilon:
            return np.random.randint(action_space)
        
        self.eval()
        with torch.no_grad():
            # Convert to tensor
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.forward(state_tensor)
            return q_values.argmax(dim=1).item()

class DQNAgent:
    """
    DQN Agent for training and inference.
    
    Implements:
    - Experience replay buffer integration
    - Target network updates
    - Epsilon-greedy exploration
    - CPU-optimized training loop
    """
    
    def __init__(self, config: Optional[DQNConfig] = None):
        self.config = config or DQNConfig.from_config()
        self.device = torch.device(self.config.device)
        
        # Initialize networks
        self.policy_network = DQN(self.config)
        self.target_network = DQN(self.config)
        
        # Copy weights to target network
        self.target_network.load_state_dict(self.policy_network.state_dict())
        self.target_network.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(
            self.policy_network.parameters(), 
            lr=self.config.learning_rate
        )
        
        # Loss function
        self.criterion = nn.MSELoss()
        
        # Epsilon decay
        self.epsilon = self.config.epsilon_start
        self.epsilon_final = self.config.epsilon_end
        self.epsilon_decay = self.config.epsilon_decay
        
        # Training statistics
        self.step_count = 0
        self.training_history: List[Dict[str, float]] = []
        
        logger.info(f"DQN Agent initialized on {self.device}")
        logger.info(f"Pruning factor: {self.config.prune_factor}")
    
    def select_action(self, state: np.ndarray, action_space: int) -> int:
        """Select action with epsilon-greedy policy."""
        self.epsilon = max(self.epsilon_final, self.epsilon * self.epsilon_decay)
        return self.policy_network.select_action(state, self.epsilon, action_space)
    
    def store_transition(self, replay_buffer):
        """
        Note: Transition storage is handled by the external replay buffer.
        This method is a placeholder for interface compatibility.
        """
        pass
    
    def train_step(
        self, 
        replay_buffer, 
        batch_size: int
    ) -> float:
        """
        Perform a single training step.
        
        Args:
            replay_buffer: External replay buffer with sample() method
            batch_size: Number of samples to use
        
        Returns:
            Loss value
        """
        if len(replay_buffer) < batch_size:
            return float('nan')
        
        # Sample batch
        states, actions, rewards, next_states, dones = replay_buffer.sample(batch_size)
        
        # Convert to tensors
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Compute current Q values
        current_q = self.policy_network(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Compute target Q values
        with torch.no_grad():
            next_q = self.target_network(next_states).squeeze(1)
            target_q = rewards + (1 - dones) * self.config.gamma * next_q
        
        # Compute loss
        loss = self.criterion(current_q, target_q)
        
        # Optimization step
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.policy_network.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        self.step_count += 1
        
        # Target network update
        if self.step_count % self.config.target_update_freq == 0:
            self._update_target_network()
        
        return loss.item()
    
    def _update_target_network(self):
        """Soft update of target network parameters."""
        target_state_dict = self.target_network.state_dict()
        policy_state_dict = self.policy_network.state_dict()
        
        for key in target_state_dict:
            target_state_dict[key] = policy_state_dict[key].clone()
        
        self.target_network.load_state_dict(target_state_dict)
    
    def get_epsilon(self) -> float:
        """Get current epsilon value."""
        return self.epsilon
    
    def save_checkpoint(self, path: Path, episode: int):
        """Save agent checkpoint."""
        checkpoint = {
            'episode': episode,
            'step_count': self.step_count,
            'epsilon': self.epsilon,
            'policy_network_state': self.policy_network.state_dict(),
            'target_network_state': self.target_network.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'config': self.config
        }
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(checkpoint, path)
        logger.info(f"Checkpoint saved to {path}")
    
    def load_checkpoint(self, path: Path):
        """Load agent checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        
        self.policy_network.load_state_dict(checkpoint['policy_network_state'])
        self.target_network.load_state_dict(checkpoint['target_network_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
        
        self.step_count = checkpoint['step_count']
        self.epsilon = checkpoint['epsilon']
        
        logger.info(f"Checkpoint loaded from {path}, episode {checkpoint['episode']}")
    
    def get_model_size_mb(self) -> float:
        """Get model size in MB."""
        param_size = 0
        for param in self.policy_network.parameters():
            param_size += param.nelement() * param.element_size()
        
        buffer_size = 0
        for buffer in self.policy_network.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        
        return (param_size + buffer_size) / 1024 / 1024

def create_dqn_agent(config: Optional[DQNConfig] = None) -> DQNAgent:
    """Factory function to create a DQN agent."""
    return DQNAgent(config)
