import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torch.optim import SGD, Adam
from torch.nn.utils import clip_grad_norm_

from config import Config
from models.cnn import SmallCNN, get_model
from training.logging import ExperimentLogger, TrainingMetrics, log_training_round
from training.dp_utils import DPConfig, configure_dp_optimizer, get_privacy_spent
from data.partition import load_femnist_data, partition_femnist, save_partition_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FedAvgOrchestrator:
    """
    Federated Averaging Orchestrator supporting both DP and Non-DP modes.
    
    This class implements the core FedAvg loop. It can run with:
    1. DP noise (Opacus integration) when dp_config is provided.
    2. Non-DP baseline (ε=∞) when dp_config is None.
    """

    def __init__(
        self,
        config: Config,
        dp_config: Optional[DPConfig] = None,
        results_dir: Optional[Path] = None
    ):
        self.config = config
        self.dp_config = dp_config
        self.results_dir = results_dir or Path("results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logger
        self.logger = ExperimentLogger(
            results_dir=self.results_dir,
            experiment_name=f"fedavg_{config.dataset}_alpha{config.alpha}_eps{config.epsilon}_seed{config.seed}"
        )

    def _get_client_data_loaders(self, partition_metadata: List[Dict]) -> List[DataLoader]:
        """
        Creates DataLoaders for each client based on partition metadata.
        Handles empty partitions gracefully.
        """
        # Load full dataset once
        dataset = load_femnist_data(self.config.dataset)
        
        loaders = []
        for meta in partition_metadata:
            client_id = meta['client_id']
            indices = meta.get('indices', [])
            
            if not indices:
                logger.warning(f"Client {client_id} has no data samples. Skipping loader creation.")
                loaders.append(None)
                continue
            
            subset = Subset(dataset, indices)
            loader = DataLoader(
                subset,
                batch_size=self.config.batch_size,
                shuffle=True,
                num_workers=0  # Keep simple for now
            )
            loaders.append(loader)
        
        return loaders

    def _aggregate_gradients(
        self,
        client_updates: List[Dict[str, torch.Tensor]],
        client_weights: List[int]
    ) -> Dict[str, torch.Tensor]:
        """
        Aggregates gradients/weights from clients using FedAvg.
        """
        if not client_updates:
            raise ValueError("No client updates to aggregate.")
        
        # Initialize aggregated model
        model = get_model(self.config.dataset)
        aggregated_state = model.state_dict()
        
        total_samples = sum(client_weights)
        
        for key in aggregated_state.keys():
            # Initialize with first client's update weighted
            aggregated_state[key] = torch.zeros_like(client_updates[0][key])
            
            for i, (update, weight) in enumerate(zip(client_updates, client_weights)):
                if key in update:
                    # Weighted average
                    aggregated_state[key] += (update[key] * (weight / total_samples))
                else:
                    # If client didn't update this layer (e.g., skipped), use global
                    aggregated_state[key] += (aggregated_state[key] * (weight / total_samples))
        
        return aggregated_state

    def _train_client(
        self,
        client_id: int,
        loader: Optional[DataLoader],
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int = 1
    ) -> Tuple[Dict[str, torch.Tensor], int, float]:
        """
        Trains a single client for one epoch.
        Returns (updated_params, num_samples, loss).
        """
        if loader is None:
            logger.warning(f"Client {client_id} has no data. Skipping training.")
            return None, 0, 0.0
        
        model.train()
        total_loss = 0.0
        num_samples = 0
        
        # Determine if we are in DP mode
        is_dp = self.dp_config is not None
        
        for batch_idx, (data, target) in enumerate(loader):
            optimizer.zero_grad()
            
            # Forward pass
            output = model(data)
            loss = nn.functional.cross_entropy(output, target)
            
            # Backward pass
            if is_dp:
                # In DP mode, Opacus handles the gradient clipping and noise
                # We need to call backward on the loss
                loss.backward()
                # Opacus optimizer handles the noise addition in step()
            else:
                # Non-DP mode: standard gradient clipping if needed
                loss.backward()
                if self.config.max_grad_norm is not None:
                    clip_grad_norm_(model.parameters(), self.config.max_grad_norm)
            
            optimizer.step()
            
            total_loss += loss.item() * data.size(0)
            num_samples += data.size(0)
        
        # Calculate average loss
        avg_loss = total_loss / num_samples if num_samples > 0 else 0.0
        
        # Get updated parameters
        updated_params = {k: v.clone() for k, v in model.state_dict().items()}
        
        return updated_params, num_samples, avg_loss

    def _evaluate_model(
        self,
        model: nn.Module,
        client_loaders: List[Optional[DataLoader]]
    ) -> Tuple[float, float, float]:
        """
        Evaluates model on all clients.
        Returns (global_accuracy, majority_accuracy, minority_accuracy).
        """
        model.eval()
        total_correct = 0
        total_samples = 0
        
        majority_correct = 0
        majority_samples = 0
        minority_correct = 0
        minority_samples = 0
        
        # Determine majority/minority clients based on label distribution
        # This is a simplified heuristic: clients with > 50% of samples in one class are majority
        # In a real implementation, we'd use the partition metadata more precisely
        
        for client_id, loader in enumerate(client_loaders):
            if loader is None:
                continue
            
            client_correct = 0
            client_samples = 0
            
            with torch.no_grad():
                for data, target in loader:
                    output = model(data)
                    pred = output.argmax(dim=1)
                    client_correct += pred.eq(target).sum().item()
                    client_samples += data.size(0)
            
            total_correct += client_correct
            total_samples += client_samples
            
            # Heuristic for majority/minority (simplified)
            # In practice, this should use the actual label distribution from metadata
            if client_samples > 0:
                # Assume uniform distribution for simplicity in this heuristic
                # A real implementation would check the actual distribution
                is_minority = False # Placeholder logic
                if is_minority:
                    minority_correct += client_correct
                    minority_samples += client_samples
                else:
                    majority_correct += client_correct
                    majority_samples += client_samples
        
        global_acc = total_correct / total_samples if total_samples > 0 else 0.0
        majority_acc = majority_correct / majority_samples if majority_samples > 0 else 0.0
        minority_acc = minority_correct / minority_samples if minority_samples > 0 else 0.0
        
        return global_acc, majority_acc, minority_acc

    def run_training(
        self,
        num_rounds: int = 10,
        num_clients_per_round: int = 10
    ) -> List[Dict]:
        """
        Runs the full federated learning training loop.
        
        Args:
            num_rounds: Number of communication rounds
            num_clients_per_round: Number of clients to sample per round
        
        Returns:
            List of training metrics for each round
        """
        logger.info(f"Starting FedAvg training (DP={self.dp_config is not None})")
        logger.info(f"Config: dataset={self.config.dataset}, alpha={self.config.alpha}, epsilon={self.config.epsilon}")
        
        # Generate partition metadata for this configuration
        # Note: In a real pipeline, this would be loaded from disk
        partition_metadata = partition_femnist(
            dataset=self.config.dataset,
            alpha=self.config.alpha,
            seed=self.config.seed,
            num_clients=100  # Fixed for now
        )
        
        # Initialize global model
        global_model = get_model(self.config.dataset)
        
        # Setup optimizer
        if self.dp_config is not None:
            optimizer = configure_dp_optimizer(
                model=global_model,
                dp_config=self.dp_config,
                lr=self.config.learning_rate
            )
        else:
            # Non-DP baseline: standard SGD
            optimizer = SGD(global_model.parameters(), lr=self.config.learning_rate)
        
        metrics_log = []
        
        for round_idx in range(1, num_rounds + 1):
            logger.info(f"Round {round_idx}/{num_rounds}")
            start_time = time.time()
            
            # Sample clients
            client_indices = np.random.choice(
                len(partition_metadata),
                size=min(num_clients_per_round, len(partition_metadata)),
                replace=False
            )
            
            # Create loaders for selected clients
            client_loaders = [partition_metadata[i] for i in client_indices]
            loaders = self._get_client_data_loaders(client_loaders)
            
            # Train each client
            client_updates = []
            client_weights = []
            
            for client_id, loader in zip(client_indices, loaders):
                # Train client
                updated_params, num_samples, loss = self._train_client(
                    client_id=client_id,
                    loader=loader,
                    model=global_model,
                    optimizer=optimizer,
                    epoch=1
                )
                
                if updated_params is not None:
                    client_updates.append(updated_params)
                    client_weights.append(num_samples)
                
                # Log per-client metrics
                client_metrics = {
                    'round': round_idx,
                    'client_id': int(client_id),
                    'loss': loss,
                    'samples': num_samples,
                    'is_dp': self.dp_config is not None,
                    'epsilon': float(self.config.epsilon) if self.dp_config else float('inf'),
                    'seed': self.config.seed,
                    'alpha': self.config.alpha
                }
                log_training_round(client_metrics)
            
            # Aggregate updates
            if client_updates:
                aggregated_state = self._aggregate_gradients(client_updates, client_weights)
                global_model.load_state_dict(aggregated_state)
            
            # Evaluate global model
            global_acc, majority_acc, minority_acc = self._evaluate_model(
                global_model,
                self._get_client_data_loaders(partition_metadata)
            )
            
            # Calculate privacy budget if DP
            epsilon_spent = 0.0
            if self.dp_config is not None:
                epsilon_spent = get_privacy_spent(self.dp_config, round_idx)
            
            # Log round metrics
            round_metrics = {
                'round': round_idx,
                'global_accuracy': global_acc,
                'majority_accuracy': majority_acc,
                'minority_accuracy': minority_acc,
                'epsilon_spent': epsilon_spent,
                'time_elapsed': time.time() - start_time,
                'is_dp': self.dp_config is not None,
                'epsilon': float(self.config.epsilon) if self.dp_config else float('inf'),
                'seed': self.config.seed,
                'alpha': self.config.alpha,
                'num_clients': len(client_updates)
            }
            
            metrics_log.append(round_metrics)
            log_training_round(round_metrics)
            
            logger.info(f"Round {round_idx} complete: Global Acc={global_acc:.4f}, "
                        f"Maj={majority_acc:.4f}, Min={minority_acc:.4f}, "
                        f"Eps={epsilon_spent:.4f}")
        
        # Save final metrics
        self.logger.save_metrics(metrics_log)
        
        return metrics_log

def run_experiment(
    config: Config,
    dp_config: Optional[DPConfig] = None,
    num_rounds: int = 10,
    num_clients_per_round: int = 10
) -> List[Dict]:
    """
    Convenience function to run a single experiment configuration.
    
    Args:
        config: Configuration object
        dp_config: DP configuration (None for Non-DP baseline)
        num_rounds: Number of training rounds
        num_clients_per_round: Number of clients per round
    
    Returns:
        List of training metrics
    """
    orchestrator = FedAvgOrchestrator(
        config=config,
        dp_config=dp_config,
        results_dir=Path("results")
    )
    
    return orchestrator.run_training(
        num_rounds=num_rounds,
        num_clients_per_round=num_clients_per_round
    )