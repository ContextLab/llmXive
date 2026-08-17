"""
Parallel batch processing utilities for image generation.

This module implements parallel batch processing for image generation tasks
to optimize runtime performance. It uses multiprocessing to distribute
image generation work across CPU cores, ensuring the pipeline completes
within the 6-hour runtime constraint.
"""
import os
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
import torch
import numpy as np

from utils.config import get_config
from models.inference import generate_image_from_velocity, euler_integrate


@dataclass
class BatchResult:
    """Result container for a single batch processing unit."""
    sample_idx: int
    success: bool
    image_path: Optional[str]
    error: Optional[str] = None
    duration: float = 0.0


def _process_single_image(
    sample_idx: int,
    velocity_vector: np.ndarray,
    noise_level: float,
    expert_type: str,
    output_dir: str,
    step_size: float = 0.1,
    num_steps: int = 50
) -> BatchResult:
    """
    Process a single image generation task.

    This function is designed to be run in a separate process for parallel execution.
    It regenerates the velocity vector based on the expert type and integrates
    to produce the final image.

    Args:
        sample_idx: Unique identifier for the sample.
        velocity_vector: Initial velocity vector from the dataset.
        noise_level: Noise level parameter for the integrator.
        expert_type: Type of expert field to use (e.g., 'expert_text_to_image').
        output_dir: Directory to save the generated image.
        step_size: Step size for Euler integration.
        num_steps: Number of integration steps.

    Returns:
        BatchResult containing the outcome of the generation.
    """
    start_time = time.time()
    try:
        # Ensure we are on CPU for consistency
        device = torch.device('cpu')

        # Generate the image using the integrator
        # Note: This re-runs the expert field logic to get a fresh velocity vector
        # and then integrates to produce the image.
        image = generate_image_from_velocity(
            velocity_vector=velocity_vector,
            noise_level=noise_level,
            expert_type=expert_type,
            device=device,
            step_size=step_size,
            num_steps=num_steps
        )

        if image is None:
            return BatchResult(
                sample_idx=sample_idx,
                success=False,
                image_path=None,
                error="Image generation returned None"
            )

        # Save the image
        output_path = Path(output_dir) / f"sample_{sample_idx}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert tensor to image and save
        # Assuming image is a tensor of shape (3, H, W) or (H, W, 3)
        if isinstance(image, torch.Tensor):
            image = image.detach().cpu().numpy()

        # Normalize if needed (assuming values are in [-1, 1] or [0, 1])
        if image.max() <= 1.0 and image.min() >= -1.0:
            image = (image + 1.0) / 2.0  # Normalize to [0, 1]
        elif image.max() <= 1.0 and image.min() < 0:
            image = (image - image.min()) / (image.max() - image.min())

        # Clip to [0, 1] and convert to uint8
        image = np.clip(image, 0, 1)
        image = (image * 255).astype(np.uint8)

        # Ensure correct shape for PIL
        if image.shape[0] == 3:
            image = np.transpose(image, (1, 2, 0))

        # Save using PIL
        from PIL import Image
        pil_image = Image.fromarray(image)
        pil_image.save(str(output_path), format='PNG')

        duration = time.time() - start_time
        return BatchResult(
            sample_idx=sample_idx,
            success=True,
            image_path=str(output_path),
            duration=duration
        )

    except Exception as e:
        duration = time.time() - start_time
        return BatchResult(
            sample_idx=sample_idx,
            success=False,
            image_path=None,
            error=str(e),
            duration=duration
        )


def run_parallel_batch_processing(
    samples: List[Dict[str, Any]],
    output_dir: str,
    num_workers: Optional[int] = None,
    batch_size: int = 10,
    step_size: float = 0.1,
    num_steps: int = 50
) -> Dict[str, Any]:
    """
    Run parallel batch processing for image generation.

    This function distributes image generation tasks across multiple CPU processes
    to optimize runtime performance. It processes samples in batches and collects
    results.

    Args:
        samples: List of sample dictionaries containing velocity_vector, noise_level,
                expert_type, and sample_idx.
        output_dir: Directory to save generated images.
        num_workers: Number of worker processes. Defaults to CPU count.
        batch_size: Number of samples to process in each batch.
        step_size: Step size for Euler integration.
        num_steps: Number of integration steps.

    Returns:
        Dictionary containing processing statistics and results.
    """
    if num_workers is None:
        num_workers = max(1, os.cpu_count() - 1)

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    total_samples = len(samples)
    results = []
    successful = 0
    failed = 0
    total_duration = 0.0

    print(f"Starting parallel batch processing with {num_workers} workers...")
    print(f"Total samples: {total_samples}, Batch size: {batch_size}")

    # Process in batches using ProcessPoolExecutor
    # Note: We use a chunked approach to manage memory and ensure progress
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = []

        for sample in samples:
            future = executor.submit(
                _process_single_image,
                sample_idx=sample['sample_idx'],
                velocity_vector=sample['velocity_vector'],
                noise_level=sample['noise_level'],
                expert_type=sample['expert_type'],
                output_dir=output_dir,
                step_size=step_size,
                num_steps=num_steps
            )
            futures.append(future)

        # Collect results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                total_duration += result.duration

                if result.success:
                    successful += 1
                else:
                    failed += 1
                    print(f"Failed sample {result.sample_idx}: {result.error}")

            except Exception as e:
                failed += 1
                print(f"Exception in batch processing: {e}")

    # Sort results by sample index
    results.sort(key=lambda x: x.sample_idx)

    # Calculate statistics
    stats = {
        'total_samples': total_samples,
        'successful': successful,
        'failed': failed,
        'success_rate': successful / total_samples if total_samples > 0 else 0.0,
        'total_duration_seconds': total_duration,
        'average_duration_per_sample': total_duration / total_samples if total_samples > 0 else 0.0,
        'num_workers': num_workers,
        'batch_size': batch_size
    }

    # Save statistics
    stats_path = Path(output_dir) / "batch_processing_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

    print(f"Batch processing complete. Success rate: {stats['success_rate']:.2%}")
    print(f"Total time: {stats['total_duration_seconds']:.2f}s, "
          f"Avg per sample: {stats['average_duration_per_sample']:.2f}s")

    return {
        'stats': stats,
        'results': results,
        'output_dir': output_dir
    }


def estimate_runtime(
    num_samples: int,
    avg_time_per_sample: float,
    num_workers: int,
    target_max_hours: float = 6.0
) -> Dict[str, Any]:
    """
    Estimate runtime for batch processing.

    Args:
        num_samples: Number of samples to process.
        avg_time_per_sample: Average time per sample in seconds.
        num_workers: Number of parallel workers.
        target_max_hours: Target maximum runtime in hours.

    Returns:
        Dictionary with runtime estimates and recommendations.
    """
    # Parallel speedup is not perfectly linear due to overhead
    # Estimate with 80% efficiency factor
    estimated_efficiency = 0.8
    effective_workers = num_workers * estimated_efficiency

    total_time_seconds = (num_samples * avg_time_per_sample) / effective_workers
    total_time_hours = total_time_seconds / 3600

    within_budget = total_time_hours <= target_max_hours

    return {
        'estimated_total_hours': total_time_hours,
        'within_6h_budget': within_budget,
        'recommended_workers': num_workers if within_budget else min(num_workers, max(1, int(num_workers * (target_max_hours / total_time_hours)))),
        'samples_per_hour': num_samples / total_time_hours if total_time_hours > 0 else 0
    }
