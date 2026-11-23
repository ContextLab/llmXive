import json
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from local utils
from utils.env_config import check_cpu_constraints
from utils.config import initialize_paths, get_path, get_hyperparameter, set_global_seed
from utils.errors import ConvergenceTimeoutError, DatasetUnavailableError
from utils.state_manager import update_state_file, get_project_root

# Import from data models
from data.models import SymbolicObservation, Trajectory

# PyTorch imports
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

class SymbolicDataset(torch.utils.data.Dataset):
    """Dataset wrapper for Symbolic-Guava trajectories."""
    def __init__(self, trajectories: List[Trajectory], tokenizer, max_length: int = 512):
        self.trajectories = trajectories
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.trajectories)

    def __getitem__(self, idx):
        traj = self.trajectories[idx]
        # Convert symbolic observation to text prompt
        prompt = self._format_trajectory(traj)
        encoding = self.tokenizer(
            prompt,
            truncation=True,
            max_length=self.max_length,
            padding="max_length"
        )
        return {
            "input_ids": torch.tensor(encoding["input_ids"]),
            "attention_mask": torch.tensor(encoding["attention_mask"]),
            "labels": torch.tensor(encoding["input_ids"]) # Simple next-token prediction
        }

    def _format_trajectory(self, traj: Trajectory) -> str:
        """Format trajectory into a text prompt for the LLM."""
        parts = []
        parts.append(f"Task: {traj.task_id}")
        parts.append(f"Goal: {traj.goal_description}")
        parts.append("Observations:")
        for obs in traj.observations:
            parts.append(f"  - {obs.to_dict()}")
        parts.append(f"Actions: {traj.actions}")
        return "\n".join(parts)

def load_symbolic_dataset(project_root: Path) -> List[Trajectory]:
    """Load symbolic trajectories from processed data directory."""
    data_path = project_root / "data" / "processed" / "symbolic_guava"
    if not data_path.exists():
        raise DatasetUnavailableError(f"Symbolic dataset directory not found: {data_path}")

    trajectories = []
    for file_path in data_path.glob("*.json"):
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Assuming data conforms to Trajectory model structure
            # In a real scenario, we would use Trajectory.parse_obj(data)
            trajectories.append(Trajectory(**data))
    return trajectories

def prepare_training_data(trajectories: List[Trajectory], tokenizer, max_length: int) -> torch.utils.data.Dataset:
    """Prepare PyTorch dataset from trajectories."""
    return SymbolicDataset(trajectories, tokenizer, max_length)

def setup_model_and_tokenizer(model_name: str = "microsoft/Phi-3-mini-4k-instruct"):
    """Load base model and tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32,
        device_map="auto" if torch.cuda.is_available() else "cpu"
    )
    return model, tokenizer

def setup_lora(model, r: int = 16, lora_alpha: int = 32, lora_dropout: float = 0.05):
    """Configure LoRA for parameter-efficient fine-tuning."""
    config = LoraConfig(
        r=r,
        lora_alpha=lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=lora_dropout,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, config)
    return model

class TrainingCheckpointer:
    def __init__(self, checkpoint_dir: Path, interval: int = 100):
        self.checkpoint_dir = checkpoint_dir
        self.interval = interval
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, model, tokenizer, epoch: int, step: int, loss: float):
        checkpoint_path = self.checkpoint_dir / f"checkpoint-epoch-{epoch}-step-{step}"
        checkpoint_path.mkdir(parents=True, exist_ok=True)
        model.save_pretrained(checkpoint_path)
        tokenizer.save_pretrained(checkpoint_path)
        # Save metrics
        metrics = {"epoch": epoch, "step": step, "loss": loss, "timestamp": datetime.now().isoformat()}
        with open(checkpoint_path / "metrics.json", 'w') as f:
            json.dump(metrics, f)

def train_model(
    model,
    tokenizer,
    train_dataset: torch.utils.data.Dataset,
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 2e-5,
    checkpoint_interval: int = 100
):
    """Main training loop."""
    training_args = TrainingArguments(
        output_dir=str(get_path("data/artifacts/training_output")),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=1,
        learning_rate=learning_rate,
        weight_decay=0.01,
        logging_steps=10,
        save_strategy="steps",
        save_steps=checkpoint_interval,
        fp16=False, # Enforced CPU training usually implies no fp16 unless MPS/CUDA
    )

    # Simple training loop for CPU constraint compliance without Trainer overhead if needed
    # But using Trainer is standard for HF. We will use Trainer for robustness.
    from transformers import Trainer, TrainerCallback

    class ConvergenceCallback(TrainerCallback):
        def __init__(self, start_time: float, timeout_hours: float):
            self.start_time = start_time
            self.timeout_seconds = timeout_hours * 3600
            self.loss_history = []

        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs is None:
                return
            current_loss = logs.get("loss")
            if current_loss is not None:
                self.loss_history.append(current_loss)
                elapsed = time.time() - self.start_time
                if elapsed > self.timeout_seconds:
                    # Check convergence: loss decrease >= 15%
                    if len(self.loss_history) > 1:
                        initial_loss = self.loss_history[0]
                        final_loss = self.loss_history[-1]
                        decrease = (initial_loss - final_loss) / initial_loss
                        if decrease < 0.15:
                            raise ConvergenceTimeoutError(
                                f"Training timeout: {timeout_hours} hours exceeded with insufficient convergence "
                                f"(loss decrease: {decrease:.2%} < 15%)."
                            )
                    else:
                        raise ConvergenceTimeoutError("Training timeout: No loss data recorded.")

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        callbacks=[ConvergenceCallback(time.time(), 4.0)]
    )

    print("Starting training...")
    trainer.train()
    print("Training completed.")
    return trainer

def main():
    """Entry point for training."""
    # 1. Enforce CPU constraints
    print("Checking CPU constraints...")
    try:
        check_cpu_constraints()
    except RuntimeError as e:
        print(f"CPU Constraint Check Failed: {e}")
        sys.exit(1)

    # 2. Initialize paths and config
    project_root = get_project_root()
    initialize_paths(project_root)
    set_global_seed(42)

    # 3. Load Data
    print("Loading symbolic dataset...")
    try:
        trajectories = load_symbolic_dataset(project_root)
        if not trajectories:
            raise DatasetUnavailableError("No symbolic trajectories found.")
    except Exception as e:
        print(f"Failed to load dataset: {e}")
        sys.exit(1)

    # 4. Setup Model
    print("Setting up model and tokenizer...")
    model, tokenizer = setup_model_and_tokenizer()
    model = setup_lora(model)

    # 5. Prepare Data
    max_length = get_hyperparameter("max_sequence_length", 512)
    train_dataset = prepare_training_data(trajectories, tokenizer, max_length)

    # 6. Train
    try:
        trainer = train_model(
            model, tokenizer, train_dataset,
            epochs=get_hyperparameter("epochs", 3),
            batch_size=get_hyperparameter("batch_size", 4),
            learning_rate=get_hyperparameter("learning_rate", 2e-5)
        )
    except ConvergenceTimeoutError as e:
        print(f"Convergence Error: {e}")
        # Trigger GPU escape hatch logic here if required by spec
        # For now, we log and exit
        sys.exit(2)

    # 7. Save Final Model
    output_dir = get_path("data/artifacts/final_model")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")

if __name__ == "__main__":
    main()
