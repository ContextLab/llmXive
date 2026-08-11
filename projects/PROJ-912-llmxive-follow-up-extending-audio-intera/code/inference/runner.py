"""
CPU Inference Runner for llmXive Audio Interaction Model.

Implements batch processing to fit RAM constraints and handles OOM gracefully.
Reads model checkpoints and runs inference on the subtle cue + control set dataset.
"""
import os
import gc
import time
import json
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import torch
import torchaudio
import pandas as pd
import numpy as np
from torch.utils.data import DataLoader, Dataset
from dataclasses import dataclass
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path_config, get_resource_limits, get_evaluation_config
from utils.logger import get_logger, LlmXiveError
from data.loader import load_class_config

# Configure logging
logger = get_logger("inference_runner")

@dataclass
class InferenceResult:
    """Container for a single inference result."""
    model_id: str
    sample_id: str
    logits: List[float]
    label: int
    latency_ms: float
    ram_gb: float

@dataclass
class InferenceRunSummary:
    """Container for a batch inference summary."""
    model_id: str
    total_samples: int
    successful_inferences: int
    failed_inferences: int
    avg_latency_ms: float
    peak_ram_gb: float

def get_model_paths(model_dir: Path) -> Dict[str, Path]:
    """
    Discover available model checkpoints in the given directory.
    
    Args:
        model_dir: Directory containing model checkpoints.
        
    Returns:
        Dictionary mapping model_id to checkpoint path.
    """
    if not model_dir.exists():
        raise LlmXiveError(f"Model directory does not exist: {model_dir}")
    
    models = {}
    for file in model_dir.glob("*.pt"):
        # Extract model_id from filename (e.g., "student_int8_pruned0.2.pt" -> "student_int8_pruned0.2")
        model_id = file.stem
        models[model_id] = file
    return models

def load_student_model(checkpoint_path: Path, device: str = "cpu") -> torch.nn.Module:
    """
    Load a student model from a checkpoint.
    
    Args:
        checkpoint_path: Path to the model checkpoint.
        device: Device to load the model on.
        
    Returns:
        Loaded model instance.
    """
    try:
        # Load the state dict
        state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
        
        # Determine model type from checkpoint metadata or filename
        # For now, we assume a standard wav2vec2-based student architecture
        # In a real scenario, this would be more sophisticated
        from transformers import Wav2Vec2Model, Wav2Vec2Config
        
        # Try to infer config from checkpoint keys or use default
        # This is a simplified approach - real implementation would need proper metadata
        config = Wav2Vec2Config.from_pretrained("facebook/wav2vec2-base-960h")
        model = Wav2Vec2Model(config)
        
        # Load state dict
        model.load_state_dict(state_dict, strict=False)
        model.to(device)
        model.eval()
        
        logger.info(f"Successfully loaded model from {checkpoint_path}")
        return model
        
    except Exception as e:
        logger.error(f"Failed to load model from {checkpoint_path}: {str(e)}")
        raise

def get_ram_usage_mb() -> float:
    """Get current RAM usage in MB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback if psutil is not available
        logger.warning("psutil not available, using placeholder RAM measurement")
        return 0.0

class AudioDataset(Dataset):
    """Dataset for loading audio samples from parquet file."""
    
    def __init__(self, parquet_path: Path, sample_rate: int = 16000):
        self.parquet_path = parquet_path
        self.sample_rate = sample_rate
        self.df = pd.read_parquet(parquet_path)
        self.base_path = parquet_path.parent.parent  # Go up to project root for relative paths
        
        if len(self.df) == 0:
            raise LlmXiveError(f"Dataset is empty: {parquet_path}")
        
        logger.info(f"Loaded {len(self.df)} samples from {parquet_path}")
    
    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        audio_path = row['audio_path']
        class_id = int(row['class_id'])
        label = int(row['label'])
        
        # Handle relative paths
        if not os.path.isabs(audio_path):
            # Try to construct full path
            full_path = self.base_path / audio_path
            if not full_path.exists():
                # Try direct path
                full_path = Path(audio_path)
        else:
            full_path = Path(audio_path)
        
        if not full_path.exists():
            logger.warning(f"Audio file not found: {full_path}, skipping")
            # Return dummy data
            waveform = torch.zeros(1, self.sample_rate)
            return {
                'waveform': waveform,
                'sample_rate': self.sample_rate,
                'sample_id': f"missing_{idx}",
                'class_id': class_id,
                'label': label
            }
        
        try:
            waveform, sr = torchaudio.load(full_path)
            if sr != self.sample_rate:
                waveform = torchaudio.functional.resample(waveform, sr, self.sample_rate)
            return {
                'waveform': waveform,
                'sample_rate': sr,
                'sample_id': f"sample_{idx}",
                'class_id': class_id,
                'label': label
            }
        except Exception as e:
            logger.warning(f"Failed to load audio {full_path}: {str(e)}")
            waveform = torch.zeros(1, self.sample_rate)
            return {
                'waveform': waveform,
                'sample_rate': self.sample_rate,
                'sample_id': f"error_{idx}",
                'class_id': class_id,
                'label': label
            }

def run_inference_batch(
    model: torch.nn.Module,
    batch: Dict[str, Any],
    device: str = "cpu"
) -> Tuple[List[InferenceResult], float]:
    """
    Run inference on a batch of audio samples.
    
    Args:
        model: The model to run inference with.
        batch: Dictionary containing batch data.
        device: Device to run inference on.
        
    Returns:
        Tuple of (list of results, latency in ms)
    """
    start_time = time.time()
    
    with torch.no_grad():
        waveforms = batch['waveform'].to(device)
        
        # Ensure proper shape for model input
        if waveforms.dim() == 3:
            # (batch, channels, time) -> (batch, time)
            waveforms = waveforms.squeeze(1)
        
        try:
            outputs = model(waveforms)
            # Extract logits - depends on model architecture
            if hasattr(outputs, 'last_hidden_state'):
                # wav2vec2 returns hidden states
                logits = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            else:
                logits = outputs.cpu().numpy()
            
            # Flatten if needed
            if logits.ndim > 2:
                logits = logits.reshape(logits.shape[0], -1)
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                logger.error("OOM detected during inference batch")
                gc.collect()
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                raise LlmXiveError("OOM during inference batch") from e
            raise
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        results = []
        batch_size = len(batch['sample_id'])
        
        for i in range(batch_size):
            result = InferenceResult(
                model_id="unknown",  # Will be set later
                sample_id=batch['sample_id'][i],
                logits=logits[i].tolist(),
                label=batch['label'][i],
                latency_ms=latency_ms / batch_size,
                ram_gb=get_ram_usage_mb() / 1024.0
            )
            results.append(result)
        
        return results, latency_ms

def run_inference_on_model(
    model_id: str,
    model_path: Path,
    data_path: Path,
    batch_size: int = 8,
    device: str = "cpu"
) -> InferenceRunSummary:
    """
    Run inference on a single model across the entire dataset.
    
    Args:
        model_id: Identifier for the model.
        model_path: Path to the model checkpoint.
        data_path: Path to the parquet dataset.
        batch_size: Batch size for inference.
        device: Device to run inference on.
        
    Returns:
        Summary of the inference run.
    """
    logger.info(f"Starting inference for model: {model_id}")
    
    # Load model
    model = load_student_model(model_path, device)
    model.to(device)
    
    # Load dataset
    try:
        dataset = AudioDataset(data_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        raise
    
    # Create DataLoader
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,  # CPU-only, avoid multiprocessing overhead
        collate_fn=lambda x: {
            'waveform': torch.stack([item['waveform'] for item in x]),
            'sample_rate': [item['sample_rate'] for item in x],
            'sample_id': [item['sample_id'] for item in x],
            'class_id': [item['class_id'] for item in x],
            'label': torch.tensor([item['label'] for item in x])
        }
    )
    
    all_results = []
    total_samples = 0
    successful = 0
    failed = 0
    total_latency = 0.0
    peak_ram = 0.0
    
    try:
        for batch_idx, batch in enumerate(dataloader):
            try:
                results, latency = run_inference_batch(model, batch, device)
                for r in results:
                    r.model_id = model_id
                all_results.extend(results)
                
                total_samples += len(batch['sample_id'])
                successful += len(results)
                total_latency += latency
                
                current_ram = get_ram_usage_mb() / 1024.0
                if current_ram > peak_ram:
                    peak_ram = current_ram
                    
                # Periodic cleanup
                if batch_idx % 10 == 0:
                    gc.collect()
                    
            except LlmXiveError as e:
                if "OOM" in str(e):
                    logger.error(f"OOM at batch {batch_idx}, skipping remaining")
                    break
                failed += len(batch['sample_id'])
            except Exception as e:
                logger.error(f"Error at batch {batch_idx}: {str(e)}")
                failed += len(batch['sample_id'])
                
    except Exception as e:
        logger.error(f"Unexpected error during inference: {str(e)}")
        traceback.print_exc()
    
    avg_latency = total_latency / max(successful, 1)
    
    summary = InferenceRunSummary(
        model_id=model_id,
        total_samples=total_samples,
        successful_inferences=successful,
        failed_inferences=failed,
        avg_latency_ms=avg_latency,
        peak_ram_gb=peak_ram
    )
    
    logger.info(f"Inference summary for {model_id}: {successful}/{total_samples} successful")
    
    return summary, all_results

def main():
    """Main entry point for the inference runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run inference on student models")
    parser.add_argument("--model-dir", type=str, required=True, help="Directory containing model checkpoints")
    parser.add_argument("--testbed", type=str, required=True, help="Path to parquet dataset")
    parser.add_argument("--thresholds", type=str, default="0.05,0.1", help="Comma-separated thresholds")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for inference")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run on")
    
    args = parser.parse_args()
    
    # Validate inputs
    model_dir = Path(args.model_dir)
    testbed_path = Path(args.testbed)
    
    if not model_dir.exists():
        raise LlmXiveError(f"Model directory not found: {model_dir}")
    if not testbed_path.exists():
        raise LlmXiveError(f"Testbed file not found: {testbed_path}")
    
    # Parse thresholds
    thresholds = [float(t) for t in args.thresholds.split(",")]
    
    logger.info(f"Starting inference run with {len(thresholds)} thresholds")
    
    # Get models
    models = get_model_paths(model_dir)
    if not models:
        raise LlmXiveError(f"No models found in {model_dir}")
    
    logger.info(f"Found {len(models)} models: {list(models.keys())}")
    
    # Run inference for each model
    all_summaries = []
    all_results = []
    
    for model_id, model_path in models.items():
        try:
            summary, results = run_inference_on_model(
                model_id=model_id,
                model_path=model_path,
                data_path=testbed_path,
                batch_size=args.batch_size,
                device=args.device
            )
            all_summaries.append(summary)
            all_results.extend(results)
            
            # Save results immediately to avoid memory buildup
            result_file = Path(f"data/processed/inference_results_{model_id}.json")
            result_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(result_file, 'w') as f:
                json.dump([
                    {
                        'model_id': r.model_id,
                        'sample_id': r.sample_id,
                        'logits': r.logits,
                        'label': r.label,
                        'latency_ms': r.latency_ms,
                        'ram_gb': r.ram_gb
                    }
                    for r in results
                ], f, indent=2)
                
            logger.info(f"Saved results for {model_id} to {result_file}")
            
        except Exception as e:
            logger.error(f"Failed to run inference for {model_id}: {str(e)}")
            traceback.print_exc()
            continue
    
    # Save summary
    summary_file = Path("data/processed/inference_summary.json")
    with open(summary_file, 'w') as f:
        json.dump([
            {
                'model_id': s.model_id,
                'total_samples': s.total_samples,
                'successful_inferences': s.successful_inferences,
                'failed_inferences': s.failed_inferences,
                'avg_latency_ms': s.avg_latency_ms,
                'peak_ram_gb': s.peak_ram_gb
            }
            for s in all_summaries
        ], f, indent=2)
    
    logger.info(f"Inference complete. Summary saved to {summary_file}")
    logger.info(f"Total models processed: {len(all_summaries)}")
    
    return all_summaries, all_results

if __name__ == "__main__":
    main()
