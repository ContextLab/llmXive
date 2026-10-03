import argparse
import json
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple

try:
    import textstat
except ImportError:
    print("Error: textstat is required. Install with: pip install textstat")
    sys.exit(1)

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    print("Error: vaderSentiment is required. Install with: pip install vaderSentiment")
    sys.exit(1)

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logger, log_script_start, log_script_end, log_data_operation, info
from utils.random_utils import set_global_seed, ensure_seed_set

logger = setup_logger()
analyzer = SentimentIntensityAnalyzer()

# Templates for the two conditions
# These are controlled templates that only change the framing (Partner vs Tool)
# while keeping structure, length, and other linguistic variables constant.
TEMPLATE_PARTNER = """
Imagine you are working on a complex project with a new AI system. This system is designed to act as a collaborative **Partner**.
It actively listens to your ideas, suggests creative directions, and challenges your assumptions to help you grow.
The AI operates with a shared sense of purpose, aiming to achieve mutual goals alongside you.
It remembers your past preferences and adapts its behavior to support your long-term development.
In this relationship, the AI is a proactive teammate that shares the burden of decision-making.
You and the AI work together as equals, blending human intuition with machine processing power.
The system's goal is to enhance your capabilities, making you a better professional through partnership.
"""

TEMPLATE_TOOL = """
Imagine you are working on a complex project with a new AI system. This system is designed to act as a specialized **Tool**.
It efficiently processes your inputs, executes specific commands, and provides accurate data for your decisions.
The Tool operates with a clear set of functions, aiming to complete assigned tasks with maximum precision.
It remembers your past inputs and adapts its output format to support your immediate workflow needs.
In this interaction, the Tool is a responsive utility that executes your specific instructions.
You direct the Tool, combining human strategy with machine speed and accuracy.
The system's goal is to enhance your efficiency, making you a faster professional through utility.
"""

def calculate_metrics(text: str) -> Dict[str, float]:
    """Calculate readability and sentiment metrics for a given text."""
    fk_score = textstat.flesch_kincaid_grade(text)
    sentiment = analyzer.polarity_scores(text)
    return {
        "flesch_kincaid_grade": fk_score,
        "sentiment_compound": sentiment['compound'],
        "sentiment_pos": sentiment['pos'],
        "sentiment_neg": sentiment['neg'],
        "sentiment_neu": sentiment['neu']
    }

def generate_vignette(condition: str) -> str:
    """Generate a vignette based on the specified condition."""
    if condition == "Partner":
        return TEMPLATE_PARTNER.strip()
    elif condition == "Tool":
        return TEMPLATE_TOOL.strip()
    else:
        raise ValueError(f"Unknown condition: {condition}")

def validate_constraints(vignettes: Dict[str, str], max_attempts: int = 10) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the generated vignettes meet the readability and sentiment constraints.
    Returns (success, metrics_log).
    """
    metrics = {}
    for condition, text in vignettes.items():
        metrics[condition] = calculate_metrics(text)

    # Check Readability Constraint (FR-001): Flesch-Kincaid diff <= 2.0
    fk_diff = abs(metrics["Partner"]["flesch_kincaid_grade"] - metrics["Tool"]["flesch_kincaid_grade"])
    if fk_diff > 2.0:
        logger.warning(f"Readability constraint failed: diff={fk_diff:.2f} > 2.0")
        return False, metrics

    # Check Sentiment Constraint (FR-010): Compound sentiment diff <= 0.05
    sent_diff = abs(metrics["Partner"]["sentiment_compound"] - metrics["Tool"]["sentiment_compound"])
    if sent_diff > 0.05:
        logger.warning(f"Sentiment constraint failed: diff={sent_diff:.2f} > 0.05")
        return False, metrics

    logger.info(f"Constraints met. FK Diff: {fk_diff:.2f}, Sentiment Diff: {sent_diff:.2f}")
    return True, metrics

def run_generation(seed: int, max_attempts: int = 10) -> Tuple[Dict[str, str], Dict[str, Any], bool]:
    """
    Run the generation loop. Since templates are static in this implementation,
    the first attempt will always succeed if the templates are well-crafted.
    In a more complex implementation, this would loop over variations.
    """
    set_global_seed(seed)
    ensure_seed_set()

    vignettes = {
        "Partner": generate_vignette("Partner"),
        "Tool": generate_vignette("Tool")
    }

    success, metrics = validate_constraints(vignettes, max_attempts)
    
    if not success:
        logger.error("Failed to generate vignettes meeting constraints after max attempts.")
        # In a real loop, we would regenerate here. Since templates are fixed, we fail.
        return vignettes, metrics, False

    return vignettes, metrics, True

def save_vignettes(vignettes: Dict[str, str], output_dir: Path):
    """Save vignettes to CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for condition, text in vignettes.items():
        filename = f"vignettes_{condition.lower()}.csv"
        filepath = output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['condition', 'text'])
            writer.writerow([condition, text])
        
        log_data_operation("save", str(filepath), 1)
        logger.info(f"Saved vignette to {filepath}")

def save_metrics_log(metrics: Dict[str, Any], output_dir: Path, seed: int):
    """Save generation metrics to a JSON log."""
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "generation_metrics.json"
    
    log_entry = {
        "seed": seed,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Saved metrics log to {log_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate and validate AI framing vignettes.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="data/stimuli", help="Output directory for CSVs")
    parser.add_argument("--max-attempts", type=int, default=10, help="Max attempts to meet constraints")
    
    args = parser.parse_args()
    
    log_script_start("01_stimulus_generation", args)
    
    output_path = Path(args.output_dir)
    
    vignettes, metrics, success = run_generation(args.seed, args.max_attempts)
    
    if success:
        save_vignettes(vignettes, output_path)
        save_metrics_log(metrics, output_path, args.seed)
        log_script_end("01_stimulus_generation", "Success")
    else:
        log_script_end("01_stimulus_generation", "Failed constraints")
        sys.exit(1)

if __name__ == "__main__":
    main()
