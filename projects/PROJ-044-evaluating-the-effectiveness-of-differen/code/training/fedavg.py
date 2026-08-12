"""
FedAvg Orchestrator for Federated Learning with Differential Privacy.
Implements FedAvg with Opacus, dynamic batch sizing, and comprehensive logging.
"""
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from opacus import PrivacyEngine
from opacus.validators import ModuleValidator

from config import Config
from models.cnn import SmallCNN, SmallMLP, get_model
from training.dp_utils import (
    DPConfig,
    calculate_noise_multiplier,
    configure_dp_optimizer,
    get_privacy_spent,
    validate_dp_config,
)
from training.logging import (
    TrainingMetrics,
    ExperimentLogger,
    log_training_round,
    load_metrics_csv,
)
from data.partition import load_femnist_data, apply_dirichlet_partition, save_partition_metadata

logger = logging.getLogger(__name__)


class FedAvgOrchestrator:
    """
    Orchestrates Federated Averaging training with Differential Privacy.
    Supports dynamic batch sizing to handle OOM errors.
    """

    def __init__(
        self,
        config: Config,
        dp_config: DPConfig,
        model_class: nn.Module,
        partition_dir: Path,
        output_dir: Path,
    ):
        self.config = config
        self.dp_config = dp_config
        self.model_class = model_class
        self.partition_dir = partition_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Validate DP config
        validate_dp_config(dp_config)

        # Initialize logger
        self.logger = ExperimentLogger(
            output_dir=output_dir,
            experiment_id=f"seed_{config.seed}_alpha_{config.alpha}_eps_{config.epsilon}",
        )

        # Initialize global model
        self.global_model = get_model(model_class=model_class, num_classes=62)  # FEMNIST has 62 classes
        self.global_model.to(self.config.device)

        # DP Privacy Engine (initialized per round or once, depending on strategy)
        self.privacy_engine = None

        # Metrics tracking
        self.round_metrics: List[Dict[str, Any]] = []

    def _load_client_data(self, client_id: int, partition_metadata: Dict) -> DataLoader:
        """Load data for a specific client from partition metadata."""
        # This is a simplified loader; in production, this would load from parquet files
        # based on the partition metadata
        try:
            # Load FEMNIST data
            dataset = load_femnist_data(self.config.dataset)
            
            # Apply partitioning logic (simplified for this example)
            # In reality, this would use the pre-computed partition metadata
            indices = partition_metadata.get(f"client_{client_id}", [])
            
            if not indices:
                logger.warning(f"Client {client_id} has no data samples")
                return None
            
            client_dataset = Subset(dataset, indices)
            
            # Dynamic batch sizing: start with configured batch size
            batch_size = self.config.batch_size
            min_batch_size = 16
            
            # Ensure batch size is at least min_batch_size if dataset is small
            if len(client_dataset) < batch_size:
                batch_size = max(len(client_dataset), min_batch_size)
            
            return DataLoader(
                client_dataset,
                batch_size=batch_size,
                shuffle=True,
                num_workers=0,  # Set to 0 for simplicity in this example
                drop_last=True,
            )
        except Exception as e:
            logger.error(f"Failed to load data for client {client_id}: {e}")
            return None

    def _train_client(
        self,
        client_id: int,
        local_data: DataLoader,
        epochs: int,
        lr: float,
        is_dp: bool,
        current_batch_size: int,
    ) -> Tuple[Optional[nn.Module], int, bool]:
        """
        Train a single client's model locally.
        Returns (updated_model, samples_used, is_time_limited).
        """
        if local_data is None:
            logger.warning(f"Client {client_id} has no data, skipping training")
            return None, 0, False

        # Clone global model for local training
        local_model = get_model(model_class=self.model_class, num_classes=62)
        local_model.load_state_dict(self.global_model.state_dict())
        local_model.to(self.config.device)
        local_model.train()

        # Configure optimizer
        optimizer = torch.optim.SGD(
            local_model.parameters(),
            lr=lr,
            momentum=0.9,
        )

        # Configure DP if enabled
        privacy_engine = None
        if is_dp:
            # Calculate noise multiplier
            noise_multiplier = calculate_noise_multiplier(
                target_epsilon=self.dp_config.target_epsilon,
                delta=self.dp_config.delta,
                steps_per_epoch=len(local_data),
                epochs=epochs,
                max_grad_norm=self.dp_config.max_grad_norm,
                noise_multiplier=self.dp_config.noise_multiplier,
            )
            
            privacy_engine = PrivacyEngine(
                local_model,
                batch_size=current_batch_size,
                sample_size=len(local_data.dataset),
                alphas=self.dp_config.alphas,
                noise_multiplier=noise_multiplier,
                max_grad_norm=self.dp_config.max_grad_norm,
            )
            
            privacy_engine.attach(optimizer)

        criterion = nn.CrossEntropyLoss()
        samples_processed = 0
        is_time_limited = False

        start_time = time.time()
        time_limit = self.config.time_limit_seconds if hasattr(self.config, 'time_limit_seconds') else 3600

        for epoch in range(epochs):
            epoch_loss = 0.0
            epoch_samples = 0

            for batch_idx, (data, target) in enumerate(local_data):
                # Check time limit
                if time.time() - start_time > time_limit:
                    logger.warning(f"Time limit exceeded for client {client_id} at epoch {epoch}")
                    is_time_limited = True
                    break

                data, target = data.to(self.config.device), target.to(self.config.device)

                optimizer.zero_grad()
                output = local_model(data)
                loss = criterion(output, target)

                # DP: clip and accumulate gradients
                if is_dp:
                    loss.backward()
                    # Privacy engine handles gradient clipping and noise addition
                    optimizer.step()
                else:
                    loss.backward()
                    optimizer.step()

                epoch_loss += loss.item() * data.size(0)
                epoch_samples += data.size(0)
                samples_processed += data.size(0)

            if is_time_limited:
                break

            # Log epoch metrics
            avg_loss = epoch_loss / epoch_samples if epoch_samples > 0 else 0
            logger.debug(f"Client {client_id} Epoch {epoch}: Loss={avg_loss:.4f}")

        # Detach model from privacy engine if used
        if privacy_engine:
            privacy_engine.detach()

        samples_used = samples_processed
        return local_model, samples_used, is_time_limited

    def _aggregate_models(
        self,
        client_models: List[Tuple[nn.Module, int]],
    ) -> nn.Module:
        """
        Aggregate client models using FedAvg.
        client_models: List of (model, samples_used) tuples
        """
        if not client_models:
            logger.warning("No client models to aggregate")
            return self.global_model

        total_samples = sum(samples for _, samples in client_models)
        
        # Initialize aggregated model
        aggregated_model = get_model(model_class=self.model_class, num_classes=62)
        aggregated_model.load_state_dict(self.global_model.state_dict())

        # Aggregate parameters weighted by samples
        for param_name, param in aggregated_model.state_dict().items():
            weighted_sum = torch.zeros_like(param)
            for model, samples in client_models:
                weighted_sum += model.state_dict()[param_name] * samples
            
            param.copy_(weighted_sum / total_samples)

        return aggregated_model

    def _reduce_batch_size(self, current_batch_size: int) -> int:
        """
        Reduce batch size by half, floor to next power of 2, with hard minimum of 16.
        """
        min_batch_size = 16
        if current_batch_size <= min_batch_size:
            return min_batch_size
        
        # Floor to next power of 2
        reduced = current_batch_size // 2
        # Ensure it's at least min_batch_size
        return max(reduced, min_batch_size)

    def train_round(
        self,
        round_num: int,
        num_clients: int,
        clients_to_sample: Optional[int] = None,
        epochs: int = 1,
        lr: float = 0.01,
        is_dp: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute a single round of FedAvg training.
        Returns round metrics.
        """
        logger.info(f"Starting round {round_num} with {num_clients} clients")
        
        # Load partition metadata
        partition_files = list(self.partition_dir.glob("partition_*.json"))
        if not partition_files:
            raise FileNotFoundError(f"No partition files found in {self.partition_dir}")
        
        # Use the first partition file (in practice, would load all or specific one)
        partition_file = partition_files[0]
        with open(partition_file, 'r') as f:
            partition_metadata = json.load(f)
        
        # Sample clients if specified
        client_ids = list(range(num_clients))
        if clients_to_sample and clients_to_sample < num_clients:
            np.random.seed(self.config.seed + round_num)
            client_ids = np.random.choice(client_ids, size=clients_to_sample, replace=False).tolist()

        client_models = []
        total_samples = 0
        time_limited_clients = 0
        oom_occurred = False
        current_batch_size = self.config.batch_size

        for client_id in client_ids:
            try:
                # Load client data
                local_data = self._load_client_data(client_id, partition_metadata)
                
                if local_data is None:
                    continue

                # Train client
                local_model, samples_used, is_time_limited = self._train_client(
                    client_id=client_id,
                    local_data=local_data,
                    epochs=epochs,
                    lr=lr,
                    is_dp=is_dp,
                    current_batch_size=current_batch_size,
                )

                if local_model is None:
                    continue

                if is_time_limited:
                    time_limited_clients += 1

                client_models.append((local_model, samples_used))
                total_samples += samples_used

            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    logger.warning(f"OOM for client {client_id} with batch size {current_batch_size}")
                    oom_occurred = True
                    current_batch_size = self._reduce_batch_size(current_batch_size)
                    logger.info(f"Reduced batch size to {current_batch_size} for next client")
                    # Retry with smaller batch size
                    local_data = self._load_client_data(client_id, partition_metadata)
                    if local_data:
                        local_model, samples_used, is_time_limited = self._train_client(
                            client_id=client_id,
                            local_data=local_data,
                            epochs=epochs,
                            lr=lr,
                            is_dp=is_dp,
                            current_batch_size=current_batch_size,
                        )
                        if local_model is not None:
                            client_models.append((local_model, samples_used))
                            total_samples += samples_used
                    else:
                        logger.error(f"Failed to load data for client {client_id} after OOM recovery")
                else:
                    logger.error(f"Error training client {client_id}: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error for client {client_id}: {e}")
                raise

        if not client_models:
            logger.warning("No clients successfully trained in this round")
            return {
                "round": round_num,
                "success": False,
                "error": "No clients trained",
            }

        # Aggregate models
        self.global_model = self._aggregate_models(client_models)

        # Evaluate global model
        # (Simplified evaluation - in practice, would use a held-out test set)
        global_accuracy = 0.0  # Placeholder
        if hasattr(self.config, 'test_data') and self.config.test_data:
            # Evaluate on test data
            pass

        # Log metrics
        round_metrics = {
            "round": round_num,
            "success": True,
            "num_clients": len(client_models),
            "total_samples": total_samples,
            "time_limited_clients": time_limited_clients,
            "oom_occurred": oom_occurred,
            "batch_size_used": current_batch_size,
            "global_accuracy": global_accuracy,
            "privacy_budget_used": 0.0,  # Placeholder - would calculate from privacy engine
        }

        if is_dp and self.privacy_engine:
            epsilon_spent, delta_spent = get_privacy_spent(self.privacy_engine)
            round_metrics["privacy_budget_used"] = epsilon_spent
            round_metrics["delta_spent"] = delta_spent

        self.round_metrics.append(round_metrics)
        self.logger.log_round(round_metrics)

        logger.info(f"Round {round_num} completed: {len(client_models)} clients, accuracy={global_accuracy:.4f}")
        return round_metrics

    def train(
        self,
        total_rounds: int,
        num_clients: int,
        clients_per_round: int,
        epochs_per_round: int = 1,
        lr: float = 0.01,
        is_dp: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Run full training for specified number of rounds.
        Returns list of round metrics.
        """
        logger.info(f"Starting training for {total_rounds} rounds")
        
        for round_num in range(1, total_rounds + 1):
            metrics = self.train_round(
                round_num=round_num,
                num_clients=num_clients,
                clients_to_sample=clients_per_round,
                epochs=epochs_per_round,
                lr=lr,
                is_dp=is_dp,
            )
            
            if not metrics.get("success", False):
                logger.error(f"Training failed at round {round_num}")
                break

        # Save final model
        model_path = self.output_dir / "final_model.pt"
        torch.save(self.global_model.state_dict(), model_path)
        logger.info(f"Final model saved to {model_path}")

        # Save metrics
        self.logger.save_metrics()

        return self.round_metrics


def run_experiment(config: Config, dp_config: DPConfig) -> Dict[str, Any]:
    """
    Run a complete FedAvg experiment with the given configuration.
    """
    logger.info(f"Running experiment with config: seed={config.seed}, alpha={config.alpha}, epsilon={config.epsilon}")
    
    # Determine model class
    if config.model_type == "cnn":
        model_class = SmallCNN
    elif config.model_type == "mlp":
        model_class = SmallMLP
    else:
        raise ValueError(f"Unknown model type: {config.model_type}")
    
    # Create orchestrator
    orchestrator = FedAvgOrchestrator(
        config=config,
        dp_config=dp_config,
        model_class=model_class,
        partition_dir=config.partition_dir,
        output_dir=config.results_dir,
    )
    
    # Run training
    metrics = orchestrator.train(
        total_rounds=config.total_rounds,
        num_clients=config.num_clients,
        clients_per_round=config.clients_per_round,
        epochs_per_round=config.epochs_per_round,
        lr=config.learning_rate,
        is_dp=config.enable_dp,
    )
    
    return {
        "config": config,
        "metrics": metrics,
        "final_model_path": config.results_dir / "final_model.pt",
    }