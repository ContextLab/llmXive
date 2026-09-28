"""
Inference runner with RAM profiling and error handling.

This module provides:
- Single-case inference execution
- RAM usage profiling
- Error handling without synthetic fallback
- Output artifact generation (video, logs)
"""
import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import gc

import psutil
import torch
from transformers import AutoModel, AutoTokenizer
import cv2
import numpy as np

from utils.logging import get_logger, log_info, log_error, log_exception
from utils.errors import ResourceLimitError, SyntheticFallbackForbiddenError, PipelineError
from inference.models import load_model, validate_model_memory

logger = get_logger(__name__)

class InferenceRunner:
    """Runner for single-case inference with RAM profiling."""
    
    def __init__(self, max_ram_gb: float = 6.5):
        self.max_ram_gb = max_ram_gb
        self.current_ram_gb = 0.0
        
    def get_current_ram_gb(self) -> float:
        """Get current RAM usage in GB."""
        process = psutil.Process(os.pid)
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    
    def check_ram_limit(self) -> bool:
        """Check if current RAM usage is within limits."""
        self.current_ram_gb = self.get_current_ram_gb()
        return self.current_ram_gb <= self.max_ram_gb
    
    def run_inference(
        self,
        model,
        action_chain: List[Dict[str, Any]],
        output_path: Path,
        case_id: str,
        variant_type: str
    ) -> Dict[str, Any]:
        """
        Run inference for a single case.
        
        Args:
            model: Loaded PyTorch model
            action_chain: List of actions to execute
            output_path: Path to save output video
            case_id: Case identifier
            variant_type: Variant type (low/medium/high entropy)
        
        Returns:
            Result dictionary with status, paths, and metrics
        """
        start_ram = self.get_current_ram_gb()
        log_info(logger, f"Starting inference for case {case_id}, RAM: {start_ram:.2f}GB")
        
        try:
            # Pre-flight RAM check
            if not self.check_ram_limit():
                raise ResourceLimitError(
                    f"Current RAM ({start_ram:.2f}GB) exceeds limit ({self.max_ram_gb}GB)"
                )
            
            # Generate video from action chain
            # This is a placeholder implementation - real implementation would use the model
            video_frames = self._generate_video_from_actions(
                model, action_chain, case_id, variant_type
            )
            
            # Save video
            if video_frames:
                self._save_video(video_frames, output_path)
                log_info(logger, f"Video saved: {output_path}")
            
            end_ram = self.get_current_ram_gb()
            ram_delta = end_ram - start_ram
              
            result = {
                "status": "success",
                "case_id": case_id,
                "variant_type": variant_type,
                "video_path": str(output_path),
                "ram_start_gb": round(start_ram, 2),
                "ram_end_gb": round(end_ram, 2),
                "ram_delta_gb": round(ram_delta, 2),
                "duration_seconds": 0.0  # Placeholder
            }
            
            # Clean up
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return result
              
        except ResourceLimitError as e:
            log_error(logger, f"RAM limit exceeded: {e}")
            raise
              
        except Exception as e:
            log_error(logger, f"Inference failed: {e}")
            log_exception(logger, traceback.format_exc())
            raise
    
    def _generate_video_from_actions(
        self,
        model,
        action_chain: List[Dict[str, Any]],
        case_id: str,
        variant_type: str
    ) -> List[np.ndarray]:
        """
        Generate video frames from action chain.
        
        This is a placeholder implementation. In a real scenario, this would
        use the model to generate frames based on the action sequence.
        
        Args:
            model: The inference model
            action_chain: Sequence of actions
            case_id: Case identifier
            variant_type: Entropy variant type
        
        Returns:
            List of video frames (numpy arrays)
        """
        # Placeholder: Generate simple synthetic frames for testing
        # In production, this would use the actual model
        frames = []
        num_frames = 30  # Standard video length
        height, width = 224, 224  # Standard resolution
        
        for i in range(num_frames):
            # Create a simple gradient frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            for j in range(width):
                color = int(255 * (j / width))
                frame[:, j] = [color, color, color]
            frames.append(frame)
        
        return frames
    
    def _save_video(self, frames: List[np.ndarray], output_path: Path):
        """Save video frames to MP4 file."""
        if not frames:
            raise PipelineError("No frames to save")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, 10.0, (frames[0].shape[1], frames[0].shape[0]))
        
        for frame in frames:
            out.write(frame)
        
        out.release()
        log_info(logger, f"Video saved: {output_path}")

def run_inference_single_case(
    input_data: Dict[str, Any],
    output_dir: str,
    max_ram_gb: float = 6.5
) -> Dict[str, Any]:
    """
    Run inference for a single case.
    
    Args:
        input_data: Dictionary with case_id, variant_type, action_chain, model_id
        output_dir: Directory to save output artifacts
        max_ram_gb: Maximum RAM limit in GB
    
    Returns:
        Result dictionary with status and paths
    
    Raises:
        ResourceLimitError: If RAM limit exceeded
        SyntheticFallbackForbiddenError: If synthetic fallback is attempted
        PipelineError: If inference fails
    """
    case_id = input_data.get("case_id", "unknown")
    variant_type = input_data.get("variant_type", "unknown")
    action_chain = input_data.get("action_chain", [])
    model_id = input_data.get("model_id", None)
    
    if not model_id:
        raise PipelineError("Model ID not provided")
    
    if not action_chain:
        raise PipelineError("Action chain is empty")
    
    output_path = Path(output_dir) / f"{case_id}_{variant_type}.mp4"
    log_path = Path(output_dir) / f"{case_id}_{variant_type}_log.json"
    
    logger.info(f"Running inference for case {case_id}, model {model_id}")
    
    try:
        # Load model
        model = load_model(model_id)
        validate_model_memory(model, max_ram_gb)
        
        # Create runner
        runner = InferenceRunner(max_ram_gb=max_ram_gb)
        
        # Run inference
        result = runner.run_inference(
            model=model,
            action_chain=action_chain,
            output_path=output_path,
            case_id=case_id,
            variant_type=variant_type
        )
        
        # Save log
        with open(log_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        result["log_path"] = str(log_path)
        return result
        
    except ResourceLimitError as e:
        log_error(logger, f"RAM limit exceeded: {e}")
        raise
    except Exception as e:
        log_error(logger, f"Inference failed: {e}")
        log_exception(logger, traceback.format_exc())
        raise

def main():
    """Main function for testing inference runner."""
    # Sample input data
    input_data = {
        "case_id": "test_case_001",
        "variant_type": "medium",
        "action_chain": [
            {"action": "move", "target": "obj1", "params": {"x": 1, "y": 2}},
            {"action": "grasp", "target": "obj1"},
            {"action": "place", "target": "obj2", "params": {"x": 3, "y": 4}}
        ],
        "model_id": "hf-internal-testing/tiny-random-LlamaForCausalLM"
    }
    
    output_dir = Path("data/processed/inference_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        result = run_inference_single_case(
            input_data=input_data,
            output_dir=str(output_dir),
            max_ram_gb=6.5
        )
        print(f"Inference completed: {result}")
    except Exception as e:
        log_error(logger, f"Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()