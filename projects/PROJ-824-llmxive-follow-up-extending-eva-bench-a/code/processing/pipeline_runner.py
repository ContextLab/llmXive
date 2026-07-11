"""
Pipeline Runner Module for EVA-Bench Extension.

Executes the EVA-Bench scoring pipeline on modified audio files.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Mock the actual EVA-Bench scoring function since the real model weights/API
# are not part of this repository. In a real deployment, this would import
# the actual scoring logic from the EVA-Bench library.
def score_scenario(audio_path: str, scenario_id: str) -> Dict[str, Any]:
    """
    Simulates scoring a scenario.
    
    In a real implementation, this would:
    1. Load the audio
    2. Run it through the EVA-Bench evaluation model
    3. Return metrics like 'conversation_progression', 'turn_taking', etc.
    
    For this task, we return deterministic mock data based on the file path
    to ensure the pipeline runs end-to-end.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    # Simulate a score that degrades slightly with longer delays (if we had the delay info)
    # Here we just return a fixed structure for the integration test
    return {
        "scenario_id": scenario_id,
        "conversation_progression": 0.85,
        "turn_taking": 0.90,
        "inter_turn_gap_ms": 500, # Mocked value, updated by caller if needed
        "latency_condition": 0,
        "timestamp": datetime.now().isoformat()
    }

def run_pipeline_evaluation(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the evaluation pipeline on a single scenario.
    
    Args:
        config: Dictionary containing:
            - scenario_id: Unique identifier for the scenario
            - input_audio: Path to the audio file
            - output_dir: Directory to save results
            - latency_injected_ms: The delay applied (for logging/metrics)
    
    Returns:
        Dictionary containing the evaluation results.
    """
    scenario_id = config.get("scenario_id", "unknown")
    input_audio = config.get("input_audio")
    output_dir = config.get("output_dir", ".")
    latency_ms = config.get("latency_injected_ms", 0)

    if not input_audio:
        raise ValueError("Input audio path is required in config")

    logger.info(f"Running pipeline for {scenario_id} with latency {latency_ms}ms")

    try:
        # Execute scoring
        results = score_scenario(input_audio, scenario_id)
        
        # Update results with known latency condition
        results["latency_condition"] = latency_ms
        
        # Adjust inter_turn_gap to reflect injected latency for the test
        # (In a real system, the model would measure this, but we simulate it here)
        # We assume a baseline gap of 200ms
        baseline_gap = 200
        results["inter_turn_gap_ms"] = baseline_gap + latency_ms

        # Save results to output directory
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        result_file = output_dir_path / f"{scenario_id}_results.json"
        with open(result_file, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to {result_file}")
        return results

    except Exception as e:
        logger.error(f"Pipeline execution failed for {scenario_id}: {e}")
        raise
