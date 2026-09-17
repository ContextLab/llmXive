import json
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# Import project utilities
from utils.config import get_hyperparameter, get_path
from utils.environment_config import enforce_cpu_only
from data.models import SymbolicObservation

# --- Dataset Classes ---

class SymbolicDataset(Dataset):
    def __init__(self, data_path: str, tokenizer, max_length: int = 512):
        self.data_path = Path(data_path)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples = []
        self._load_data()

    def _load_data(self):
        """Load symbolic JSON files into memory."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Symbolic dataset path not found: {self.data_path}")
        
        for file_path in self.data_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Assuming data structure matches SymbolicObservation or Trajectory
                    # Adjust based on actual transform_symbolic output structure
                    if isinstance(data, list):
                        self.samples.extend(data)
                    else:
                        self.samples.append(data)
            except Exception as e:
                print(f"Warning: Failed to load {file_path}: {e}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]
        # Convert sample to text prompt
        # This is a placeholder logic; actual prompt construction depends on the specific schema
        text = f"Trajectory: {json.dumps(sample)}" 
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": encoding["input_ids"].squeeze(0)  # For causal LM, labels = input_ids
        }

# --- Helper Functions ---

def load_symbolic_dataset(dataset_dir: str, tokenizer, max_length: int = 512) -> SymbolicDataset:
    return SymbolicDataset(dataset_dir, tokenizer, max_length)

def prepare_training_data(dataset: SymbolicDataset) -> DataLoader:
    return DataLoader(dataset, batch_size=4, shuffle=True) # Batch size configurable via config

def setup_model_and_tokenizer(model_name: str = "microsoft/phi-3-mini"):
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        trust_remote_code=True,
        torch_dtype=torch.float32, # CPU constraint
        device_map="cpu"
    )
    return model, tokenizer

def setup_lora(model: nn.Module, rank: int = 16, alpha: int = 32, dropout: float = 0.05):
    config = LoraConfig(
        r=rank,
        lora_alpha=alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], # Example targets
        lora_dropout=dropout,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, config)
    return model

# --- Checkpointing Logic ---

class TrainingCheckpointer:
    def __init__(self, checkpoint_dir: str, save_interval_epochs: int = 1, save_interval_steps: int = 1000):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.save_interval_epochs = save_interval_epochs
        self.save_interval_steps = save_interval_steps
        self.last_checkpoint_step = 0
        self.last_checkpoint_epoch = 0

    def save_checkpoint(self, model, tokenizer, epoch: int, global_step: int, metrics: dict):
        """Save model, tokenizer, and training state to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = self.checkpoint_dir / f"checkpoint_epoch_{epoch}_step_{global_step}_{timestamp}"
        checkpoint_path.mkdir(parents=True, exist_ok=True)

        # Save model and tokenizer
        model.save_pretrained(checkpoint_path)
        tokenizer.save_pretrained(checkpoint_path)

        # Save training state (epoch, step, metrics)
        state_path = checkpoint_path / "training_state.json"
        state = {
            "epoch": epoch,
            "global_step": global_step,
            "metrics": metrics,
            "timestamp": timestamp
        }
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)

        print(f"Checkpoint saved to {checkpoint_path}")

    def should_save(self, epoch: int, global_step: int) -> bool:
        should_save = False
        if (epoch - self.last_checkpoint_epoch) >= self.save_interval_epochs:
            should_save = True
            self.last_checkpoint_epoch = epoch
        
        if (global_step - self.last_checkpoint_step) >= self.save_interval_steps:
            should_save = True
            self.last_checkpoint_step = global_step
        
        return should_save

# --- Training Loop ---

def train_model(model, dataset_dir, output_dir, epochs=1, learning_rate=2e-5):
    model, tokenizer = setup_model_and_tokenizer()
    model = setup_lora(model)
    
    dataset = load_symbolic_dataset(dataset_dir, tokenizer)
    train_loader = prepare_training_data(dataset)
    
    # Setup Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        fp16=False, # CPU constraint
        logging_steps=10,
        save_strategy="epoch", # Custom logic handled by checkpointer
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        report_to="none"
    )

    # Custom Trainer to integrate checkpointing
    checkpointer = TrainingCheckpointer(
        checkpoint_dir=os.path.join(output_dir, "checkpoints"),
        save_interval_epochs=1,
        save_interval_steps=500
    )

    class CustomTrainer(Trainer):
        def __init__(self, *args, checkpointer, **kwargs):
            super().__init__(*args, **kwargs)
            self.checkpointer = checkpointer

        def training_step(self, model, inputs):
            loss = super().training_step(model, inputs)
            # Checkpoint logic inside training step for step-based saving
            if self.checkpointer.should_save(self.state.epoch, self.state.global_step):
                self.checkpointer.save_checkpoint(
                    model, 
                    self.tokenizer, 
                    self.state.epoch, 
                    self.state.global_step,
                    {"loss": loss.item()}
                )
            return loss

    trainer = CustomTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
        checkpointer=checkpointer
    )

    print(f"Starting training for {epochs} epochs on {len(dataset)} samples...")
    start_time = time.time()
    trainer.train()
    end_time = time.time()
    
    print(f"Training completed in {end_time - start_time:.2f} seconds.")
    
    # Save final model
    trainer.save_model(os.path.join(output_dir, "final_model"))
    tokenizer.save_pretrained(os.path.join(output_dir, "final_model"))

def main():
    parser = argparse.ArgumentParser(description="Train Symbolic-Guava LLM")
    parser.add_argument("--dataset_dir", type=str, default="data/processed/symbolic_guava", help="Path to symbolic dataset")
    parser.add_argument("--output_dir", type=str, default="data/artifacts/trained_model", help="Output directory for model and checkpoints")
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    
    args = parser.parse_args()

    # Ensure CPU constraint
    enforce_cpu_only()

    # Create output directories
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    try:
        train_model(
            model=None, # Model is loaded inside train_model
            dataset_dir=args.dataset_dir,
            output_dir=args.output_dir,
            epochs=args.epochs,
            learning_rate=args.lr
        )
    except Exception as e:
        print(f"Training failed: {e}")
        # Log failure to artifacts if needed
        raise e

if __name__ == "__main__":
    main()