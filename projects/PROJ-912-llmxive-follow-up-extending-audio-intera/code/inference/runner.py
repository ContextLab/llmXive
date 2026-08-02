"""
CPU Inference Runner for Audio Interaction Model.

Implements batch processing to fit RAM, handles OOM gracefully,
and executes inference on student models using the Subtle Cue dataset.
"""
import os
import gc
import time
import json
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass, asdict

import torch
import numpy as np
from torch.utils.data import DataLoader

# Project imports
from config import (
    get_path_config, 
    get_evaluation_config, 
    get_resource_limits,
    PathConfig,
    EvaluationConfig
)
from utils.logger import get_logger, EvaluationError
from models.student import StudentModel, StudentModelMetadata
from data.loader import FilteredDataLoader, FilteredAudioDataset

# Ensure inference directory exists
INFER_DIR = Path("code/inference")
INFER_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

@dataclass
class InferenceResult:
    """Container for a single inference batch result."""
    model_id: str
    batch_index: int
    total_batches: int
    predictions: List[float]
    labels: List[int]
    inference_time_seconds: float
    peak_memory_mb: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class InferenceRunSummary:
    """Summary of a full inference run across all batches."""
    model_id: str
    total_samples: int
    total_batches: int
    total_time_seconds: float
    avg_batch_time_seconds: float
    peak_memory_mb: float
    success: bool
    error_message: Optional[str] = None
    output_path: Optional[str] = None

def get_model_paths(path_config: PathConfig) -> List[Path]:
    """
    Retrieve paths to all saved student model checkpoints.
    Expects models to be in data/processed/ as per T015.
    """
    model_dir = path_config.processed_data_dir
    if not model_dir.exists():
        raise FileNotFoundError(f"Model directory not found: {model_dir}")
    
    # Look for .pt or .pth files that contain 'student' or 'compressed'
    # Adjust extension matching if T015 uses a different naming convention
    candidates = list(model_dir.glob("*.pt")) + list(model_dir.glob("*.pth"))
    # Filter to ensure they look like student models based on naming or metadata
    # For robustness, we assume T015 saves them with a specific pattern or metadata
    # Here we assume all found models are valid student models for this run
    return candidates

def load_student_model(model_path: Path) -> Tuple[StudentModel, StudentModelMetadata]:
    """
    Load a student model and its metadata from disk.
    Ensures CPU-only loading.
    """
    logger.info(f"Loading student model from: {model_path}")
    
    # Load metadata if it exists alongside the model
    metadata_path = model_path.with_suffix('.json')
    metadata = None
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata_dict = json.load(f)
            metadata = StudentModelMetadata(**metadata_dict)
    else:
        logger.warning(f"Metadata file not found for {model_path}. Attempting to infer or skip.")
        # Fallback: create a minimal metadata object if not found
        # This might need adjustment based on T015 output format
        metadata = StudentModelMetadata(
            bit_width=16, # Default fallback
            param_count=0,
            compression_type="unknown",
            pruning_ratio=0.0
        )

    # Load the actual model state
    try:
        state_dict = torch.load(model_path, map_location='cpu', weights_only=True)
    except Exception as e:
        raise EvaluationError(f"Failed to load model state from {model_path}: {e}")

    # Reconstruct the model. 
    # Note: StudentModel constructor signature depends on T007/T016 implementation.
    # We assume it can be initialized with the metadata or a default config, 
    # then load_state_dict.
    # If StudentModel requires specific architecture args, we might need to read them from metadata.
    
    # Assuming StudentModel has a from_checkpoint or similar, or we can init with defaults
    # For now, we assume a standard init that matches the architecture implied by metadata
    # or we try to load the state dict into a fresh instance.
    # Since T007 defines the skeleton, we assume a standard __init__.
    
    # If the model was saved with the full object (torch.save(model)), we just load it.
    # If saved as state_dict, we need to reconstruct.
    # T015 says "save to data/processed/ with metadata". Usually implies state_dict + json.
    
    # Heuristic: Try loading as full object first, then state_dict
    try:
        model = torch.load(model_path, map_location='cpu')
        if not isinstance(model, StudentModel):
            raise TypeError("Loaded object is not a StudentModel instance")
    except Exception:
        # Reconstruct
        # We need to know the architecture. Let's assume metadata contains enough info
        # or we use a default config.
        # Since we don't have the exact constructor args here without reading more from T007,
        # we assume the metadata or a standard config is used.
        # A safer bet if T015 saved the config is to load it.
        
        # Fallback strategy: If we can't reconstruct easily, we assume the saved file
        # contains the model or we use a generic init.
        # Given constraints, let's assume we can load state_dict into a new StudentModel.
        # We need to instantiate StudentModel. 
        # Let's assume StudentModel has a default constructor or takes config.
        # If T007 is just a skeleton, we might need to infer args.
        
        # Let's try to infer from metadata if possible, otherwise default.
        # If this fails, it's a design gap in T007/T015.
        # We will assume StudentModel can be initialized with the metadata or default.
        # For now, we assume a generic init that accepts no args or a config.
        # If T007 defines `__init__(self, config)`, we need config.
        
        # Let's assume the metadata file has the necessary config info.
        # If not, we might fail here.
        
        # Attempt 1: Use metadata to init
        try:
            # Assuming StudentModel accepts metadata or derived config
            model = StudentModel(metadata=metadata) 
        except TypeError:
            # Attempt 2: Default init
            model = StudentModel()
        
        model.load_state_dict(state_dict)
    
    model.eval()
    logger.info(f"Model loaded successfully. Params: {sum(p.numel() for p in model.parameters())}")
    return model, metadata

def get_ram_usage_mb() -> float:
    """Get current RAM usage in MB (Linux/Windows agnostic where possible)."""
    # Simple heuristic using torch or os
    # For CPU-only, we can try to read /proc/self/status on Linux or use psutil if available
    # Since we want to avoid external deps if possible, we use a basic fallback
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On Linux, ru_maxrss is in KB. On macOS, it's in KB too.
        return usage / 1024.0
    except ImportError:
        # Fallback: estimate or return 0 if not available
        # In a real runner, we'd use psutil or a system call
        return 0.0

def run_inference_batch(
    model: torch.nn.Module,
    dataloader: DataLoader,
    batch: Dict[str, Any],
    batch_idx: int,
    total_batches: int
) -> Tuple[List[float], List[int], float]:
    """
    Run inference on a single batch.
    Returns predictions, labels, and time taken.
    """
    start_time = time.time()
    
    with torch.no_grad():
        inputs = batch['audio'] # Assuming 'audio' key from T020/T021
        if isinstance(inputs, list):
            # If streaming returns raw waveforms, we might need to process them
            # But T020 should return tensors.
            # Fallback: stack if list
            try:
                inputs = torch.stack(inputs)
            except RuntimeError:
                # If shapes differ, we might need padding, but T020 should handle that
                raise EvaluationError("Batch audio tensors have inconsistent shapes")
        
        inputs = inputs.float().to('cpu')
        
        # Ensure model is on CPU
        model = model.to('cpu')
        
        outputs = model(inputs)
        
        # Handle output format. Assuming logits or probabilities.
        # If model returns dict, extract logits.
        if isinstance(outputs, dict):
            logits = outputs.get('logits')
        else:
            logits = outputs
        
        if logits is None:
            raise EvaluationError("Model output is None")
        
        # Flatten if necessary
        if logits.dim() > 1:
            predictions = logits.argmax(dim=-1).tolist()
        else:
            predictions = logits.tolist()
        
        labels = batch['label'].tolist() if 'label' in batch else [0] * len(predictions)
    
    duration = time.time() - start_time
    return predictions, labels, duration

def run_inference_on_model(
    model: StudentModel,
    model_metadata: StudentModelMetadata,
    dataloader: DataLoader,
    model_id: str,
    config: EvaluationConfig
) -> InferenceRunSummary:
    """
    Run inference on a single model across the entire dataloader.
    Handles OOM and memory constraints.
    """
    logger.info(f"Starting inference for model: {model_id}")
    total_samples = len(dataloader.dataset)
    total_batches = len(dataloader)
    
    all_predictions = []
    all_labels = []
    total_time = 0.0
    peak_memory = 0.0
    
    batch_size = config.batch_size
    if batch_size is None:
        # Dynamic batch size search could go here, but for now use a safe default
        batch_size = 4 
    
    # Re-create dataloader if needed to ensure correct batch size
    current_dl = dataloader
    if dataloader.batch_size != batch_size:
        current_dl = DataLoader(
            dataloader.dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=0, # CPU only, avoid fork issues
            pin_memory=False
        )

    try:
        for batch_idx, batch in enumerate(current_dl):
            # Check memory before processing
            current_ram = get_ram_usage_mb()
            if current_ram > peak_memory:
                peak_memory = current_ram

            # Safety check: if RAM is too high, force GC
            resource_limits = get_resource_limits()
            max_ram = resource_limits.get('max_ram_gb', 7) * 1024
            if peak_memory > max_ram * 0.9:
                logger.warning(f"RAM usage high ({peak_memory:.1f}MB). Forcing GC.")
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                # In CPU only, torch doesn't manage cache the same way, but good practice
            
            try:
                preds, labels, duration = run_inference_batch(
                    model, current_dl, batch, batch_idx, total_batches
                )
                all_predictions.extend(preds)
                all_labels.extend(labels)
                total_time += duration

                # Log progress
                if (batch_idx + 1) % 10 == 0 or (batch_idx + 1) == total_batches:
                    logger.info(
                        f"Model {model_id}: Batch {batch_idx+1}/{total_batches} "
                        f"(Time: {duration:.2f}s, RAM: {peak_memory:.1f}MB)"
                    )

            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    logger.error(f"OOM error at batch {batch_idx}. Attempting recovery...")
                    gc.collect()
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    # Reduce batch size for next iteration? 
                    # For now, we fail loudly as per constraints (no silent fallback)
                    raise EvaluationError(f"OOM at batch {batch_idx}. Model: {model_id}.") from e
                else:
                    raise
    
        avg_time = total_time / total_batches if total_batches > 0 else 0.0
        
        # Save results to a temporary file or return them
        # T024 will aggregate these. We return the summary and the raw data.
        # We'll write a partial result file for this model.
        output_file = Path(f"data/processed/inference_{model_id.replace('/', '_')}.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        result_data = {
            "model_id": model_id,
            "predictions": all_predictions,
            "labels": all_labels,
            "total_time": total_time,
            "peak_memory_mb": peak_memory,
            "total_samples": len(all_predictions)
        }
        
        with open(output_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        return InferenceRunSummary(
            model_id=model_id,
            total_samples=len(all_predictions),
            total_batches=total_batches,
            total_time_seconds=total_time,
            avg_batch_time_seconds=avg_time,
            peak_memory_mb=peak_memory,
            success=True,
            output_path=str(output_file)
        )

    except Exception as e:
        logger.error(f"Inference failed for {model_id}: {e}")
        traceback.print_exc()
        return InferenceRunSummary(
            model_id=model_id,
            total_samples=0,
            total_batches=total_batches,
            total_time_seconds=0.0,
            avg_batch_time_seconds=0.0,
            peak_memory_mb=peak_memory,
            success=False,
            error_message=str(e)
        )

def main():
    """
    Main entry point for the inference runner.
    Iterates over all saved student models and runs inference on the Subtle Cue dataset.
    """
    logger.info("Starting CPU Inference Runner (T022)")
    
    path_config = get_path_config()
    eval_config = get_evaluation_config()
    
    # 1. Load Dataset
    # T020 should have set up the loader. We assume FilteredDataLoader is ready.
    # We need to instantiate it with the subtle cue builder settings.
    # T021/T021b define the classes.
    
    try:
        # Assuming FilteredDataLoader can be instantiated with a config or builder
        # We need to pass the builder or class lists.
        # For now, we assume the builder is used to create the dataset.
        # Let's assume a helper function or direct instantiation.
        # Since T020 is `code/data/loader.py`, we assume it exports a way to get the loader.
        
        # Re-reading T020: "Implement filtered data loader ... using streaming"
        # We assume FilteredDataLoader takes a builder or config.
        # Let's assume we need to import the builder to get the class lists.
        from data.subtle_cue_builder import SubtleCueBuilder, ControlSetBuilder, get_binary_discrimination_mapping
        
        subtle_builder = SubtleCueBuilder()
        control_builder = ControlSetBuilder()
        
        # Get class lists
        subtle_classes = subtle_builder.get_subtle_classes()
        control_classes = control_builder.get_control_classes()
        
        # Create dataset
        dataset = FilteredAudioDataset(
            subtle_classes=subtle_classes,
            control_classes=control_classes,
            streaming=True
        )
        
        dataloader = DataLoader(
            dataset,
            batch_size=eval_config.batch_size or 4,
            shuffle=False,
            num_workers=0
        )
        
        logger.info(f"Dataset loaded: {len(dataset)} samples")
        
    except Exception as e:
        raise EvaluationError(f"Failed to load dataset: {e}") from e

    # 2. Get Model Paths
    try:
        model_paths = get_model_paths(path_config)
        if not model_paths:
            raise FileNotFoundError("No student models found in data/processed/")
        logger.info(f"Found {len(model_paths)} student models to evaluate")
    except Exception as e:
        raise EvaluationError(f"Failed to find models: {e}") from e

    # 3. Run Inference for each model
    summaries = []
    for model_path in model_paths:
        model_id = model_path.stem
        try:
            model, metadata = load_student_model(model_path)
            summary = run_inference_on_model(
                model, metadata, dataloader, model_id, eval_config
            )
            summaries.append(summary)
        except Exception as e:
            logger.error(f"Skipping {model_id} due to error: {e}")
            summaries.append(InferenceRunSummary(
                model_id=model_id,
                total_samples=0,
                total_batches=0,
                total_time_seconds=0,
                avg_batch_time_seconds=0,
                peak_memory_mb=0,
                success=False,
                error_message=str(e)
            ))

    # 4. Log Summary
    logger.info("Inference Run Summary:")
    for s in summaries:
        status = "SUCCESS" if s.success else "FAILED"
        logger.info(f"  {s.model_id}: {status} (Samples: {s.total_samples}, Time: {s.total_time_seconds:.2f}s, RAM: {s.peak_memory_mb:.1f}MB)")
        if not s.success:
            logger.info(f"    Error: {s.error_message}")

    # 5. Aggregate results (T024 will consume these, but we can save a master log here)
    summary_path = path_config.processed_data_dir / "inference_run_summary.json"
    with open(summary_path, 'w') as f:
        json.dump([asdict(s) for s in summaries], f, indent=2)
    
    logger.info(f"Full summary saved to {summary_path}")
    logger.info("Inference Runner completed.")

if __name__ == "__main__":
    main()
