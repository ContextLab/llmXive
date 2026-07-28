import argparse
import json
import os
import sys
import random
from pathlib import Path
import csv
import textstat
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Ensure we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))
from utils.logger import setup_logger, log_script_start, log_script_end, info, error
from utils.random_utils import set_global_seed, ensure_seed_set

logger = setup_logger("stimulus_generation")

# Constants
VIGNETTE_TEMPLATES = {
    "partner": [
        "Imagine you are working on a collaborative project with an AI system. "
        "This system is designed to act as a **Partner**, working alongside you as an equal team member. "
        "It contributes ideas, challenges your assumptions, and shares responsibility for the outcome. "
        "You interact with it as you would with a human colleague, trusting its input as part of a shared goal.",
        "Consider a scenario where you are collaborating with an AI **Partner**. "
        "This AI is not just a tool; it is a co-pilot that actively participates in decision-making. "
        "It offers suggestions, critiques your work constructively, and helps navigate complex problems. "
        "The relationship is defined by mutual respect and a joint commitment to success.",
        "You are paired with an AI **Partner** for a creative task. "
        "This system is designed to be an active participant, bringing its own 'perspective' to the table. "
        "It engages in dialogue, debates points, and co-creates solutions with you. "
        "You view it as a teammate whose contributions are integral to the final result."
    ],
    "tool": [
        "Imagine you are working on a project and using an AI system as a **Tool**. "
        "This system is designed to assist you by performing specific tasks efficiently. "
        "It processes data, generates drafts, and provides information when requested. "
        "You control the workflow, directing the tool to execute commands and produce outputs as needed.",
        "Consider a scenario where you are using an AI **Tool** to support your work. "
        "This AI is a utility designed to increase your productivity. "
        "It handles repetitive tasks, organizes information, and offers quick responses to queries. "
        "You are the operator, utilizing the tool's capabilities to achieve your specific objectives.",
        "You are utilizing an AI **Tool** for a creative task. "
        "This system is a resource that you command to generate content or analyze data. "
        "It follows your instructions precisely, acting as an extension of your own capabilities. "
        "You maintain full authority over the process, using the tool to streamline your workflow."
    ]
}

def calculate_metrics(text: str) -> dict:
    """Calculate readability and sentiment metrics for a given text."""
    fk_score = textstat.flesch_kincaid_grade(text)
    fk_reading = textstat.flesch_reading_ease(text)
    sentiment = SentimentIntensityAnalyzer().polarity_scores(text)
    return {
        "flesch_kincaid_grade": fk_score,
        "flesch_reading_ease": fk_reading,
        "sentiment_compound": sentiment['compound'],
        "sentiment_pos": sentiment['pos'],
        "sentiment_neu": sentiment['neu'],
        "sentiment_neg": sentiment['neg']
    }

def generate_vignette(condition: str, seed: int) -> str:
    """Generate a vignette for the specified condition using a controlled seed."""
    set_global_seed(seed)
    templates = VIGNETTE_TEMPLATES[condition]
    selected_template = random.choice(templates)
    return selected_template

def validate_constraints(metrics_partner: dict, metrics_tool: dict) -> bool:
    """
    Validate that readability and sentiment constraints are met.
    FR-001: Flesch-Kincaid diff <= 2.0
    FR-010: VADER compound diff <= 0.05
    """
    fk_diff = abs(metrics_partner['flesch_kincaid_grade'] - metrics_tool['flesch_kincaid_grade'])
    sent_diff = abs(metrics_partner['sentiment_compound'] - metrics_tool['sentiment_compound'])

    if fk_diff > 2.0:
        logger.warning(f"Flesch-Kincaid diff {fk_diff:.2f} exceeds 2.0 limit.")
        return False
    if sent_diff > 0.05:
        logger.warning(f"Sentiment diff {sent_diff:.2f} exceeds 0.05 limit.")
        return False

    logger.info(f"Constraints met: FK diff={fk_diff:.2f}, Sent diff={sent_diff:.2f}")
    return True

def run_generation(seed: int = 42, max_attempts: int = 10) -> tuple:
    """
    Generate vignettes for both conditions, ensuring constraints are met.
    Returns (partner_text, tool_text, metrics_log) or raises ValueError if constraints fail.
    """
    set_global_seed(seed)
    
    for attempt in range(max_attempts):
        # Generate texts
        partner_text = generate_vignette("partner", seed + attempt * 100)
        tool_text = generate_vignette("tool", seed + attempt * 200)
        
        # Calculate metrics
        metrics_partner = calculate_metrics(partner_text)
        metrics_tool = calculate_metrics(tool_text)
        
        # Validate
        if validate_constraints(metrics_partner, metrics_tool):
            metrics_log = {
                "attempt": attempt + 1,
                "partner": metrics_partner,
                "tool": metrics_tool,
                "success": True
            }
            return partner_text, tool_text, metrics_log
        
        logger.info(f"Attempt {attempt + 1} failed constraints, retrying...")

    raise ValueError(f"Failed to generate vignettes meeting constraints after {max_attempts} attempts.")

def save_vignettes(partner_text: str, tool_text: str, output_dir: Path):
    """Save generated vignettes to CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    partner_path = output_dir / "vignettes_partner.csv"
    tool_path = output_dir / "vignettes_tool.csv"
    
    with open(partner_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["condition", "vignette_text"])
        writer.writerow(["partner", partner_text])
    
    with open(tool_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["condition", "vignette_text"])
        writer.writerow(["tool", tool_text])
    
    logger.info(f"Vignettes saved to {partner_path} and {tool_path}")

def save_metrics_log(metrics_log: dict, output_dir: Path):
    """Save generation metrics to a JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "generation_metrics.json"
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_log, f, indent=2)
    logger.info(f"Metrics log saved to {log_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate and export AI vignettes.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--max-attempts", type=int, default=10, help="Max attempts to meet constraints")
    parser.add_argument("--output-dir", type=str, default="data/stimuli", help="Output directory for CSVs")
    args = parser.parse_args()

    log_script_start(logger, "stimulus_generation", args)
    
    try:
        partner_text, tool_text, metrics_log = run_generation(args.seed, args.max_attempts)
        output_path = Path(args.output_dir)
        save_vignettes(partner_text, tool_text, output_path)
        save_metrics_log(metrics_log, output_path)
        log_script_end(logger, "stimulus_generation", "Success")
    except Exception as e:
        error(logger, f"Generation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
