"""
Memory integration module for feature extraction.

Integrates memory management (chunking, subsampling) into the extraction pipeline.
"""
import os
import json
import gc
import logging
from typing import List, Dict, Any, Optional, Tuple, Iterator
import numpy as np

from utils.memory_manager import get_processing_plan, generate_subsample_indices, generate_temporal_chunks
from utils.logging_config import get_logger

logger = get_logger(__name__)

class MemoryManagedExtractor:
    """
    Extractor that manages memory by applying subsampling and chunking strategies.
    """
    def __init__(self, max_ram_gb: float = 7.0):
        self.max_ram_gb = max_ram_gb
        self.stats = {
            "chunks_processed": 0,
            "frames_subsampled": 0,
            "temporal_chunks_created": 0,
            "peak_memory_mb": 0.0
        }

    def get_processing_plan(self, clip_id: str, clip_length: int) -> Dict[str, Any]:
        """
        Get a processing plan for a clip based on its length and memory constraints.
        
        Args:
            clip_id: The ID of the clip.
            clip_length: The number of frames in the clip.
        
        Returns:
            A dictionary containing the processing plan (frame indices, chunking strategy).
        """
        # Estimate memory per frame (placeholder)
        # In reality, this would depend on the video resolution and model input size
        estimated_frame_memory_mb = 0.1 # Placeholder
        
        # Calculate max frames allowed
        max_frames = int((self.max_ram_gb * 1024) / estimated_frame_memory_mb)
        
        if clip_length <= max_frames:
            # Clip is short enough, use subsampling if needed to reduce further
            # or process all frames
            plan = {
                "strategy": "subsample",
                "frame_indices": generate_subsample_indices(clip_length, max_frames)
            }
            self.stats["frames_subsampled"] += len(plan["frame_indices"])
        else:
            # Clip is too long, use temporal chunking
            plan = {
                "strategy": "chunk",
                "chunks": generate_temporal_chunks(clip_length, max_frames)
            }
            self.stats["temporal_chunks_created"] += len(plan["chunks"])
        
        return plan

    def process_clip(self, clip_id: str, clip_length: int) -> Iterator[np.ndarray]:
        """
        Process a clip with memory management.
        
        Yields:
            Processed frames or chunks of frames.
        """
        plan = self.get_processing_plan(clip_id, clip_length)
        
        if plan["strategy"] == "subsample":
            # Process subsampled frames
            for idx in plan["frame_indices"]:
                # Yield frame index for processing
                yield idx
                gc.collect()
        else:
            # Process temporal chunks
            for chunk_start, chunk_end in plan["chunks"]:
                # Yield chunk range for processing
                yield (chunk_start, chunk_end)
                gc.collect()

    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        return self.stats

def main():
    """Main entry point for memory integration testing."""
    extractor = MemoryManagedExtractor()
    
    # Test with a short clip
    plan_short = extractor.get_processing_plan("short_clip", 100)
    logger.info(f"Short clip plan: {plan_short}")
    
    # Test with a long clip
    plan_long = extractor.get_processing_plan("long_clip", 10000)
    logger.info(f"Long clip plan: {plan_long}")
    
    logger.info(f"Stats: {extractor.get_stats()}")

if __name__ == "__main__":
    main()