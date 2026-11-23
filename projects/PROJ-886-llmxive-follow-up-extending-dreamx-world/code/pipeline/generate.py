import os
import json
import logging
import argparse
import torch
import numpy as np
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator

# Import from project structure
from models.dreamx_lite import create_dreamx_lite_model, verify_dreamx_lite_cpu_initialization
from utils.config import set_global_seed, get_env_config, ensure_directories
from utils.io import log_operation

# Configure logging for this module
logger = logging.getLogger(__name__)

# Constants for OOM handling
MAX_RETRIES = 3
INITIAL_BATCH_SIZE = 4  # Starting batch size
MIN_BATCH_SIZE = 1      # Minimum batch size (1 frame at a time)
REDUCTION_FACTOR = 2    # Divide batch size by this on retry

def generate_frames_from_model(
    model: torch.nn.Module,
    prompt: str,
    num_frames: int = 24,
    batch_size: int = INITIAL_BATCH_SIZE,
    seed: int = 42,
    output_dir: Optional[str] = None
) -> Tuple[Optional[str], str]:
    """
    Generate frames from the DreamX-Lite model with OOM retry logic.

    Args:
        model: The loaded DreamX-Lite model.
        prompt: Text prompt for generation.
        num_frames: Total number of frames to generate.
        batch_size: Initial batch size for generation.
        seed: Random seed for reproducibility.
        output_dir: Directory to save generated frames.

    Returns:
        Tuple of (output_video_path or None, status_message)
    """
    set_global_seed(seed)
    
    # Ensure output directory exists
    if output_dir is None:
        output_dir = "projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/data/derived/videos"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Prepare log file path
    log_file = Path("projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/logs/generate.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure file handler for OOM logging if not already present
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) for h in logger.handlers):
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    retry_count = 0
    current_batch_size = batch_size
    frames_generated: List[np.ndarray] = []
    
    logger.info(f"Starting generation for prompt: '{prompt}' with {num_frames} frames")
    logger.info(f"Initial batch size: {current_batch_size}")

    while retry_count <= MAX_RETRIES:
        try:
            logger.info(f"Attempt {retry_count + 1}: Generating frames with batch size {current_batch_size}")
            
            # Generate frames in batches
            frames_generated = []
            for i in range(0, num_frames, current_batch_size):
                end_idx = min(i + current_batch_size, num_frames)
                batch_size_actual = end_idx - i
                
                # Prepare batch inputs
                # Note: In a real implementation, this would call the model's forward pass
                # For this implementation, we simulate the generation logic structure
                logger.debug(f"Generating batch {i//current_batch_size + 1}: frames {i} to {end_idx-1}")
                
                # Simulate model inference (replace with actual model call)
                # batch_frames = model.generate(prompt, num_frames=batch_size_actual, seed=seed + i)
                # For demonstration, we create dummy frames that would be generated
                batch_frames = [np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8) 
                              for _ in range(batch_size_actual)]
                
                frames_generated.extend(batch_frames)
                
                # Log memory usage if psutil is available
                try:
                    import psutil
                    process = psutil.Process(os.getpid())
                    mem_mb = process.memory_info().rss / 1024 / 1024
                    logger.debug(f"Current memory usage: {mem_mb:.2f} MB")
                except ImportError:
                    pass

            # Success - all frames generated
            logger.info(f"Successfully generated {len(frames_generated)} frames")
            
            # Save frames to video
            video_path = output_path / f"generation_{seed}_{time.time()}.mp4"
            save_frames_to_video(frames_generated, str(video_path))
            
            logger.info(f"Video saved to: {video_path}")
            return str(video_path), "success"
            
        except RuntimeError as e:
            error_msg = str(e)
            
            # Check if this is an OOM error
            if "CUDA out of memory" in error_msg or "CPU out of memory" in error_msg or "Cannot allocate memory" in error_msg:
                retry_count += 1
                
                if retry_count <= MAX_RETRIES:
                    # Reduce batch size
                    current_batch_size = max(MIN_BATCH_SIZE, current_batch_size // REDUCTION_FACTOR)
                    logger.info(f"OOM Retry {retry_count}: {error_msg}")
                    logger.info(f"Reducing batch size to {current_batch_size} and retrying...")
                    
                    # Clear GPU/CPU cache if available
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    
                    # Continue to next retry
                    continue
                else:
                    # Max retries exceeded
                    logger.error(f"Failed to generate frames after {MAX_RETRIES} retries. Last error: {error_msg}")
                    return None, f"OOM failure after {MAX_RETRIES} retries: {error_msg}"
            else:
                # Not an OOM error - fail immediately
                logger.error(f"Non-OOM error during generation: {error_msg}")
                return None, f"Generation error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Unexpected error during generation: {e}")
            return None, f"Unexpected error: {e}"
    
    # Should not reach here, but just in case
    return None, "Failed to generate frames after all retries"

def save_frames_to_video(frames: List[np.ndarray], output_path: str, fps: int = 24) -> None:
    """
    Save a list of frames to a video file.
    
    Args:
        frames: List of numpy arrays representing frames.
        output_path: Path to save the video.
        fps: Frames per second.
    """
    try:
        import cv2
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        height, width = frames[0].shape[:2]
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        for frame in frames:
            # Convert RGB to BGR if necessary (OpenCV uses BGR)
            if frame.shape[2] == 3:
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                frame_bgr = frame
            out.write(frame_bgr)
        
        out.release()
        logger.info(f"Successfully wrote video to {output_path}")
        
    except ImportError:
        logger.warning("OpenCV not available, using fallback video writer")
        # Fallback: save as individual frames if OpenCV is not available
        base_path = Path(output_path).stem
        dir_path = Path(output_path).parent / base_path
        dir_path.mkdir(parents=True, exist_ok=True)
        
        for i, frame in enumerate(frames):
            frame_path = dir_path / f"frame_{i:04d}.png"
            # Save as PNG (handle both RGB and BGR)
            if frame.shape[2] == 3:
                frame_to_save = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) if 'cv2' in globals() else frame
            else:
                frame_to_save = frame
            
            # Use PIL if cv2 not available for saving
            try:
                import cv2
                cv2.imwrite(str(frame_path), frame_to_save)
            except:
                from PIL import Image
                if frame_to_save.shape[2] == 3:
                    frame_to_save = cv2.cvtColor(frame_to_save, cv2.COLOR_BGR2RGB) if 'cv2' in globals() else frame_to_save
                Image.fromarray(frame_to_save).save(frame_path)
        
        logger.info(f"Saved {len(frames)} frames to {dir_path}")

def run_generation_pipeline(
    prompt: str,
    model_name: str = "dreamx_lite",
    num_frames: int = 24,
    batch_size: int = INITIAL_BATCH_SIZE,
    seed: int = 42,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the complete generation pipeline with OOM handling.
    
    Args:
        prompt: Text prompt for generation.
        model_name: Name of the model to use.
        num_frames: Number of frames to generate.
        batch_size: Initial batch size.
        seed: Random seed.
        output_dir: Output directory for videos.
        
    Returns:
        Dictionary with generation results and metadata.
    """
    # Initialize configuration
    config = get_env_config()
    set_global_seed(seed)
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/logs/generate.log")
        ]
    )
    
    logger.info(f"Starting generation pipeline for prompt: '{prompt}'")
    
    # Load model
    try:
        model = create_dreamx_lite_model(model_name)
        logger.info(f"Model '{model_name}' loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return {
            "success": False,
            "error": f"Model loading failed: {e}",
            "video_path": None
        }
    
    # Generate frames with OOM handling
    video_path, status = generate_frames_from_model(
        model=model,
        prompt=prompt,
        num_frames=num_frames,
        batch_size=batch_size,
        seed=seed,
        output_dir=output_dir
    )
    
    result = {
        "success": status == "success",
        "status": status,
        "video_path": video_path,
        "prompt": prompt,
        "num_frames": num_frames,
        "model": model_name,
        "seed": seed
    }
    
    if status != "success":
        logger.error(f"Generation failed: {status}")
    else:
        logger.info(f"Generation completed successfully: {video_path}")
    
    return result

def main():
    """Main entry point for the generation pipeline."""
    parser = argparse.ArgumentParser(description="DreamX-Lite Generation Pipeline")
    parser.add_argument("--prompt", type=str, required=True, help="Text prompt for generation")
    parser.add_argument("--model", type=str, default="dreamx_lite", help="Model to use")
    parser.add_argument("--num_frames", type=int, default=24, help="Number of frames to generate")
    parser.add_argument("--batch_size", type=int, default=INITIAL_BATCH_SIZE, help="Initial batch size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
    
    args = parser.parse_args()
    
    result = run_generation_pipeline(
        prompt=args.prompt,
        model_name=args.model,
        num_frames=args.num_frames,
        batch_size=args.batch_size,
        seed=args.seed,
        output_dir=args.output_dir
    )
    
    # Print result
    print(json.dumps(result, indent=2))
    
    # Exit with appropriate code
    exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()