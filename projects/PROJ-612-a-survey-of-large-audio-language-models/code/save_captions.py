"""
T015b: Implement caption storage.
Writes all generated captions to results/captions.json (JSONL format).
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import existing infrastructure
from config import load_config
from setup_logging import get_logger, init_logging
from run_inference import GenerationResult, run_inference_pipeline

def load_captions_from_inference(
    model_list_path: str,
    dataset_paths: Dict[str, Any],
    sample_limits: Dict[str, int],
    audio_config: Dict[str, Any],
    logger: logging.Logger
) -> List[GenerationResult]:
    """
    Runs the inference pipeline to generate captions for the configured datasets.
    Returns a list of GenerationResult objects.
    """
    # Delegate to the existing inference pipeline implementation
    results = run_inference_pipeline(
        model_list_path=model_list_path,
        dataset_paths=dataset_paths,
        sample_limits=sample_limits,
        audio_config=audio_config,
        logger=logger
    )
    return results

def save_captions_to_jsonl(
    results: List[GenerationResult],
    output_path: Path,
    logger: logging.Logger
) -> None:
    """
    Writes the list of GenerationResult objects to a JSONL file.
    Each line is a JSON object representing one caption generation.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for result in results:
            # Convert dataclass to dict
            record = {
                "model_name": result.model_name,
                "domain": result.domain,
                "audio_id": result.audio_id,
                "caption": result.caption,
                "timestamp": result.timestamp.isoformat() if result.timestamp else None
            }
            f.write(json.dumps(record) + '\n')
    
    logger.info(f"Saved {len(results)} captions to {output_path}")

def main():
    """Main entry point for T015b."""
    init_logging()
    logger = get_logger("save_captions")
    
    try:
        config = load_config()
        
        model_list_path = config.get("model_list_path", "data/model_list.yaml")
        dataset_paths = config.get("dataset_paths", {})
        sample_limits = config.get("sample_limits", {})
        audio_config = config.get("audio_config", {})
        
        # Define output path based on project structure
        output_path = Path("results/captions.json")
        
        logger.info(f"Starting caption generation for {len(dataset_paths)} datasets...")
        
        # Run inference to get captions
        results = load_captions_from_inference(
            model_list_path=model_list_path,
            dataset_paths=dataset_paths,
            sample_limits=sample_limits,
            audio_config=audio_config,
            logger=logger
        )
        
        if not results:
            logger.warning("No captions were generated.")
            return 1
        
        # Save to JSONL
        save_captions_to_jsonl(results, output_path, logger)
        
        logger.info("T015b completed successfully.")
        return 0
        
    except Exception as e:
        logger.exception(f"Error during caption storage: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())