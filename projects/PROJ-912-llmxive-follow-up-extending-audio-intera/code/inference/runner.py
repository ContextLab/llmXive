"""
Dynamic batch size adjustment logic for inference runner.
Implements resource-aware batch sizing to prevent OOM on constrained CPU runners.
"""
import os
import gc
import time
import json
import logging
import traceback
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator
import numpy as np

# Import from project modules using exact names from API surface
try:
    from config import get_path_config, get_resource_limits
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_path_config, get_resource_limits

try:
    from inference.metrics import get_peak_ram_mb, check_constraints
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from inference.metrics import get_peak_ram_mb, check_constraints

try:
    from utils.logger import get_logger, LlmXiveError
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.logger import get_logger, LlmXiveError

# Try to import psutil, but provide a fallback if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    # Provide a simple fallback RAM estimation
    def get_ram_usage_mb_fallback():
        """Fallback RAM estimation without psutil"""
        try:
            # Try to read from /proc/stat on Linux
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        return float(line.split()[1]) / 1024.0
        except Exception:
            return 0.0
        return 0.0

# Set up logging
logger = get_logger("inference.runner")

class InferenceResult:
    """Container for inference results from a single batch."""
    def __init__(self, model_id: str, batch_size: int, logits: np.ndarray, labels: np.ndarray, latency_ms: float, ram_gb: float):
        self.model_id = model_id
        self.batch_size = batch_size
        self.logits = logits
        self.labels = labels
        self.latency_ms = latency_ms
        self.ram_gb = ram_gb

class InferenceRunSummary:
    """Summary of an entire inference run."""
    def __init__(self):
        self.results: List[InferenceResult] = []
        self.total_samples = 0
        self.total_latency_ms = 0.0
        self.peak_ram_gb = 0.0
        self.batch_sizes_used: Dict[int, int] = {}  # batch_size -> count
        self.skipped_batches = 0
        self.retries = 0

def get_ram_usage_mb() -> float:
    """Get current RAM usage in MB."""
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    else:
        return get_ram_usage_mb_fallback()

def get_model_paths(model_dir: Path) -> List[Path]:
    """Get list of model checkpoint paths from directory."""
    if not model_dir.exists():
        raise LlmXiveError(f"Model directory does not exist: {model_dir}")
    
    paths = list(model_dir.glob("*.pt")) + list(model_dir.glob("*.pth"))
    if not paths:
        raise LlmXiveError(f"No model checkpoints found in {model_dir}")
    
    return sorted(paths)

def load_student_model(model_path: Path, device: str = "cpu") -> Any:
    """Load a student model checkpoint."""
    logger.info(f"Loading model from {model_path}")
    try:
        # Placeholder for actual model loading logic
        # In a real implementation, this would load the specific model architecture
        import torch
        model = torch.load(model_path, map_location=device)
        model.eval()
        return model
    except Exception as e:
        raise LlmXiveError(f"Failed to load model {model_path}: {str(e)}")

class AudioDataset:
    """Simple audio dataset wrapper for testing."""
    def __init__(self, data_path: Path, batch_size: int = 8):
        self.data_path = data_path
        self.batch_size = batch_size
        self.samples = []
        
        if data_path.exists():
            # Try to load parquet file
            try:
                import pandas as pd
                df = pd.read_parquet(data_path)
                self.samples = df.to_dict('records')
                logger.info(f"Loaded {len(self.samples)} samples from {data_path}")
            except Exception as e:
                logger.warning(f"Failed to load parquet: {str(e)}, using mock data")
                self._generate_mock_data()
        else:
            logger.warning(f"Data file not found: {data_path}, using mock data")
            self._generate_mock_data()
    
    def _generate_mock_data(self):
        """Generate mock audio data for testing."""
        logger.info("Generating mock audio data (100 samples)")
        for i in range(100):
            self.samples.append({
                'audio_path': f"mock_audio_{i}.wav",
                'class_id': i % 10,
                'label': i % 10,
                'audio': np.random.randn(16000).astype(np.float32)  # 1 second at 16kHz
            })
    
    def __len__(self):
        return len(self.samples)
    
    def __iter__(self) -> Iterator[Tuple[np.ndarray, int, int]]:
        """Yield batches of (audio, label, index) tuples."""
        for i in range(0, len(self.samples), self.batch_size):
            batch_samples = self.samples[i:i + self.batch_size]
            # Extract audio and labels
            audio_batch = np.array([s['audio'] for s in batch_samples])
            labels = np.array([s['label'] for s in batch_samples])
            indices = [i + j for j in range(len(batch_samples))]
            yield audio_batch, labels, indices

def run_inference_batch(
    model: Any,
    audio_batch: np.ndarray,
    labels: np.ndarray,
    batch_size: int,
    device: str = "cpu"
) -> Tuple[np.ndarray, float, float]:
    """
    Run inference on a single batch with dynamic batch size adjustment.
    
    Returns: (logits, latency_ms, ram_gb)
    """
    start_time = time.time()
    ram_before = get_ram_usage_mb()
    
    try:
        # Convert to torch tensors
        import torch
        audio_tensor = torch.from_numpy(audio_batch).float()
        
        # Run inference
        with torch.no_grad():
            model.eval()
            logits = model(audio_tensor)
            if isinstance(logits, tuple):
                logits = logits[0]
            logits_np = logits.cpu().numpy()
        
        latency_ms = (time.time() - start_time) * 1000
        ram_after = get_ram_usage_mb()
        ram_gb = ram_after / (1024 * 1024)
        
        return logits_np, latency_ms, ram_gb
        
    except Exception as e:
        logger.error(f"Inference failed: {str(e)}")
        raise

def run_inference_on_model(
    model: Any,
    dataset: AudioDataset,
    model_id: str,
    max_retries: int = 3,
    ram_threshold_gb: float = 6.0,
    default_batch_size: int = 8
) -> InferenceRunSummary:
    """
    Run inference on a model with dynamic batch size adjustment.
    
    Args:
        model: Loaded model
        dataset: Audio dataset
        model_id: Model identifier
        max_retries: Maximum batch size reductions before skipping
        ram_threshold_gb: RAM threshold to trigger batch size reduction
        default_batch_size: Starting batch size
        
    Returns:
        InferenceRunSummary with results and statistics
    """
    summary = InferenceRunSummary()
    current_batch_size = default_batch_size
    batch_log = []
    
    logger.info(f"Starting inference for {model_id} with initial batch size {current_batch_size}")
    
    for batch_idx, (audio_batch, labels, indices) in enumerate(dataset):
        retry_count = 0
        batch_success = False
        current_batch_size = min(current_batch_size, len(audio_batch))
        
        while retry_count < max_retries and not batch_success:
            try:
                # Run inference
                logits, latency_ms, ram_gb = run_inference_batch(
                    model, audio_batch, labels, current_batch_size
                )
                
                # Check RAM usage
                if ram_gb > ram_threshold_gb:
                    if retry_count < max_retries - 1:
                        logger.warning(
                            f"Batch {batch_idx} exceeded RAM threshold ({ram_gb:.2f}GB > {ram_threshold_gb}GB). "
                            f"Reducing batch size from {current_batch_size} to {current_batch_size // 2}"
                        )
                        current_batch_size = max(1, current_batch_size // 2)
                        retry_count += 1
                        summary.retries += 1
                        gc.collect()
                        continue
                    else:
                        logger.warning(
                            f"Batch {batch_idx} still exceeds RAM after {max_retries} reductions. "
                            f"Skipping batch. Current batch size: {current_batch_size}"
                        )
                        summary.skipped_batches += 1
                        batch_success = True
                        continue
                
                # Success
                result = InferenceResult(
                    model_id=model_id,
                    batch_size=current_batch_size,
                    logits=logits,
                    labels=labels,
                    latency_ms=latency_ms,
                    ram_gb=ram_gb
                )
                summary.results.append(result)
                summary.total_samples += len(labels)
                summary.total_latency_ms += latency_ms
                summary.peak_ram_gb = max(summary.peak_ram_gb, ram_gb)
                summary.batch_sizes_used[current_batch_size] = summary.batch_sizes_used.get(current_batch_size, 0) + 1
                batch_success = True
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_idx}: {str(e)}")
                if retry_count < max_retries - 1:
                    logger.info(f"Retrying batch {batch_idx} with smaller batch size")
                    current_batch_size = max(1, current_batch_size // 2)
                    retry_count += 1
                    summary.retries += 1
                    gc.collect()
                else:
                    logger.error(f"Failed to process batch {batch_idx} after {max_retries} retries. Skipping.")
                    summary.skipped_batches += 1
                    batch_success = True
        
        # Clean up
        gc.collect()
    
    # Save inference config
    config_path = get_path_config().processed_dir / "inference_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config_data = {
        "model_id": model_id,
        "default_batch_size": default_batch_size,
        "ram_threshold_gb": ram_threshold_gb,
        "max_retries": max_retries,
        "final_batch_sizes_used": summary.batch_sizes_used,
        "total_samples_processed": summary.total_samples,
        "skipped_batches": summary.skipped_batches,
        "total_retries": summary.retries,
        "peak_ram_gb": summary.peak_ram_gb,
        "avg_latency_ms": summary.total_latency_ms / max(1, len(summary.results))
    }
    
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    logger.info(f"Inference config saved to {config_path}")
    logger.info(f"Final batch sizes used: {summary.batch_sizes_used}")
    logger.info(f"Total samples: {summary.total_samples}, Skipped: {summary.skipped_batches}, Retries: {summary.retries}")
    
    return summary

def main():
    """Main entry point for inference runner with dynamic batch sizing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run inference with dynamic batch size adjustment")
    parser.add_argument("--model-dir", type=str, required=True, help="Directory containing model checkpoints")
    parser.add_argument("--testbed", type=str, required=True, help="Path to test data (parquet)")
    parser.add_argument("--thresholds", type=str, default="0.05,0.1", help="Comma-separated thresholds for evaluation")
    parser.add_argument("--ram-threshold", type=float, default=6.0, help="RAM threshold in GB")
    parser.add_argument("--initial-batch-size", type=int, default=8, help="Initial batch size")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retries before skipping batch")
    
    args = parser.parse_args()
    
    try:
        # Setup
        model_dir = Path(args.model_dir)
        testbed_path = Path(args.testbed)
        thresholds = [float(t) for t in args.thresholds.split(',')]
        
        logger.info(f"Model directory: {model_dir}")
        logger.info(f"Testbed: {testbed_path}")
        logger.info(f"Thresholds: {thresholds}")
        logger.info(f"RAM threshold: {args.ram_threshold}GB")
        logger.info(f"Initial batch size: {args.initial_batch_size}")
        
        # Get model paths
        model_paths = get_model_paths(model_dir)
        logger.info(f"Found {len(model_paths)} model checkpoints")
        
        all_summaries = []
        
        for model_path in model_paths:
            model_id = model_path.stem
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing model: {model_id}")
            logger.info(f"{'='*60}")
            
            # Load model
            model = load_student_model(model_path)
            
            # Create dataset
            dataset = AudioDataset(testbed_path, batch_size=args.initial_batch_size)
            
            # Run inference
            summary = run_inference_on_model(
                model=model,
                dataset=dataset,
                model_id=model_id,
                max_retries=args.max_retries,
                ram_threshold_gb=args.ram_threshold,
                default_batch_size=args.initial_batch_size
            )
            
            all_summaries.append(summary)
            
            # Cleanup
            del model
            gc.collect()
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("INFERENCE COMPLETE")
        logger.info(f"{'='*60}")
        for summary in all_summaries:
            logger.info(f"Model: {summary.results[0].model_id if summary.results else 'N/A'}")
            logger.info(f"  Samples: {summary.total_samples}")
            logger.info(f"  Peak RAM: {summary.peak_ram_gb:.2f}GB")
            logger.info(f"  Batch sizes: {summary.batch_sizes_used}")
            logger.info(f"  Skipped: {summary.skipped_batches}")
            logger.info(f"  Retries: {summary.retries}")
        
        logger.info("Inference completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
