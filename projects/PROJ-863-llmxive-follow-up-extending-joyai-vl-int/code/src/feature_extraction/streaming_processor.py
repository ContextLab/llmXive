"""
Streaming Processor for Feature Extraction (Task T022).

Integrates the streaming utilities from T008 to process video data
in fixed-size chunks, ensuring RAM usage remains under 6GB.
"""
import json
import gc
import os
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional, Generator
from dataclasses import asdict

import numpy as np

from src.feature_extraction.streaming import StreamingBuffer, StreamingConfig
from src.feature_extraction.extractor import JoyAIFeatureExtractor
from src.data_synthesis.models import SyntheticVideoFrame, InternalStateVector
from src.utils.logging import get_logger
from src.utils.validation import validate_dimension_match

logger = get_logger(__name__)

# Default chunk size to ensure < 6GB RAM usage.
# Assuming ~100MB per 1000 frames of raw video + features in memory.
# 6000 frames is a safe upper bound for < 1GB usage, leaving room for model weights.
DEFAULT_CHUNK_SIZE = 2000

class StreamingFeatureProcessor:
    """
    Processes video frames in chunks to extract features while managing memory.
    """

    def __init__(
        self,
        model_path: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        output_dir: str = "data/features",
        streaming_config: Optional[StreamingConfig] = None,
    ):
        self.model_path = model_path
        self.chunk_size = chunk_size
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = streaming_config or StreamingConfig()
        self.extractor = JoyAIFeatureExtractor(model_path=model_path)
        self.logger = get_logger(__name__)

    def _process_chunk(
        self, 
        chunk_frames: List[SyntheticVideoFrame], 
        chunk_id: int
    ) -> List[Dict[str, Any]]:
        """
        Process a single chunk of frames.
        
        Args:
            chunk_frames: List of SyntheticVideoFrame objects.
            chunk_id: Identifier for the chunk.
            
        Returns:
            List of extracted feature dictionaries.
        """
        if not chunk_frames:
            return []

        self.logger.info(f"Processing chunk {chunk_id} with {len(chunk_frames)} frames.")
        
        extracted_features = []
        
        try:
            # Extract features for the entire chunk
            # The extractor handles internal batching if needed, but we pass the list
            # to ensure we don't load the whole dataset at once.
            features = self.extractor.extract_batch(chunk_frames)
            
            for frame, feat_vec in zip(chunk_frames, features):
                feat_dict = {
                    "frame_id": frame.frame_id,
                    "timestamp": frame.timestamp,
                    "video_chunk_id": chunk_id,
                    "features": feat_vec.tolist() if isinstance(feat_vec, np.ndarray) else feat_vec,
                    "feature_shape": list(feat_vec.shape) if isinstance(feat_vec, np.ndarray) else [len(feat_vec)],
                }
                extracted_features.append(feat_dict)
                
        except Exception as e:
            self.logger.error(f"Error processing chunk {chunk_id}: {e}")
            raise

        return extracted_features

    def _write_chunk_to_disk(
        self, 
        features: List[Dict[str, Any]], 
        chunk_id: int
    ) -> Path:
        """
        Write a chunk of features to a JSONL file.
        """
        output_path = self.output_dir / f"features_chunk_{chunk_id:05d}.jsonl"
        
        with open(output_path, "w", encoding="utf-8") as f:
            for feat in features:
                f.write(json.dumps(feat) + "\n")
                
        self.logger.info(f"Wrote {len(features)} features to {output_path}")
        return output_path

    def process_stream(
        self, 
        input_manifest_path: str
    ) -> Generator[Path, None, None]:
        """
        Main entry point to process the video stream from a manifest.
        Reads frames in chunks, extracts features, and writes to disk.
        
        Args:
            input_manifest_path: Path to the manifest.jsonl file from US1.
            
        Yields:
            Path to each written feature chunk file.
        """
        if not os.path.exists(input_manifest_path):
            raise FileNotFoundError(f"Manifest not found: {input_manifest_path}")

        self.logger.info(f"Starting streaming processing from {input_manifest_path}")
        
        chunk_frames: List[SyntheticVideoFrame] = []
        chunk_id = 0
        
        with open(input_manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                
                data = json.loads(line)
                frame = SyntheticVideoFrame(**data)
                chunk_frames.append(frame)
                
                # Check if chunk is full
                if len(chunk_frames) >= self.chunk_size:
                    chunk_id += 1
                    processed_features = self._process_chunk(chunk_frames, chunk_id)
                    output_path = self._write_chunk_to_disk(processed_features, chunk_id)
                    yield output_path
                    
                    # Clear memory
                    chunk_frames = []
                    gc.collect()
            
            # Process remaining frames
            if chunk_frames:
                chunk_id += 1
                processed_features = self._process_chunk(chunk_frames, chunk_id)
                output_path = self._write_chunk_to_disk(processed_features, chunk_id)
                yield output_path
                
        self.logger.info(f"Completed processing. Total chunks: {chunk_id}")

def main():
    """
    CLI entry point for the streaming processor.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Process video features in streaming chunks.")
    parser.add_argument(
        "--manifest", 
        type=str, 
        required=True, 
        help="Path to the input manifest.jsonl"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        required=True, 
        help="Path to the JoyAI-VL-Interaction model"
    )
    parser.add_argument(
        "--chunk-size", 
        type=int, 
        default=DEFAULT_CHUNK_SIZE, 
        help="Number of frames per chunk"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/features",
        help="Output directory for feature chunks"
    )
    
    args = parser.parse_args()
    
    processor = StreamingFeatureProcessor(
        model_path=args.model,
        chunk_size=args.chunk_size,
        output_dir=args.output
    )
    
    try:
        for path in processor.process_stream(args.manifest):
            logger.info(f"Produced: {path}")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

if __name__ == "__main__":
    main()
