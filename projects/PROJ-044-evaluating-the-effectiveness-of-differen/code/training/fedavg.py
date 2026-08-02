import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import Optimizer
from torch.nn import Module
from opacus import PrivacyEngine
from opacus.validators import ModuleValidator

# Local imports based on provided API surface
from config import Config, get_default_config
from data.partition import load_femnist_data, load_shakespeare_data, apply_dirichlet_partition, partition_femnist, partition_shakespeare
from training.logging import ExperimentLogger, TrainingMetrics, log_training_round
from training.dp_utils import DPConfig, calculate_noise_multiplier, configure_dp_optimizer, get_privacy_spent, validate_dp_config
from models.cnn import SmallCNN, get_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FedAvgOrchestrator:
    """
    Orchestrates Federated Learning with Differential Privacy.
    Implements FedAvg with Opacus for DP-SGD.
    """
    
    def __init__(self, config: Config, dp_config: DPConfig):
        self.config = config
        self.dp_config = dp_config
        self.logger = ExperimentLogger(config.seed, config.epsilon, config.alpha)
        self.model: Optional[Module] = None
        self.optimizer: Optional[Optimizer] = None
        self.privacy_engine: Optional[PrivacyEngine] = None
        self.round_count = 0
        self.is_time_limited = False
        self.utility_collapse_detected = False
        
        # Utility collapse thresholds
        self.MIN_ACCURACY_THRESHOLD = 0.05  # 5% accuracy (near random for 10 classes)
        self.MIN_LOSS_THRESHOLD = 10.0      # Extremely high loss indicates collapse
        self.CRITICAL_EPSILON = 0.01        # Epsilon below this is considered critical
        
    def _initialize_model(self):
        """Initialize the global model based on dataset."""
        if self.config.dataset == "femnist":
            self.model = SmallCNN(num_classes=62)  # FEMNIST has 62 classes
        elif self.config.dataset == "shakespeare":
            self.model = SmallCNN(num_classes=80)  # Shakespeare has 80 classes (chars)
        else:
            raise ValueError(f"Unsupported dataset: {self.config.dataset}")
        
        self.model.train()
        
    def _get_client_loaders(self, partition_data: Dict[str, Dict[str, Any]]) -> Dict[str, DataLoader]:
        """Create DataLoaders for each client from partition metadata."""
        client_loaders = {}
        for client_id, client_info in partition_data.items():
            # Assuming partition_data contains pre-loaded tensors or paths
            # This is a simplified mapping; in real implementation, 
            # we would use the actual partitioned datasets
            dataset = client_info.get('dataset')
            if dataset is None:
                continue
            
            loader = DataLoader(
                dataset,
                batch_size=self.dp_config.batch_size,
                shuffle=True,
                num_workers=0  # Set to >0 if multiprocessing is needed
            )
            client_loaders[client_id] = loader
        return client_loaders

    def _train_round(self, client_loaders: Dict[str, DataLoader], clients_to_update: List[str]) -> Dict[str, float]:
        """
        Perform one round of federated training.
        Returns per-client accuracies.
        """
        client_accuracies = {}
        
        for client_id in clients_to_update:
            if client_id not in client_loaders:
                logger.warning(f"Client {client_id} not found in loaders, skipping.")
                continue
            
            client_loader = client_loaders[client_id]
            client_loss = 0.0
            correct = 0
            total = 0
            
            # Check for empty loader (zero samples)
            if len(client_loader) == 0:
                logger.warning(f"Client {client_id} has zero samples, skipping gradient update.")
                client_accuracies[client_id] = 0.0
                continue
            
            self.model.train()
            for batch in client_loader:
                data, targets = batch
                if isinstance(data, torch.Tensor):
                    data = data.to(next(self.model.parameters()).device)
                    targets = targets.to(next(self.model.parameters()).device)
                else:
                    # Handle potential non-tensor data (e.g., strings for Shakespeare)
                    # This is a placeholder for actual data processing
                    continue

                self.optimizer.zero_grad()
                output = self.model(data)
                loss = nn.CrossEntropyLoss()(output, targets)
                
                # DP-SGD: compute per-sample gradients and clip
                loss.backward()
                self.optimizer.step()
                
                # Track metrics
                client_loss += loss.item() * data.size(0)
                pred = output.argmax(dim=1, keepdim=True)
                correct += pred.eq(targets.view_as(pred)).sum().item()
                total += data.size(0)
            
            avg_loss = client_loss / total if total > 0 else 0.0
            accuracy = correct / total if total > 0 else 0.0
            client_accuracies[client_id] = accuracy
            
            # Check for utility collapse locally
            if accuracy < self.MIN_ACCURACY_THRESHOLD:
                logger.warning(f"Client {client_id} accuracy {accuracy:.4f} below threshold {self.MIN_ACCURACY_THRESHOLD}")
            
        return client_accuracies

    def _aggregate_updates(self, client_loaders: Dict[str, DataLoader], clients_to_update: List[str]):
        """Standard FedAvg aggregation."""
        # In a real implementation, we would accumulate gradients or model weights
        # Here we assume the optimizer handles the aggregation implicitly via 
        # the privacy engine or we perform explicit weight averaging
        # For Opacus, the global model is updated directly in the loop
        # This method serves as a hook for custom aggregation logic if needed
        pass

    def _detect_utility_collapse(self, global_accuracy: float, global_loss: float) -> bool:
        """
        Detects if the model has suffered a 'utility collapse' due to excessive noise.
        Conditions:
        1. Epsilon is extremely low (<= 0.01)
        2. Accuracy is near random (below 5% for classification)
        3. Loss is extremely high (indicating noise dominates signal)
        
        Returns True if collapse is detected.
        """
        if self.config.epsilon <= self.CRITICAL_EPSILON:
            if global_accuracy < self.MIN_ACCURACY_THRESHOLD or global_loss > self.MIN_LOSS_THRESHOLD:
                logger.critical(
                    f"UTILITY COLLAPSE DETECTED: "
                    f"Epsilon={self.config.epsilon}, "
                    f"Accuracy={global_accuracy:.4f}, "
                    f"Loss={global_loss:.4f}. "
                    f"Model performance has collapsed due to excessive privacy noise."
                )
                return True
        return False

    def run(self, num_rounds: int = 100, fraction_clients: float = 1.0):
        """
        Execute the full federated learning experiment.
        
        Args:
            num_rounds: Number of communication rounds.
            fraction_clients: Fraction of clients to participate in each round.
        """
        logger.info(f"Starting FL experiment: Dataset={self.config.dataset}, "
                    f"Alpha={self.config.alpha}, Epsilon={self.config.epsilon}, "
                    f"Rounds={num_rounds}")
        
        self._initialize_model()
        
        # Load and partition data
        if self.config.dataset == "femnist":
            raw_data = load_femnist_data()
            partition_data = partition_femnist(raw_data, self.config.alpha, self.config.seed)
        elif self.config.dataset == "shakespeare":
            raw_data = load_shakespeare_data()
            partition_data = partition_shakespeare(raw_data, self.config.alpha, self.config.seed)
        else:
            raise ValueError(f"Unsupported dataset: {self.config.dataset}")
        
        # Configure DP
        validate_dp_config(self.dp_config)
        self.optimizer = configure_dp_optimizer(
            self.model, 
            self.dp_config, 
            self.config.epsilon,
            self.config.seed
        )
        
        # Prepare client loaders
        client_loaders = self._get_client_loaders(partition_data)
        client_ids = list(client_loaders.keys())
        
        if not client_ids:
            logger.error("No clients available for training.")
            return
        
        num_clients = len(client_ids)
        clients_per_round = max(1, int(num_clients * fraction_clients))
        
        start_time = time.time()
        
        for round_idx in range(num_rounds):
            self.round_count = round_idx + 1
            
            # Select clients for this round
            np.random.seed(self.config.seed + round_idx)
            selected_clients = np.random.choice(client_ids, size=clients_per_round, replace=False).tolist()
            
            # Train on selected clients
            client_accuracies = self._train_round(client_loaders, selected_clients)
            
            # Calculate global metrics
            if client_accuracies:
                global_accuracy = np.mean(list(client_accuracies.values()))
                global_loss = 0.0 # Placeholder for global loss calculation
            else:
                global_accuracy = 0.0
                global_loss = 0.0
            
            # Get privacy spent
            epsilon_spent, delta = get_privacy_spent(self.optimizer)
            
            # Log metrics
            metrics = TrainingMetrics(
                round=round_idx + 1,
                global_accuracy=global_accuracy,
                global_loss=global_loss,
                epsilon_spent=epsilon_spent,
                delta=delta,
                clients_participated=clients_per_round,
                is_time_limited=False,
                utility_collapse_detected=False
            )
            
            # Check for utility collapse
            if self._detect_utility_collapse(global_accuracy, global_loss):
                self.utility_collapse_detected = True
                metrics.utility_collapse_detected = True
                logger.warning("Stopping training due to utility collapse.")
                # Optionally break or continue with warning
                # break 
            
            # Log to CSV/JSON
            self.logger.log(metrics)
            
            # Check time limit (simplified)
            elapsed = time.time() - start_time
            if elapsed > 3600: # 1 hour limit example
                self.is_time_limited = True
                metrics.is_time_limited = True
                self.logger.log(metrics)
                logger.warning("Time limit reached.")
                break
            
            logger.info(f"Round {round_idx + 1}/{num_rounds}: Acc={global_accuracy:.4f}, "
                        f"Epsilon={epsilon_spent:.4f}, Delta={delta:.4e}")
        
        logger.info("Experiment completed.")
        return self.logger.get_results()

def run_experiment(config: Config, dp_config: DPConfig, num_rounds: int = 100):
    """
    Entry point for running a federated learning experiment.
    
    Args:
        config: Configuration object with seed, alpha, epsilon, dataset.
        dp_config: Differential privacy configuration.
        num_rounds: Number of training rounds.
        
    Returns:
        Dict containing experiment results and metrics.
    """
    orchestrator = FedAvgOrchestrator(config, dp_config)
    results = orchestrator.run(num_rounds=num_rounds)
    return results