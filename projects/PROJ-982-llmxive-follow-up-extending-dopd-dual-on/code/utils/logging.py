"""
Logging utilities for training metrics.
"""
import json
import os
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

class TrainingLogger:
    """
    Logger for training metrics and results.
    """
    def __init__(self, run_id: str, output_dir: str, seed: int = None):
        self.run_id = run_id
        self.output_dir = output_dir
        self.seed = seed
        self.metrics: Dict[str, List[Any]] = {
            'step': [],
            'reward': [],
            'loss': [],
            'accuracy': [],
            'entropy': [],
            'timestamp': []
        }
        self.start_time = datetime.now()

        os.makedirs(output_dir, exist_ok=True)

    def log_step(self, step: int, reward: float, loss: float,
                 accuracy: float = None, entropy: float = None):
        """Log metrics for a training step."""
        self.metrics['step'].append(step)
        self.metrics['reward'].append(reward)
        self.metrics['loss'].append(loss)
        if accuracy is not None:
            self.metrics['accuracy'].append(accuracy)
        if entropy is not None:
            self.metrics['entropy'].append(entropy)
        self.metrics['timestamp'].append(datetime.now().isoformat())

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics of logged metrics."""
        summary = {
            'run_id': self.run_id,
            'seed': self.seed,
            'duration': str(datetime.now() - self.start_time),
            'total_steps': len(self.metrics['step'])
        }

        if self.metrics['reward']:
            summary['reward_mean'] = np.mean(self.metrics['reward'])
            summary['reward_std'] = np.std(self.metrics['reward'])
            summary['reward_max'] = np.max(self.metrics['reward'])
            summary['reward_min'] = np.min(self.metrics['reward'])

        if self.metrics['loss']:
            summary['loss_mean'] = np.mean(self.metrics['loss'])
            summary['loss_std'] = np.std(self.metrics['loss'])
            summary['loss_final'] = self.metrics['loss'][-1]

        if self.metrics['accuracy']:
            summary['accuracy_mean'] = np.mean(self.metrics['accuracy'])
            summary['accuracy_final'] = self.metrics['accuracy'][-1]

        if self.metrics['entropy']:
            summary['entropy_mean'] = np.mean(self.metrics['entropy'])
            summary['entropy_final'] = self.metrics['entropy'][-1]

        return summary

    def save_metrics(self, filename: str = None):
        """Save metrics to a JSON file."""
        if filename is None:
            filename = f"{self.run_id}_metrics.json"

        filepath = os.path.join(self.output_dir, filename)

        summary = self.get_summary()
        summary['metrics'] = self.metrics

        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)

        return filepath

def log_training_metrics(logger: TrainingLogger, step: int, reward: float,
                         loss: float, accuracy: float = None, entropy: float = None):
    """
    Convenience function to log training metrics.

    Args:
        logger: TrainingLogger instance.
        step: Current training step.
        reward: Reward obtained.
        loss: Loss value.
        accuracy: Optional accuracy metric.
        entropy: Optional action entropy.
    """
    logger.log_step(step, reward, loss, accuracy, entropy)

def calculate_action_entropy(action_probs: np.ndarray) -> float:
    """
    Calculate the entropy of an action distribution.

    Args:
        action_probs: Probability distribution over actions.

    Returns:
        Entropy value (in nats).
    """
    # Avoid log(0)
    action_probs = np.clip(action_probs, 1e-10, 1.0)
    entropy = -np.sum(action_probs * np.log(action_probs))
    return entropy

def calculate_training_accuracy(predictions: np.ndarray, targets: np.ndarray) -> float:
    """
    Calculate accuracy between predictions and targets.

    Args:
        predictions: Predicted actions.
        targets: Target actions.

    Returns:
        Accuracy as a fraction (0.0 to 1.0).
    """
    if len(predictions) == 0:
        return 0.0

    correct = np.sum(predictions == targets)
    return correct / len(predictions)
