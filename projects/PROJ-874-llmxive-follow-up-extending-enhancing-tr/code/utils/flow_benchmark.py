"""
Benchmark script to verify RAFT-Small model feasibility on CPU.

This script tests if RAFT-Small can run in FP16 precision on CPU.
If FP16 fails (OOM), it reports fallback to FP32.
"""

import os
import sys
import time
import logging
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from raft_small import RAFTSmall  # Assuming RAFT implementation
    RAFT_AVAILABLE = True
except ImportError:
    RAFT_AVAILABLE = False
    logger.warning("RAFT-Small not available. Install with: pip install raft-s")


def create_test_frames(height: int = 480, width: int = 640) -> tuple:
    """Create two synthetic frames for testing."""
    # Frame 1: static image
    frame1 = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    
    # Frame 2: slightly shifted version
    frame2 = np.zeros_like(frame1)
    frame2[:, :-10] = frame1[:, 10:]  # Shift right by 10 pixels
    
    return frame1, frame2


def benchmark_raft_small(fp16: bool = True) -> dict:
    """
    Run RAFT-Small benchmark on CPU.
    
    Args:
        fp16: Whether to use FP16 precision
        
    Returns:
        Dictionary with benchmark results
    """
    result = {
        'fp16': fp16,
        'success': False,
        'error': None,
        'inference_time_ms': None,
        'peak_memory_mb': None
    }
    
    if not RAFT_AVAILABLE:
        result['error'] = "RAFT-Small not available"
        return result
    
    try:
        # Create test frames
        frame1, frame2 = create_test_frames()
        
        # Convert to tensors
        img1 = torch.from_numpy(frame1).permute(2, 0, 1).float().unsqueeze(0)
        img2 = torch.from_numpy(frame2).permute(2, 0, 1).float().unsqueeze(0)
        
        if fp16:
            img1 = img1.half()
            img2 = img2.half()
        
        # Initialize model
        model = RAFTSmall()
        model.eval()
        
        if fp16:
            model = model.half()
        
        # Move to CPU
        model = model.cpu()
        
        # Warmup
        with torch.no_grad():
            _ = model(img1, img2)
        
        # Benchmark
        start_time = time.time()
        with torch.no_grad():
            flow = model(img1, img2)
        end_time = time.time()
        
        result['success'] = True
        result['inference_time_ms'] = (end_time - start_time) * 1000
        result['peak_memory_mb'] = torch.cuda.max_memory_allocated() / 1024 / 1024 if torch.cuda.is_available() else 0
        
    except Exception as e:
        result['error'] = str(e)
        result['success'] = False
        
    return result


def main():
    """Main entry point for the benchmark."""
    parser = argparse.ArgumentParser(description="Benchmark RAFT-Small on CPU")
    parser.add_argument("--fp16", action="store_true", help="Use FP16 precision")
    parser.add_argument("--fp32", action="store_true", help="Use FP32 precision")
    args = parser.parse_args()
    
    # Default to FP16 if neither specified
    use_fp16 = args.fp16 or (not args.fp16 and not args.fp32)
    
    logger.info(f"Running RAFT-Small benchmark with {'FP16' if use_fp16 else 'FP32'} precision...")
    
    result = benchmark_raft_small(fp16=use_fp16)
    
    if result['success']:
        logger.info(f"✓ SUCCESS: Inference time: {result['inference_time_ms']:.2f} ms")
        if result['peak_memory_mb']:
            logger.info(f"  Peak memory: {result['peak_memory_mb']:.2f} MB")
    else:
        logger.error(f"✗ FAILED: {result['error']}")
        
        if use_fp16:
            logger.warning("Attempting fallback to FP32...")
            fp32_result = benchmark_raft_small(fp16=False)
            if fp32_result['success']:
                logger.info(f"✓ FP32 fallback SUCCESS: Inference time: {fp32_result['inference_time_ms']:.2f} ms")
            else:
                logger.error(f"✗ FP32 also failed: {fp32_result['error']}")
    
    return 0 if result['success'] else 1


if __name__ == "__main__":
    sys.exit(main())
