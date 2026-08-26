import os
import sys
import csv
import json
import time
import torch
from typing import List, Dict, Any, Optional, Tuple

# Local imports
from models.student import DistilBERTStudent, create_student_model
from models.teacher import Teacher
from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger
from utils.resource_monitor import ResourceMonitor
from config import get_config, Config

logger = get_logger(__name__)

def load_dataset_from_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load dataset from CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")
    
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert premises/operators strings back to lists if needed
            if 'premises' in row:
                try:
                    row['premises'] = json.loads(row['premises'])
                except (json.JSONDecodeError, TypeError):
                    row['premises'] = row['premises'].split('|||') if row['premises'] else []
            
            if 'operators' in row:
                try:
                    row['operators'] = json.loads(row['operators'])
                except (json.JSONDecodeError, TypeError):
                    row['operators'] = row['operators'].split('|||') if row['operators'] else []
            
            data.append(row)
    
    return data

def prepare_input_from_problem(problem: Dict[str, Any]) -> Dict[str, torch.Tensor]:
    """Prepare input tensors from a problem dictionary."""
    # Simple tokenization for demonstration - in real impl, use tokenizer
    premises_text = " ".join(problem.get('premises', []))
    operators_text = " ".join(problem.get('operators', []))
    full_text = f"{premises_text} {operators_text}"
    
    # Create dummy input tensors (shape: [batch_size, seq_len])
    # In real implementation, use actual tokenizer
    input_ids = torch.randint(0, 1000, (1, 64))
    attention_mask = torch.ones((1, 64))
    
    return {
        'input_ids': input_ids,
        'attention_mask': attention_mask
    }

def prepare_teacher_output(problem: Dict[str, Any], teacher: Teacher) -> Dict[str, torch.Tensor]:
    """Prepare teacher output (logits/probabilities) for a problem."""
    # Generate trace and probabilities using teacher
    synthetic_prob = SyntheticProblem(
        id=problem['id'],
        premises=problem.get('premises', []),
        operators=problem.get('operators', []),
        solution=problem.get('solution', ''),
        entropy_level=problem.get('entropy_level', 'medium'),
        metadata=problem.get('metadata', {})
    )
    
    trace, probs = teacher.generate_trace(synthetic_prob)
    
    # Convert probabilities to tensor
    # Shape: [seq_len, vocab_size] - simplified to [seq_len] for demo
    probs_tensor = torch.tensor(probs, dtype=torch.float32)
    
    return {
        'teacher_logits': probs_tensor,
        'trace': trace
    }

def kl_divergence_loss(student_logits: torch.Tensor, teacher_logits: torch.Tensor, temperature: float = 1.0) -> torch.Tensor:
    """Compute KL divergence loss between student and teacher outputs."""
    # Apply temperature scaling
    student_soft = torch.softmax(student_logits / temperature, dim=-1)
    teacher_soft = torch.softmax(teacher_logits / temperature, dim=-1)
    
    # KL divergence: sum(teacher * log(teacher / student))
    kl = torch.sum(teacher_soft * torch.log(teacher_soft / (student_soft + 1e-8)), dim=-1)
    return kl.mean()

def train_epoch(
    model: torch.nn.Module,
    dataloader: List[Dict[str, Any]],
    teacher: Teacher,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    config: Config
) -> Tuple[float, int]:
    """Train one epoch and return average loss and sample count."""
    model.train()
    total_loss = 0.0
    count = 0
    
    for problem in dataloader:
        # Prepare inputs
        inputs = prepare_input_from_problem(problem)
        teacher_output = prepare_teacher_output(problem, teacher)
        
        # Move to device
        inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
        teacher_logits = teacher_output['teacher_logits'].to(device)
        
        # Forward pass
        optimizer.zero_grad()
        outputs = model(**inputs)
        
        # Get student logits (simplified - in real impl, extract from SequenceClassifierOutput)
        if hasattr(outputs, 'logits'):
            student_logits = outputs.logits
        else:
            student_logits = outputs if isinstance(outputs, torch.Tensor) else outputs[0]
        
        # Compute loss
        loss = kl_divergence_loss(student_logits, teacher_logits)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        count += 1
        
        # Check resource limits periodically
        if count % 10 == 0:
            # Resource monitoring is handled at the loop level
            pass
    
    return total_loss / max(count, 1), count

def run_distillation(
    dataset_path: str,
    output_path: str,
    subset_name: str,
    config: Config,
    max_epochs: int = 100,
    loss_threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Run the distillation process with resource monitoring.
    
    Enforces:
    - RAM ceiling (max_ram_gb from Config)
    - Wall-clock time limit (max_runtime_hours from Config)
    - Early stopping if loss <= loss_threshold
    
    Returns a dictionary with run statistics and status.
    """
    logger.info(f"Starting distillation for subset: {subset_name}")
    logger.info(f"Dataset path: {dataset_path}")
    logger.info(f"Output path: {output_path}")
    
    # Initialize resource monitor
    monitor = ResourceMonitor()
    start_time = time.time()
    max_runtime_seconds = config.max_runtime_hours * 3600
    ram_limit_gb = config.max_ram_gb
    
    # Load dataset
    try:
        dataset = load_dataset_from_csv(dataset_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load dataset: {e}")
        return {
            'status': 'failed',
            'error': f'Dataset not found: {dataset_path}',
            'subset': subset_name,
            'run_id': f'{subset_name}_{int(start_time)}'
        }
    
    if not dataset:
        logger.error("Dataset is empty")
        return {
            'status': 'failed',
            'error': 'Empty dataset',
            'subset': subset_name,
            'run_id': f'{subset_name}_{int(start_time)}'
        }
    
    logger.info(f"Loaded {len(dataset)} samples")
    
    # Initialize teacher and student
    teacher = Teacher()
    student = create_student_model()
    
    # Use CPU only (per US2 requirements)
    device = torch.device('cpu')
    student.to(device)
    
    # Optimizer
    optimizer = torch.optim.Adam(student.parameters(), lr=1e-4)
    
    # Tracking variables
    best_loss = float('inf')
    convergence_epoch = max_epochs + 1
    training_log = []
    epoch_loss = []
    
    # Start resource monitoring
    monitor.start()
    
    try:
        for epoch in range(max_epochs):
            # Check time limit
            elapsed = time.time() - start_time
            if elapsed > max_runtime_seconds:
                logger.warning(f"Time limit exceeded: {elapsed:.2f}s > {max_runtime_seconds:.2f}s")
                raise TimeoutError(f"Training exceeded time limit ({config.max_runtime_hours}h)")
            
            # Check RAM limit
            current_ram = monitor.get_peak_ram_gb()
            if current_ram > ram_limit_gb:
                logger.warning(f"RAM limit exceeded: {current_ram:.2f}GB > {ram_limit_gb}GB")
                raise MemoryError(f"Training exceeded RAM limit ({config.max_ram_gb}GB)")
            
            # Train one epoch
            avg_loss, sample_count = train_epoch(
                student, dataset, teacher, optimizer, device, config
            )
            epoch_loss.append(avg_loss)
            
            logger.info(f"Epoch {epoch+1}/{max_epochs}: Loss={avg_loss:.4f}, Samples={sample_count}")
            
            # Track best loss
            if avg_loss < best_loss:
                best_loss = avg_loss
            
            # Check for convergence
            if avg_loss <= loss_threshold:
                convergence_epoch = epoch + 1
                logger.info(f"Converged at epoch {convergence_epoch} with loss {avg_loss:.4f}")
                break
            
            training_log.append({
                'epoch': epoch + 1,
                'loss': avg_loss,
                'samples': sample_count,
                'timestamp': time.time()
            })
            
            # Periodic resource check
            if (epoch + 1) % 10 == 0:
                current_ram = monitor.get_peak_ram_gb()
                logger.info(f"Epoch {epoch+1}: Peak RAM={current_ram:.2f}GB, Elapsed={elapsed:.2f}s")
    
    except (MemoryError, TimeoutError) as e:
        logger.error(f"Training failed due to resource constraint: {e}")
        monitor.stop()
        return {
            'status': 'failed',
            'error': str(e),
            'subset': subset_name,
            'run_id': f'{subset_name}_{int(start_time)}',
            'peak_ram_gb': monitor.get_peak_ram_gb(),
            'elapsed_seconds': time.time() - start_time,
            'epochs_completed': len(epoch_loss),
            'final_loss': epoch_loss[-1] if epoch_loss else None
        }
    except Exception as e:
        logger.error(f"Training failed with unexpected error: {e}", exc_info=True)
        monitor.stop()
        return {
            'status': 'failed',
            'error': str(e),
            'subset': subset_name,
            'run_id': f'{subset_name}_{int(start_time)}',
            'peak_ram_gb': monitor.get_peak_ram_gb(),
            'elapsed_seconds': time.time() - start_time,
            'epochs_completed': len(epoch_loss),
            'final_loss': epoch_loss[-1] if epoch_loss else None
        }
    finally:
        monitor.stop()
    
    # Final resource report
    final_ram = monitor.get_peak_ram_gb()
    final_time = time.time() - start_time
    
    logger.info(f"Distillation completed for {subset_name}")
    logger.info(f"Final loss: {best_loss:.4f}, Convergence epoch: {convergence_epoch}")
    logger.info(f"Peak RAM: {final_ram:.2f}GB, Total time: {final_time:.2f}s")
    
    # Prepare result
    result = {
        'run_id': f'{subset_name}_{int(start_time)}',
        'subset': subset_name,
        'status': 'converged' if convergence_epoch <= max_epochs else 'failed_non_converge',
        'convergence_epoch': convergence_epoch,
        'final_loss': best_loss,
        'total_epochs': len(epoch_loss),
        'peak_ram_gb': final_ram,
        'elapsed_seconds': final_time,
        'max_ram_gb': ram_limit_gb,
        'max_runtime_hours': config.max_runtime_hours,
        'training_log': training_log,
        'loss_curve': epoch_loss,
        'timestamp': time.time()
    }
    
    # Save result to output path
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    return result

def main():
    """Main entry point for distillation loop."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run distillation with resource monitoring')
    parser.add_argument('--input', type=str, required=True, help='Path to input CSV dataset')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON results')
    parser.add_argument('--subset', type=str, default='default', help='Subset name for logging')
    parser.add_argument('--max-epochs', type=int, default=100, help='Maximum training epochs')
    parser.add_argument('--loss-threshold', type=float, default=0.1, help='Loss threshold for early stopping')
    
    args = parser.parse_args()
    config = get_config()
    
    result = run_distillation(
        dataset_path=args.input,
        output_path=args.output,
        subset_name=args.subset,
        config=config,
        max_epochs=args.max_epochs,
        loss_threshold=args.loss_threshold
    )
    
    # Exit with appropriate code
    if result['status'] == 'failed':
        error_type = result.get('error', 'Unknown error')
        if 'RAM' in error_type or 'MemoryError' in error_type:
            sys.exit(2)  # Resource limit exceeded
        elif 'time' in error_type.lower() or 'TimeoutError' in error_type:
            sys.exit(3)  # Time limit exceeded
        else:
            sys.exit(1)  # General failure
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()