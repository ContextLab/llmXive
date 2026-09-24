import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import Optimizer

from config import Config
from models.cnn import get_model
from training.logging import ExperimentLogger, TrainingMetrics, log_training_round
from training.dp_utils import DPConfig, configure_dp_optimizer, get_privacy_spent
from data.partition import load_femnist_data, apply_dirichlet_partition, partition_femnist
from data.generate_partition_metadata import generate_metadata_for_configuration

logger = logging.getLogger(__name__)

class FedAvgOrchestrator:
    """
    Core FedAvg orchestrator implementing client selection, local training,
    and gradient aggregation. This is the base implementation without DP noise.
    T018b will extend this to integrate Opacus DP noise wrapper.
    """

    def __init__(
        self,
        config: Config,
        device: torch.device,
        global_model: nn.Module,
        logger: ExperimentLogger,
        dp_config: Optional[DPConfig] = None
    ):
        self.config = config
        self.device = device
        self.global_model = global_model
        self.logger = logger
        self.dp_config = dp_config
        self.privacy_accountant = None
        
        if dp_config:
            # Initialize privacy accountant for DP (placeholder for T018b integration)
            # For T018a (core loop without DP), this remains None or unused
            logger.info("DP configuration provided but not active in core loop (T018a)")

    def _select_clients(self, total_clients: int, num_clients: int) -> List[int]:
        """
        Select a subset of clients for the current round.
        For T018a, we use random selection without replacement.
        """
        if num_clients >= total_clients:
            return list(range(total_clients))
        
        selected = np.random.choice(total_clients, size=num_clients, replace=False)
        return sorted(selected.tolist())

    def _get_client_data_loader(
        self,
        client_id: int,
        partition_data: Dict[int, Dict[str, Any]],
        batch_size: int
    ) -> Optional[DataLoader]:
        """
        Retrieve data loader for a specific client.
        Returns None if client has no data.
        """
        if client_id not in partition_data:
            logger.warning(f"Client {client_id} not found in partition data")
            return None
        
        client_data = partition_data[client_id]
        if not client_data or 'data_loader' not in client_data:
            logger.warning(f"Client {client_id} has no data loader")
            return None
        
        return client_data['data_loader']

    def _train_local(
        self,
        client_id: int,
        data_loader: DataLoader,
        local_epochs: int,
        learning_rate: float
    ) -> Tuple[Dict[str, float], Optional[Dict[str, torch.Tensor]]]:
        """
        Train model locally on client data.
        Returns metrics and updated model parameters (if valid).
        """
        # Create a local copy of the model
        local_model = get_model(self.config.dataset)
        local_model.load_state_dict(self.global_model.state_dict())
        local_model.to(self.device)
        local_model.train()

        optimizer = torch.optim.SGD(local_model.parameters(), lr=learning_rate)
        criterion = nn.CrossEntropyLoss()

        metrics = {
            'loss': 0.0,
            'accuracy': 0.0,
            'samples': 0
        }

        total_samples = 0
        total_correct = 0
        total_loss = 0.0

        for epoch in range(local_epochs):
            for batch_idx, (data, target) in enumerate(data_loader):
                data, target = data.to(self.device), target.to(self.device)
                
                optimizer.zero_grad()
                output = local_model(data)
                loss = criterion(output, target)
                
                # T018a: No DP noise application here (reserved for T018b)
                # If dp_config were active, we would clip gradients and add noise here
                
                loss.backward()
                optimizer.step()

                total_loss += loss.item() * data.size(0)
                total_samples += data.size(0)
                
                # Calculate accuracy
                pred = output.argmax(dim=1, keepdim=True)
                total_correct += pred.eq(target.view_as(pred)).sum().item()

        if total_samples == 0:
            logger.warning(f"Client {client_id} had no samples for training")
            return {}, None

        avg_loss = total_loss / total_samples
        accuracy = total_correct / total_samples

        metrics = {
            'loss': avg_loss,
            'accuracy': accuracy,
            'samples': total_samples
        }

        # Return updated parameters
        updated_params = {k: v.clone() for k, v in local_model.state_dict().items()}
        
        return metrics, updated_params

    def _aggregate_weights(
        self,
        client_updates: List[Tuple[int, Dict[str, torch.Tensor], int]],
        total_samples: int
    ) -> Dict[str, torch.Tensor]:
        """
        Aggregate client updates using weighted averaging based on sample count.
        """
        if not client_updates:
            return {}

        # Initialize aggregated parameters
        aggregated = None
        sample_weights = []

        for client_id, params, num_samples in client_updates:
            sample_weights.append(num_samples)
            if aggregated is None:
                aggregated = {k: v.clone() * num_samples for k, v in params.items()}
            else:
                for k in params:
                    aggregated[k] += params[k] * num_samples

        # Normalize by total samples
        total_weight = sum(sample_weights)
        if total_weight == 0:
            logger.error("Total sample weight is zero, cannot aggregate")
            return {}

        for k in aggregated:
            aggregated[k] /= total_weight

        return aggregated

    def run_round(
        self,
        round_num: int,
        partition_data: Dict[int, Dict[str, Any]],
        num_clients: int,
        local_epochs: int,
        learning_rate: float,
        batch_size: int
    ) -> Dict[str, Any]:
        """
        Execute one round of FedAvg.
        """
        start_time = time.time()
        
        total_clients = len(partition_data)
        selected_client_ids = self._select_clients(total_clients, num_clients)
        
        logger.info(f"Round {round_num}: Selected {len(selected_client_ids)} clients from {total_clients}")

        client_updates = []
        client_metrics = []
        skipped_clients = 0

        for client_id in selected_client_ids:
            data_loader = self._get_client_data_loader(client_id, partition_data, batch_size)
            
            if data_loader is None:
                logger.warning(f"Skipping client {client_id}: no data available")
                skipped_clients += 1
                continue

            client_metrics_data, updated_params = self._train_local(
                client_id, data_loader, local_epochs, learning_rate
            )

            if updated_params is None:
                logger.warning(f"Skipping client {client_id}: training returned no updates")
                skipped_clients += 1
                continue

            # T019b: Check for zero-sample clients (should be caught by data_loader check, but double-check)
            if client_metrics_data.get('samples', 0) == 0:
                logger.warning(f"Skipping client {client_id}: zero samples after training")
                skipped_clients += 1
                continue

            client_updates.append((client_id, updated_params, client_metrics_data['samples']))
            client_metrics.append({
                'client_id': client_id,
                'metrics': client_metrics_data
            })

        if not client_updates:
            logger.warning("No valid client updates received for this round")
            return {
                'round': round_num,
                'global_accuracy': None,
                'global_loss': None,
                'skipped_clients': skipped_clients,
                'active_clients': 0,
                'round_time': time.time() - start_time,
                'is_time_limited': False
            }

        # Aggregate updates
        aggregated_params = self._aggregate_weights(client_updates, sum([u[2] for u in client_updates]))
        
        # Update global model
        self.global_model.load_state_dict(aggregated_params)
        self.global_model.to(self.device)
        self.global_model.eval()

        # Calculate global metrics (evaluate on a holdout set or average client metrics)
        # For simplicity, we average client accuracies weighted by samples
        total_weighted_accuracy = 0.0
        total_weighted_loss = 0.0
        total_samples_global = 0

        for client_id, params, num_samples in client_updates:
            # Find corresponding metrics
            for cm in client_metrics:
                if cm['client_id'] == client_id:
                    metrics = cm['metrics']
                    total_weighted_accuracy += metrics['accuracy'] * num_samples
                    total_weighted_loss += metrics['loss'] * num_samples
                    total_samples_global += num_samples
                    break

        global_accuracy = total_weighted_accuracy / total_samples_global if total_samples_global > 0 else 0.0
        global_loss = total_weighted_loss / total_samples_global if total_samples_global > 0 else 0.0

        round_duration = time.time() - start_time

        # Log metrics
        metrics_record = TrainingMetrics(
            round=round_num,
            global_accuracy=global_accuracy,
            global_loss=global_loss,
            num_clients=len(client_updates),
            skipped_clients=skipped_clients,
            round_time=round_duration,
            alpha=self.config.alpha,
            epsilon=self.config.epsilon,
            seed=self.config.seed,
            dataset=self.config.dataset,
            is_time_limited=False,  # T020: Will be set based on timeout logic
            is_utility_collapse=False,  # T021: Will be set based on accuracy threshold
            minority_accuracy=None,  # T019: Calculated separately
            majority_accuracy=None  # T019: Calculated separately
        )

        log_training_round(self.logger, metrics_record)

        logger.info(
            f"Round {round_num} complete: "
            f"Global Acc={global_accuracy:.4f}, "
            f"Global Loss={global_loss:.4f}, "
            f"Clients={len(client_updates)}, "
            f"Skipped={skipped_clients}, "
            f"Time={round_duration:.2f}s"
        )

        return {
            'round': round_num,
            'global_accuracy': global_accuracy,
            'global_loss': global_loss,
            'num_clients': len(client_updates),
            'skipped_clients': skipped_clients,
            'round_time': round_duration,
            'is_time_limited': False
        }

    def run_experiment(
        self,
        partition_data: Dict[int, Dict[str, Any]],
        num_rounds: int,
        num_clients_per_round: int,
        local_epochs: int,
        learning_rate: float,
        batch_size: int,
        target_accuracy: float = 0.90
    ) -> Dict[str, Any]:
        """
        Run the full Federated Learning experiment.
        """
        logger.info(f"Starting FedAvg experiment: {num_rounds} rounds, "
                   f"{num_clients_per_round} clients/round, "
                   f"{local_epochs} local epochs")

        start_time = time.time()
        results = {
            'rounds': [],
            'final_accuracy': None,
            'total_time': 0.0,
            'is_time_limited': False,
            'is_utility_collapse': False
        }

        for round_num in range(1, num_rounds + 1):
            round_result = self.run_round(
                round_num=round_num,
                partition_data=partition_data,
                num_clients=num_clients_per_round,
                local_epochs=local_epochs,
                learning_rate=learning_rate,
                batch_size=batch_size
            )

            results['rounds'].append(round_result)

            # T020: Check for timeout (placeholder - actual timeout logic would be implemented here)
            # For T018a, we assume no timeout unless explicitly triggered
            if round_result['is_time_limited']:
                results['is_time_limited'] = True
                logger.warning("Time limit reached, stopping early")
                break

            # T021: Check for utility collapse
            if round_result['global_accuracy'] is not None and round_result['global_accuracy'] < 0.05:
                results['is_utility_collapse'] = True
                logger.warning("Utility collapse detected (accuracy < 0.05)")
                # Continue running to log the collapse, but flag it

            # Check if target accuracy reached
            if round_result['global_accuracy'] is not None and round_result['global_accuracy'] >= target_accuracy:
                logger.info(f"Target accuracy {target_accuracy} reached at round {round_num}")
                # Optionally break early, but we continue to log full trajectory

        results['total_time'] = time.time() - start_time
        results['final_accuracy'] = results['rounds'][-1]['global_accuracy'] if results['rounds'] else None

        logger.info(f"Experiment complete: {results['total_time']:.2f}s, "
                   f"Final Acc={results['final_accuracy']:.4f}")

        return results

def run_experiment(
    config: Config,
    num_rounds: int,
    num_clients_per_round: int,
    local_epochs: int,
    learning_rate: float,
    batch_size: int,
    target_accuracy: float = 0.90
) -> Dict[str, Any]:
    """
    Main entry point for running a FedAvg experiment.
    T018a: Core implementation without DP noise.
    T018b: Will integrate DP noise wrapper and moments accountant.
    """
    # Set random seed for reproducibility
    torch.manual_seed(config.seed)
    np.random.seed(config.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Load data partitions (assumes T011 and T012 have completed)
    # The partition data should be pre-loaded and cached
    partition_data = partition_femnist(
        seed=config.seed,
        alpha=config.alpha,
        data_path=Path("data/raw/femnist.parquet"),
        output_dir=Path("data/partitions")
    )

    # Initialize global model
    global_model = get_model(config.dataset)
    global_model.to(device)

    # Initialize logger
    logger_instance = ExperimentLogger(
        experiment_dir=Path("results"),
        config=config
    )

    # Initialize DP config (for future T018b integration)
    dp_config = None  # T018a: No DP noise

    # Create orchestrator
    orchestrator = FedAvgOrchestrator(
        config=config,
        device=device,
        global_model=global_model,
        logger=logger_instance,
        dp_config=dp_config
    )

    # Run experiment
    results = orchestrator.run_experiment(
        partition_data=partition_data,
        num_rounds=num_rounds,
        num_clients_per_round=num_clients_per_round,
        local_epochs=local_epochs,
        learning_rate=learning_rate,
        batch_size=batch_size,
        target_accuracy=target_accuracy
    )

    return results