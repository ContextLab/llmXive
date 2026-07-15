import os
import sys
import csv
import json
import time
import torch
import torch.nn as nn
from typing import List, Dict, Any, Tuple, Optional

# Local imports based on provided API surface
from config import Config, get_config
from models.student import DistilBERTStudent, create_student_model
from models.teacher import Teacher
from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger
from utils.resource_monitor import ResourceMonitor
from analysis.metrics import compute_trace_entropy

logger = get_logger(__name__)

def load_dataset_from_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load a dataset from a CSV file into a list of dictionaries."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")
    
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields back to appropriate types
            if 'entropy_level' in row:
                row['entropy_level'] = row['entropy_level']
            # premises and operators are stored as JSON strings or comma-separated
            if 'premises' in row and row['premises']:
                try:
                    row['premises'] = json.loads(row['premises'])
                except (json.JSONDecodeError, TypeError):
                    row['premises'] = row['premises'].split(',') if row['premises'] else []
            
            if 'operators' in row and row['operators']:
                try:
                    row['operators'] = json.loads(row['operators'])
                except (json.JSONDecodeError, TypeError):
                    row['operators'] = row['operators'].split(',') if row['operators'] else []
            
            data.append(row)
    return data

def prepare_input_from_problem(problem: SyntheticProblem) -> torch.Tensor:
    """Convert a SyntheticProblem into a tensor input for the student model."""
    # Simple encoding: concatenate premises and solution into a single string
    # then tokenize (mock implementation for CPU tractability)
    text = " ".join(problem.premises) + " " + problem.solution
    # In a real scenario, we would use a tokenizer. 
    # Here we create a dummy tensor of fixed size for the loop to run.
    # The student model expects an input_ids tensor.
    dummy_input = torch.randint(0, 1000, (1, 10)) # Batch size 1, Seq len 10
    return dummy_input

def prepare_teacher_output(problem: SyntheticProblem, teacher: Teacher) -> torch.Tensor:
    """Generate teacher output (soft labels) for a given problem."""
    trace = teacher.generate_trace(problem)
    # Convert trace to a probability distribution (mock)
    # In reality, this would be logits from the teacher model
    num_classes = 10
    logits = torch.randn(1, num_classes)
    return logits

def kl_divergence_loss(student_logits: torch.Tensor, teacher_logits: torch.Tensor, temperature: float = 1.0) -> torch.Tensor:
    """Compute KL divergence loss between student and teacher outputs."""
    student_probs = torch.softmax(student_logits / temperature, dim=-1)
    teacher_probs = torch.softmax(teacher_logits / temperature, dim=-1)
    kl = nn.KLDivLoss(reduction='batchmean')(torch.log(student_probs + 1e-9), teacher_probs)
    return kl

def train_epoch(
    model: nn.Module, 
    dataloader: List[Dict[str, Any]], 
    teacher: Teacher, 
    optimizer: torch.optim.Optimizer, 
    epoch: int, 
    max_ram_gb: float,
    max_runtime_seconds: float
) -> Tuple[float, bool]:
    """Train the model for one epoch with resource monitoring."""
    model.train()
    total_loss = 0.0
    count = 0
    start_time = time.time()
    
    # We assume the ResourceMonitor is started externally or here if not already
    # For this function, we check the global monitor state if available, 
    # but the main loop handles the enforcement.
    
    for i, raw_problem in enumerate(dataloader):
        # Check runtime limit
        elapsed = time.time() - start_time
        if elapsed > max_runtime_seconds:
            logger.warning(f"Epoch {epoch} exceeded time limit ({elapsed:.1f}s > {max_runtime_seconds}s). Stopping.")
            return total_loss / max(count, 1), False

        # Reconstruct problem object if needed, or use raw dict
        # Assuming raw_problem is already a dict with necessary fields
        # We need to convert it to SyntheticProblem if the model expects it
        # For this mock, we pass the dict directly to helpers that handle it
        
        try:
            # Mock reconstruction for type safety in helpers if they expect class
            # In a real impl, we'd parse the dict into SyntheticProblem
            problem = SyntheticProblem(
                id=raw_problem.get('id', str(i)),
                premises=raw_problem.get('premises', []),
                operators=raw_problem.get('operators', []),
                solution=raw_problem.get('solution', ''),
                entropy_level=raw_problem.get('entropy_level', 'unknown'),
                metadata=raw_problem.get('metadata', {})
            )
        except Exception as e:
            logger.error(f"Failed to reconstruct problem: {e}")
            continue

        inputs = prepare_input_from_problem(problem)
        teacher_logits = prepare_teacher_output(problem, teacher)
        
        optimizer.zero_grad()
        student_logits = model(inputs)
        loss = kl_divergence_loss(student_logits, teacher_logits)
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        count += 1

    return total_loss / max(count, 1), True

def run_distillation(
    dataset_path: str, 
    output_path: str, 
    config: Config, 
    max_epochs: int = 10,
    early_stop_threshold: float = 0.1
) -> Dict[str, Any]:
    """Run the full distillation loop with resource constraints."""
    logger.info(f"Starting distillation on {dataset_path}")
    
    # Load dataset
    data = load_dataset_from_csv(dataset_path)
    if not data:
        raise ValueError("Dataset is empty or failed to load.")
    
    # Initialize models
    student = create_student_model()
    teacher = Teacher()
    optimizer = torch.optim.Adam(student.parameters(), lr=0.001)
    
    # Resource Monitoring Setup
    monitor = ResourceMonitor()
    monitor.start()
    
    start_time = time.time()
    max_runtime_seconds = config.max_runtime_hours * 3600
    peak_ram = 0.0
    convergence_epoch = -1
    final_accuracy = 0.0
    status = "running"
    
    try:
        for epoch in range(max_epochs):
            # Check global time limit
            elapsed = time.time() - start_time
            if elapsed > max_runtime_seconds:
                logger.error(f"Total runtime exceeded limit ({elapsed:.1f}s > {max_runtime_seconds}s).")
                status = "failed_timeout"
                break

            # Check RAM limit
            current_ram = monitor.get_peak_ram_gb()
            if current_ram > max_ram_gb:
                logger.error(f"RAM usage exceeded limit: {current_ram:.2f}GB > {max_ram_gb}GB.")
                status = "failed_ram_limit"
                break

            avg_loss, completed = train_epoch(
                student, data, teacher, optimizer, epoch, 
                config.max_ram_gb, max_runtime_seconds - elapsed
            )
            
            if not completed:
                logger.info(f"Epoch {epoch} stopped early due to time limit.")
                break

            logger.info(f"Epoch {epoch}: Loss = {avg_loss:.4f}")
            
            if avg_loss <= early_stop_threshold:
                convergence_epoch = epoch
                status = "converged"
                logger.info(f"Converged at epoch {epoch} with loss {avg_loss:.4f}")
                break
        
        if status == "running":
            status = "completed_max_epochs"
            convergence_epoch = max_epochs + 1 # Indicate no convergence within limit

        # Final resource check
        monitor.stop()
        peak_ram = monitor.get_peak_ram_gb()

    except Exception as e:
        logger.error(f"Distillation failed with exception: {e}")
        status = "failed_exception"
        monitor.stop()
        raise e

    # Save results
    result = {
        "run_id": os.path.basename(dataset_path).replace('.csv', ''),
        "entropy_subset": "unknown", # Should be parsed from path or data
        "model_params": str(config.seed),
        "training_loss_curve": [], # In a real impl, store history
        "convergence_epoch": convergence_epoch,
        "final_accuracy": final_accuracy,
        "status": status,
        "resource_usage": {
            "peak_ram_gb": peak_ram,
            "total_runtime_seconds": time.time() - start_time
        }
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Distillation complete. Results saved to {output_path}")
    return result

def main():
    """Entry point for the distillation script."""
    import argparse
    parser = argparse.ArgumentParser(description="Run Distillation Loop")
    parser.add_argument("--dataset", type=str, required=True, help="Path to input CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    parser.add_argument("--max_epochs", type=int, default=10)
    args = parser.parse_args()

    config = get_config()
    
    # Enforce limits via ResourceMonitor hooks as per T025
    # The run_distillation function handles the checks, but we ensure the monitor is active.
    
    try:
        run_distillation(
            dataset_path=args.dataset,
            output_path=args.output,
            config=config,
            max_epochs=args.max_epochs
        )
        sys.exit(0)
    except Exception as e:
        logger.error(f"Script failed: {e}")
        # Specific error code for resource breach or other failures
        # 1: General failure, 2: RAM limit, 3: Time limit
        # The run_distillation sets status, but we exit with 1 for any exception here
        sys.exit(1)

if __name__ == "__main__":
    main()
