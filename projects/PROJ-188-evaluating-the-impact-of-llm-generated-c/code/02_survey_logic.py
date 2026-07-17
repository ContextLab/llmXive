import random
import json
import csv
import logging
import os
from pathlib import Path
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_explanations(explanations_path: Path) -> Dict[str, str]:
    """Load explanations from JSON file."""
    with open(explanations_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {item["snippet_id"]: item["explanation"] for item in data}

def stratified_randomize(snippets: List[Dict[str, Any]], seed: int = 42) -> Dict[str, List[Dict[str, Any]]]:
    """Stratified randomization of snippets into three conditions."""
    random.seed(seed)
    conditions = {"A": [], "B": [], "C": []}
    
    # Group by complexity
    by_complexity = {"low": [], "medium": [], "high": []}
    for snippet in snippets:
        by_complexity[snippet["complexity"]].append(snippet)
    
    # Distribute evenly within each complexity group
    for complexity, items in by_complexity.items():
        random.shuffle(items)
        n = len(items)
        conditions["A"].extend(items[:n//3])
        conditions["B"].extend(items[n//3:2*n//3])
        conditions["C"].extend(items[2*n//3:])
    
    return conditions

def render_condition_a(snippet: Dict[str, Any]) -> str:
    """Condition A: Code only."""
    return f"CODE:\n{snippet['code']}"

def render_condition_b(snippet: Dict[str, Any], explanations: Dict[str, str]) -> str:
    """Condition B: Code + LLM Explanation."""
    explanation = explanations.get(snippet["snippet_id"], "No explanation available")
    return f"CODE:\n{snippet['code']}\n\nEXPLANATION:\n{explanation}"

def render_condition_c(snippet: Dict[str, Any]) -> str:
    """Condition C: Code + Official Docstring."""
    docstring = snippet.get("docstring", "No docstring available")
    return f"CODE:\n{snippet['code']}\n\nDOCSTRING:\n{docstring}"

def run_mock_survey(snippets: List[Dict[str, Any]], explanations: Dict[str, str], n: int = 10) -> List[Dict[str, Any]]:
    """Run mock survey with N participants."""
    random.seed(42)
    responses = []
    conditions = stratified_randomize(snippets)
    
    # Flatten conditions for participant assignment
    all_snippets = []
    for cond, items in conditions.items():
        for item in items:
            item["condition"] = cond
            all_snippets.append(item)
    
    random.shuffle(all_snippets)
    
    for i in range(n):
        snippet = all_snippets[i % len(all_snippets)]
        # Simulate latency > 30s
        latency_ms = random.randint(30001, 60000)
        # Simulate answer (random boolean)
        answer = random.choice([True, False])
        
        responses.append({
            "participant_id": f"p{i+1}",
            "condition": snippet["condition"],
            "snippet_id": snippet["snippet_id"],
            "answer": answer,
            "latency_ms": latency_ms,
            "timestamp": "2024-01-01T00:00:00Z"
        })
    
    return responses

def save_mock_responses(responses: List[Dict[str, Any]], output_path: Path) -> None:
    """Save mock responses to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["participant_id", "condition", "snippet_id", "answer", "latency_ms", "timestamp"])
        writer.writeheader()
        writer.writerows(responses)
    logger.info(f"Saved {len(responses)} mock responses to {output_path}")

def main():
    """Main entry point for survey logic."""
    # Load explanations
    explanations_path = Path(__file__).parent.parent / "data" / "intermediate" / "explanations.json"
    if explanations_path.exists():
        explanations = load_explanations(explanations_path)
    else:
        logger.warning("Explanations file not found, using empty dict")
        explanations = {}
    
    # Load curated snippets
    snippets_path = Path(__file__).parent.parent / "data" / "intermediate" / "curated_snippets.json"
    if snippets_path.exists():
        with open(snippets_path, 'r', encoding='utf-8') as f:
            snippets = json.load(f)
    else:
        logger.error("Curated snippets file not found")
        return
    
    # Run mock survey
    responses = run_mock_survey(snippets, explanations, n=10)
    
    # Save
    output_path = Path(__file__).parent.parent / "data" / "intermediate" / "mock_responses.csv"
    save_mock_responses(responses, output_path)
    
    logger.info("Mock survey complete")

if __name__ == "__main__":
    main()
