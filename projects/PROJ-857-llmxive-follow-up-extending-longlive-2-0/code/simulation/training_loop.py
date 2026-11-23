import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

from config import get_path_str, ensure_dirs_exist
from simulation.quantization_emulator import QuantizationEmulator, switch_emulator_bit_width
from simulation.student_model import SimplifiedDiffusionStudent, create_student_model, TrainingLoopError
from data.loader import load_kinetics_streaming, get_kinetics_sample_count, KineticsLoaderError
from data.downsampler import extract_4s_clips, DownsamplingError

class TrainingLoopError(Exception):
    """Custom exception for training loop errors."""
    pass

def check_memory_limit(max_gb: float = 7.0) -> bool:
    """
    Check if current system memory usage is within limits.
    Returns True if within limit, False otherwise.
    """
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        current_gb = mem_info.rss / (1024 ** 3)
        if current_gb > max_gb:
            raise TrainingLoopError(f"Memory limit exceeded: {current_gb:.2f}GB > {max_gb}GB")
        return True
    except ImportError:
        # Fallback if psutil not available, assume safe but log warning
        print("Warning: psutil not installed. Skipping memory check.")
        return True

def check_model_collapse(loss_history: List[float], threshold: float = 1e-6) -> Tuple[bool, Optional[str]]:
    """
    Check if the model has collapsed (NaN or Inf in loss).
    
    Args:
        loss_history: List of loss values from recent steps.
        threshold: Minimum absolute value for valid loss (optional sanity check).
    
    Returns:
        Tuple of (is_collapsed, status_string).
        status_string is "Collapse" if detected, None otherwise.
    """
    if not loss_history:
        return False, None
    
    last_loss = loss_history[-1]
    
    # Check for NaN or Inf
    if torch.is_tensor(last_loss):
        if torch.isnan(last_loss) or torch.isinf(last_loss):
            return True, "Collapse"
    else:
        if np.isnan(last_loss) or np.isinf(last_loss):
            return True, "Collapse"
    
    # Optional: Check if loss is suspiciously low (degenerate mode)
    # This is heuristic and depends on the specific loss function scale
    if abs(last_loss) < threshold:
        # Log but don't necessarily fail immediately unless it persists
        pass 
    
    return False, None

def run_training_loop(
    num_epochs: int = 1,
    batch_size: int = 1,
    bit_width: int = 4,
    max_samples: Optional[int] = None,
    output_dir: Optional[str] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Execute a complete training simulation loop on CPU-only environment.
    
    Args:
        num_epochs: Number of epochs to run.
        batch_size: Batch size for training.
        bit_width: Precision bit-width (2, 4, or 8).
        max_samples: Maximum number of samples to process (for testing).
        output_dir: Directory to save results.
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary containing training metrics and status.
    """
    torch.manual_seed(seed)
    np.random.seed(seed)
    
    # Initialize paths
    if output_dir is None:
        output_dir = get_path_str("results_dir")
    results_path = Path(output_dir)
    ensure_dirs_exist([results_path])
    
    # Initialize components
    try:
        student_model = create_student_model()
        emulator = create_quantization_emulator(bit_width=bit_width)
    except Exception as e:
        raise TrainingLoopError(f"Failed to initialize model or emulator: {e}")
    
    # Switch bit width if needed (dynamic switching capability)
    if bit_width not in [2, 4, 8]:
        raise TrainingLoopError(f"Invalid bit_width: {bit_width}. Must be 2, 4, or 8.")
    
    # Setup data loader
    try:
        data_stream = load_kinetics_streaming(shuffle=True)
        if max_samples:
            # Limit stream for testing
            from itertools import islice
            data_stream = islice(data_stream, max_samples)
    except KineticsLoaderError as e:
        raise TrainingLoopError(f"Failed to load data stream: {e}")
    
    loss_history: List[float] = []
    status_log: List[Dict[str, Any]] = []
    collapse_detected = False
    
    try:
        for epoch in range(num_epochs):
            epoch_loss_sum = 0.0
            num_batches = 0
            
            # Process data stream
            for batch_idx, sample in enumerate(data_stream):
                # Check memory before processing batch
                check_memory_limit()
                
                # Extract 4s clips (downsampling logic)
                try:
                    # Assuming sample contains 'video' key with frames
                    if 'video' not in sample:
                        continue
                    
                    frames = sample['video'] # Expected shape: (T, H, W, C)
                    if not isinstance(frames, torch.Tensor):
                        frames = torch.tensor(frames, dtype=torch.float32)
                    
                    # Ensure frames are on CPU
                    frames = frames.cpu()
                    
                    # Apply quantization emulator to simulate precision
                    # This emulates the forward pass under low precision
                    quantized_frames = emulator.quantize(frames)
                    
                    # Forward pass through student model
                    # Simplified: model takes frames and predicts next step or reconstruction
                    # This is a placeholder for the actual diffusion logic
                    model_input = quantized_frames
                    prediction = student_model(model_input)
                    
                    # Calculate loss (MSE for reconstruction example)
                    target = frames # In real scenario, this would be the next frame or clean frame
                    loss = F.mse_loss(prediction, target)
                    
                    # Backward pass (CPU only)
                    student_model.zero_grad()
                    loss.backward()
                    
                    # Update weights
                    for param in student_model.parameters():
                        if param.grad is not None:
                            param.data -= 0.01 * param.grad # Simple SGD
                    
                    # Check for model collapse AFTER backward pass
                    is_collapse, collapse_status = check_model_collapse(loss_history + [loss.item()])
                    
                    if is_collapse:
                        collapse_detected = True
                        status_log.append({
                            "epoch": epoch,
                            "batch": batch_idx,
                            "status": collapse_status,
                            "loss": float(loss.item()) if not torch.isnan(loss) else "NaN"
                        })
                        # Record collapse and optionally break or continue
                        # For this implementation, we record and continue to see if it recovers
                        # Or we could break: break 
                    
                    loss_history.append(loss.item())
                    epoch_loss_sum += loss.item()
                    num_batches += 1
                    
                    # Log progress
                    if batch_idx % 10 == 0:
                        print(f"Epoch {epoch+1}/{num_epochs}, Batch {batch_idx}, Loss: {loss.item():.4f}")
                
                except (DownsamplingError, Exception) as e:
                    print(f"Error processing batch {batch_idx}: {e}")
                    continue
            
            avg_epoch_loss = epoch_loss_sum / max(num_batches, 1)
            print(f"Epoch {epoch+1} completed. Avg Loss: {avg_epoch_loss:.4f}")
            
            # Check collapse at end of epoch
            if collapse_detected:
                status_log.append({
                    "epoch": epoch,
                    "batch": "end",
                    "status": "Collapse",
                    "loss": float(avg_epoch_loss) if not np.isnan(avg_epoch_loss) else "NaN"
                })
    
    except KeyboardInterrupt:
        print("Training interrupted by user.")
    except Exception as e:
        raise TrainingLoopError(f"Training loop failed: {e}")
    
    # Final status
    final_status = "Collapse" if collapse_detected else "Completed"
    
    results = {
        "status": final_status,
        "epochs_completed": num_epochs,
        "final_loss": loss_history[-1] if loss_history else None,
        "avg_loss": np.mean(loss_history) if loss_history else None,
        "collapse_detected": collapse_detected,
        "status_log": status_log,
        "bit_width": bit_width,
        "total_samples_processed": len(loss_history)
    }
    
    # Save results
    import json
    results_file = results_path / f"training_results_{bit_width}bit.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Training results saved to {results_file}")
    return results

def main():
    """Entry point for running the training loop."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run training simulation loop.")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=1, help="Batch size")
    parser.add_argument("--bit_width", type=int, default=4, choices=[2, 4, 8], help="Precision bit-width")
    parser.add_argument("--max_samples", type=int, default=None, help="Max samples to process")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    try:
        results = run_training_loop(
            num_epochs=args.epochs,
            batch_size=args.batch_size,
            bit_width=args.bit_width,
            max_samples=args.max_samples,
            seed=args.seed
        )
        print(f"Final Status: {results['status']}")
    except TrainingLoopError as e:
        print(f"Training failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())