import os
import sys
import time
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import project utilities and models
from config import get_annotated_data_path, get_processed_data_path, ensure_dirs
from utils.logging import get_experiment_logger, log_metric, log_error, log_info
from data.models import InteractionTurn, RoutingDecision, SimulationRun
from models.router import predict_intent, load_quantized_model
from models.fallback import match_intent, generate_fallback
from simulation.patience import sample_patience
from simulation.rubric import calculate_alignment_score

logger = get_experiment_logger("simulation_runner")

# Constants for density levels (FR-004)
DENSITY_LEVELS = [1, 3, 5, 10]

def load_annotated_data() -> pd.DataFrame:
    """Load the labeled dataset from T013/T012b."""
    path = get_annotated_data_path()
    if not os.path.exists(path):
        raise FileNotFoundError(f"Annotated data not found at {path}. Run T012b first.")
    df = pd.read_csv(path)
    # Ensure required columns exist
    required_cols = ['query', 'ground_truth_intent']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in {path}")
    return df

def simulate_interaction(
    row: Dict[str, Any],
    router_model,
    density: int,
    rng: np.random.Generator
) -> Dict[str, Any]:
    """
    Simulate a single interaction turn based on the task requirements.
    
    Handles:
    1. Routing (High-Confidence vs Ambiguous)
    2. Ambiguous handling: invoke fallback, log "no-match" if no ontology entry, return minimal UI.
    3. Latency injection and patience modeling.
    4. Alignment scoring.
    """
    query = row['query']
    ground_truth = row.get('ground_truth_intent', 'unknown')
    
    interaction_start = time.time()
    
    # 1. Routing Decision
    # Predict intent using the trained router
    try:
        intent, confidence = predict_intent(router_model, query)
    except Exception as e:
        log_error(f"Router prediction failed for query: {query[:50]}... Error: {e}")
        intent = "Ambiguous"
        confidence = 0.0
    
    routing_decision = RoutingDecision(
        intent=intent,
        confidence=confidence,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    # 2. Determine Path
    is_ambiguous = (intent == "Ambiguous") or (confidence < 0.6) # Threshold example
    
    latency_injected = 0.0
    user_patience = sample_patience() # Mean=2s exponential decay
    ui_elements = []
    response_content = ""
    fallback_status = "none"
    ontology_match = False
    
    if is_ambiguous:
        # --- T026 Logic: Handle Ambiguous Queries ---
        log_info(f"Ambiguous query detected: '{query[:50]}...' (Conf: {confidence:.2f})")
        
        # Invoke deterministic rule-based fallback
        matched_intent, matched_entry = match_intent(query)
        
        if matched_entry:
            ontology_match = True
            response_content = generate_fallback(matched_entry, density)
            fallback_status = "matched"
            # Minimal UI generation based on density
            # For density 1: 1 element, density 3: 3 elements, etc.
            # Simulating a minimal UI structure
            ui_elements = [{"type": "fallback_button", "label": matched_entry.get('label', 'Action'), "id": i} for i in range(min(density, 10))]
        else:
            # "no-match" if no ontology entry
            fallback_status = "no-match"
            log_info(f"Ontology no-match for query: '{query[:50]}...'")
            # Return minimal UI (element) as per requirement
            ui_elements = [{"type": "minimal_fallback", "label": "Try again", "id": 0}]
            response_content = "I'm not sure how to help with that specific request based on current rules."
        
        # Latency injection for fallback (usually faster than gen, but we simulate)
        # In a real system, fallback is deterministic and fast. 
        # We inject a small, deterministic delay based on density to simulate processing.
        latency_injected = 0.05 * density 
        
    else:
        # High-Confidence path (simulated generative response)
        # In a real system, this would call the generative model.
        # We simulate the latency of a generative model here.
        latency_injected = 1.5 + (0.1 * density) # Base gen time + density cost
        response_content = f"Generated response for: {query}"
        ui_elements = [{"type": "gen_component", "id": i} for i in range(density)]
        fallback_status = "skipped"

    # 3. Patience Check
    if latency_injected > user_patience:
        log_info(f"User abandoned (Patience: {user_patience:.2f}s, Latency: {latency_injected:.2f}s)")
        total_time = user_patience
        abandonment_event = True
    else:
        total_time = latency_injected
        abandonment_event = False

    # 4. Scoring
    # Calculate alignment score using rubric
    # rubric.score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness
    intent_match = 1.0 if intent == ground_truth else 0.0
    latency_penalty = min(1.0, latency_injected / 5.0) # Penalty scales with latency
    ui_completeness = len(ui_elements) / max(DENSITY_LEVELS) # Normalized by max density
    
    alignment_score = calculate_alignment_score(
        intent_match=intent_match,
        latency_injected=latency_injected,
        ui_element_count=len(ui_elements),
        density=density
    )

    # Construct SimulationRun object
    run = SimulationRun(
        interaction_id=str(uuid.uuid4()),
        query=query,
        ground_truth_intent=ground_truth,
        routing_decision=routing_decision,
        is_ambiguous=is_ambiguous,
        fallback_status=fallback_status,
        ontology_match=ontology_match,
        latency_injected=latency_injected,
        user_patience=user_patience,
        total_time=total_time,
        abandonment_event=abandonment_event,
        ui_element_count=len(ui_elements),
        alignment_score=alignment_score,
        density=density,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

    return {
        "run": run,
        "is_ambiguous": is_ambiguous,
        "fallback_status": fallback_status,
        "ontology_match": ontology_match,
        "ui_elements": ui_elements
    }

def run_simulation(
    num_samples: int = 500,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run the full simulation pipeline over the annotated dataset.
    Iterates through density levels {1, 3, 5, 10} as per FR-004.
    """
    logger.info("Starting Simulation Run")
    
    # Load data
    df = load_annotated_data()
    if num_samples < len(df):
        df = df.sample(n=num_samples, random_state=42)
    else:
        num_samples = len(df)
    
    # Load Router Model
    model_path = get_processed_data_path() / "router_model" # Assuming T019 saves here
    if not model_path.exists():
        # Fallback to a default path if T019 saved elsewhere, or raise error
        # Per T019 description: "save model to code/models/router_model/"
        model_path = Path("code/models/router_model")
        if not model_path.exists():
            raise FileNotFoundError(f"Router model not found at {model_path}. Run T019 first.")
    
    router_model = load_quantized_model(str(model_path))
    
    results = []
    rng = np.random.default_rng(42)
    
    # Iterate through density levels
    for density in DENSITY_LEVELS:
        log_info(f"Processing density level: {density}")
        
        for idx, row in df.iterrows():
            try:
                result = simulate_interaction(row.to_dict(), router_model, density, rng)
                results.append({
                    "density": density,
                    "interaction_id": result["run"].interaction_id,
                    "query": row['query'],
                    "ground_truth_intent": row['ground_truth_intent'],
                    "predicted_intent": result["run"].routing_decision.intent,
                    "confidence": result["run"].routing_decision.confidence,
                    "is_ambiguous": result["is_ambiguous"],
                    "fallback_status": result["fallback_status"],
                    "ontology_match": result["ontology_match"],
                    "latency_injected": result["run"].latency_injected,
                    "total_time": result["run"].total_time,
                    "abandonment_event": result["run"].abandonment_event,
                    "ui_element_count": result["run"].ui_element_count,
                    "alignment_score": result["run"].alignment_score
                })
            except Exception as e:
                log_error(f"Error processing row {idx}: {e}")
                continue
    
    # Save results
    if not output_path:
        output_path = get_processed_data_path() / "simulation_results.csv"
    else:
        output_path = Path(output_path)
    
    ensure_dirs(output_path.parent)
    pd.DataFrame(results).to_csv(output_path, index=False)
    log_metric("simulation_completed", len(results))
    log_info(f"Simulation results saved to {output_path}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Run A2UI Latency Simulation")
    parser.add_argument("--samples", type=int, default=500, help="Number of samples to process")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()
    
    run_simulation(num_samples=args.samples, output_path=args.output)

if __name__ == "__main__":
    main()