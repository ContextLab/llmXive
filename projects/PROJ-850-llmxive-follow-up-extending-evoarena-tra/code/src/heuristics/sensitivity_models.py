import os
import sys
import csv
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.heuristics.conflict_detector import ConflictDetector, load_synthetic_pairs
from src.utils.seeding import set_deterministic_seed
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODELS = ['distilbert-base-uncased', 'bert-base-uncased']
THRESHOLDS = [0.5, 0.7, 0.9]
OUTPUT_PATH = Path('data/processed/sensitivity_analysis_models.csv')

def get_model_param_count(model_name: str) -> int:
    """Get the number of parameters for a given model name."""
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    return model.num_parameters()

def format_params(count: int) -> str:
    """Format parameter count to string (e.g., '110M', '88M')."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.0f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.0f}K"
    return str(count)

def calculate_metrics(predictions: List[bool], labels: List[bool]) -> Dict[str, float]:
    """Calculate accuracy, precision, recall, and F1 score."""
    if not predictions or not labels:
        return {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

    tp = sum(1 for p, l in zip(predictions, labels) if p and l)
    fp = sum(1 for p, l in zip(predictions, labels) if p and not l)
    fn = sum(1 for p, l in zip(predictions, labels) if not p and l)
    tn = sum(1 for p, l in zip(predictions, labels) if not p and not l)

    accuracy = (tp + tn) / len(predictions) if predictions else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

def run_sensitivity_analysis(model_name: str, threshold: float, synthetic_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run sensitivity analysis for a specific model and threshold."""
    set_deterministic_seed(42)

    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    detector = ConflictDetector(model_name=model_name, threshold=threshold)

    # Prepare inputs
    texts_a = [pair['patch_a'] for pair in synthetic_data]
    texts_b = [pair['patch_b'] for pair in synthetic_data]
    labels = [pair['is_contradiction'] for pair in synthetic_data]

    # Measure latency (inference time)
    start_time = time.perf_counter()
    predictions = detector.predict(texts_a, texts_b)
    end_time = time.perf_counter()

    latency = (end_time - start_time) / len(texts_a)  # Average latency per pair

    # Calculate metrics
    metrics = calculate_metrics(predictions, labels)

    return {
        'model_name': model_name,
        'params': format_params(get_model_param_count(model_name)),
        'accuracy': metrics['accuracy'],
        'latency': latency,
        'threshold_used': threshold
    }

def write_results_to_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Write sensitivity analysis results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['model_name', 'params', 'accuracy', 'latency', 'threshold_used']
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def main():
    """Main function to run sensitivity analysis across models and thresholds."""
    set_deterministic_seed(42)

    # Load synthetic pairs
    synthetic_data = load_synthetic_pairs(Path('data/raw/synthetic_pairs.json'))

    if not synthetic_data:
        print("Error: No synthetic data found. Run T005 first.")
        sys.exit(1)

    results = []

    for model_name in MODELS:
        print(f"Processing model: {model_name}")
        for threshold in THRESHOLDS:
            print(f"  Threshold: {threshold}")
            result = run_sensitivity_analysis(model_name, threshold, synthetic_data)
            results.append(result)
            print(f"    Accuracy: {result['accuracy']:.4f}, Latency: {result['latency']:.4f}s")

    # Write results to CSV
    write_results_to_csv(results, OUTPUT_PATH)
    print(f"Results written to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()
