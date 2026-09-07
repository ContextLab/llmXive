import json
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import set_global_seed, ensure_directories
from utils.environment_config import configure_torch_for_cpu, detect_cpu_count
from data.models import SymbolicObservation, Trajectory
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import torch
import numpy as np

# Constants
CPU_TIME_LIMIT_SECONDS = 4 * 60 * 60  # 4 hours in seconds
MODEL_NAME = "microsoft/phi-3-mini"
LORA_R = 8
LORA_ALPHA = 16
LORA_TARGET_MODULES = ["qkv_proj", "o_proj"]
SEED = 42

class SymbolicDataset(torch.utils.data.Dataset):
    """Dataset wrapper for symbolic observations."""
    def __init__(self, data_list, tokenizer, max_length=512):
        self.data = data_list
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        # Convert symbolic observation to text format
        text = self._format_symbolic(item)
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length
        )
        return {
            "input_ids": torch.tensor(encoding["input_ids"]),
            "attention_mask": torch.tensor(encoding["attention_mask"]),
            "labels": torch.tensor(encoding["input_ids"])  # For causal LM
        }

    def _format_symbolic(self, item):
        """Format symbolic observation into text prompt."""
        if isinstance(item, dict):
            # Handle already formatted dict
            return json.dumps(item)
        elif isinstance(item, SymbolicObservation):
            return item.model_dump_json()
        else:
            raise TypeError(f"Unsupported type: {type(item)}")

def load_symbolic_dataset(data_dir: str):
    """Load symbolic dataset from processed directory."""
    data_path = Path(data_dir)
    trajectories = []

    for json_file in data_path.glob("*.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)
            # Convert to SymbolicObservation objects if needed
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        trajectories.append(SymbolicObservation(**item))
                    else:
                        trajectories.append(item)
            elif isinstance(data, dict):
                trajectories.append(SymbolicObservation(**data))

    return trajectories

def prepare_training_data(trajectories, tokenizer, max_length=512):
    """Prepare training dataset from trajectories."""
    # Convert trajectories to training format
    # For simplicity, we use the raw symbolic data as both input and target
    # In a real scenario, you might want to format this differently
    training_data = []
    for traj in trajectories:
        if isinstance(traj, SymbolicObservation):
            training_data.append(traj.model_dump())
        else:
            training_data.append(traj)

    return SymbolicDataset(training_data, tokenizer, max_length)

def setup_model_and_tokenizer(model_name: str = MODEL_NAME):
    """Setup the model and tokenizer for training."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32 if device == "cpu" else torch.float16,
        device_map="auto" if device != "cpu" else None
    )

    if device == "cpu":
        model = configure_torch_for_cpu(model)

    return model, tokenizer, device

def setup_lora(model, r=LORA_R, alpha=LORA_ALPHA, target_modules=None):
    """Setup LoRA for parameter-efficient fine-tuning."""
    if target_modules is None:
        target_modules = LORA_TARGET_MODULES

    lora_config = LoraConfig(
        r=r,
        lora_alpha=alpha,
        target_modules=target_modules,
        lora_dropout=0.1,
        bias="none",
        task_type="CAUSAL_LM"
    )

    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, lora_config)
    return model

def train_model(
    model,
    train_dataset,
    output_dir: str,
    num_epochs: int = 3,
    per_device_train_batch_size: int = 1,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-4,
    logging_steps: int = 10,
    save_steps: int = 100,
    use_gpu: bool = False,
    validation_only: bool = False
):
    """Train the model with LoRA."""
    start_time = time.time()

    device = "cuda" if (torch.cuda.is_available() and use_gpu) else "cpu"
    model.to(device)

    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=per_device_train_batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        logging_steps=logging_steps,
        save_steps=save_steps,
        save_total_limit=2,
        fp16=use_gpu,
        bf16=False,
        report_to="none",
        disable_tqdm=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
    )

    print(f"Starting training on {device}...")
    print(f"CPU Time Limit: {CPU_TIME_LIMIT_SECONDS} seconds (4 hours)")

    # Train
    trainer.train()

    elapsed_time = time.time() - start_time

    # Check if CPU time limit exceeded
    cpu_constraint_met = elapsed_time <= CPU_TIME_LIMIT_SECONDS

    if not cpu_constraint_met and not use_gpu:
        print(f"WARNING: CPU training exceeded 4-hour limit ({elapsed_time:.2f}s)")
        print("Triggering GPU escape hatch...")

        # Log the metrics before triggering
        metrics_file = Path(output_dir) / "training_metrics.json"
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            metrics["cpu_constraint_met"] = False
            metrics["elapsed_time_seconds"] = elapsed_time
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)

        # Trigger GPU escape hatch
        trigger_script = Path(__file__).parent / "trigger_gpu_run.sh"
        if trigger_script.exists():
            os.chmod(trigger_script, 0o755)
            os.system(f"bash {trigger_script}")
        else:
            print(f"ERROR: Trigger script not found at {trigger_script}")

        # Save final metrics
        final_metrics = {
            "status": "cpu_timeout_triggered_gpu_escape",
            "elapsed_time_seconds": elapsed_time,
            "cpu_constraint_met": False,
            "final_loss": trainer.state.log_history[-1].get("loss", None) if trainer.state.log_history else None,
            "timestamp": datetime.now().isoformat()
        }

        with open(metrics_file, 'w') as f:
            json.dump(final_metrics, f, indent=2)

        return False, final_metrics

    # Save final metrics
    metrics_file = Path(output_dir) / "training_metrics.json"
    final_metrics = {
        "status": "completed",
        "elapsed_time_seconds": elapsed_time,
        "cpu_constraint_met": cpu_constraint_met,
        "epochs_completed": num_epochs,
        "final_loss": trainer.state.log_history[-1].get("loss", None) if trainer.state.log_history else None,
        "timestamp": datetime.now().isoformat()
    }

    with open(metrics_file, 'w') as f:
        json.dump(final_metrics, f, indent=2)

    print(f"Training completed in {elapsed_time:.2f} seconds")
    print(f"CPU constraint met: {cpu_constraint_met}")

    return cpu_constraint_met, final_metrics

def main():
    parser = argparse.ArgumentParser(description="Train Symbolic-Guava LLM")
    parser.add_argument("--data_dir", type=str, default="data/processed/symbolic_guava",
                        help="Directory containing symbolic dataset")
    parser.add_argument("--output_dir", type=str, default="data/artifacts/trained_model",
                        help="Directory to save trained model")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed")
    parser.add_argument("--use-gpu", action="store_true", help="Use GPU for training (escape hatch)")
    parser.add_argument("--validation-only", action="store_true", help="Run validation only on GPU")
    args = parser.parse_args()

    # Setup
    set_global_seed(args.seed)
    ensure_directories([args.output_dir, "data/artifacts"])

    # Check CPU constraint
    if not args.use_gpu:
        enforce_cpu_only = True
        # In a real scenario, we would check system resources here
        # For now, we assume CPU-only unless --use-gpu is specified

    # Load dataset
    print("Loading symbolic dataset...")
    trajectories = load_symbolic_dataset(args.data_dir)
    print(f"Loaded {len(trajectories)} trajectories")

    if not trajectories:
        print("ERROR: No trajectories found. Exiting.")
        sys.exit(1)

    # Setup model and tokenizer
    print("Setting up model and tokenizer...")
    model, tokenizer, device = setup_model_and_tokenizer()
    print(f"Using device: {device}")

    # Prepare dataset
    print("Preparing training data...")
    train_dataset = prepare_training_data(trajectories, tokenizer)

    # Setup LoRA
    print("Setting up LoRA...")
    model = setup_lora(model)

    # Train
    print("Starting training...")
    success, metrics = train_model(
        model,
        train_dataset,
        args.output_dir,
        num_epochs=args.epochs,
        use_gpu=args.use_gpu,
        validation_only=args.validation_only
    )

    if success:
        print("Training completed successfully within CPU constraints.")
    else:
        print("Training exceeded CPU constraints. GPU escape hatch triggered.")

    # Save checkpoint
    checkpoint_dir = Path(args.output_dir) / "checkpoint_final"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(checkpoint_dir)
    tokenizer.save_pretrained(checkpoint_dir)
    print(f"Model saved to {checkpoint_dir}")

if __name__ == "__main__":
    main()