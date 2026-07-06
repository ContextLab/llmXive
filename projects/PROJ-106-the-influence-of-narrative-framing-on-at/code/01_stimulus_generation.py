import argparse
import json
import os
import sys
import random
from pathlib import Path
import csv
import textstat
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Ensure we can import sibling utilities when run as a script
sys.path.insert(0, str(Path(__file__).parent))
from utils.logger import setup_logger, log_script_start, log_script_end, log_data_operation
from utils.random_utils import set_global_seed

logger = setup_logger(__name__)
analyzer = SentimentIntensityAnalyzer()

# Controlled templates for the two conditions
# These templates are designed to be identical in structure and length,
# differing only in the framing noun (Partner vs Tool).
TEMPLATES = {
    "Partner": [
        "Imagine you are working on a complex project with an AI system designed to act as a collaborative Partner. This AI Partner actively engages with your ideas, offering suggestions and building upon your thoughts in a conversational manner. It feels like working with a teammate who understands your goals and helps you navigate challenges together.",
        "In this scenario, the AI Partner adapts its communication style to match your preferences, creating a sense of mutual understanding. When you encounter difficulties, the Partner offers encouragement and alternative perspectives, much like a human colleague would. The interaction feels natural and supportive, fostering a sense of shared purpose."
    ],
    "Tool": [
        "Imagine you are working on a complex project using an AI system designed to function as a specialized Tool. This AI Tool processes information efficiently, providing data and suggestions based on your inputs in a functional manner. It operates like a sophisticated instrument that helps you execute tasks more effectively.",
        "In this scenario, the AI Tool responds to your commands with precision, delivering results based on its programming. When you encounter difficulties, the Tool provides optimized solutions and data-driven alternatives, much like a high-tech calculator. The interaction feels efficient and precise, maximizing your individual productivity."
    ]
}

def calculate_metrics(text: str) -> dict:
    """Calculate readability and sentiment metrics for a given text."""
    fk_score = textstat.flesch_reading_ease(text)
    fk_grade = textstat.flesch_kincaid_grade(text)
    sentiment = analyzer.polarity_scores(text)
    return {
        "flesch_reading_ease": fk_score,
        "flesch_kincaid_grade": fk_grade,
        "sentiment_compound": sentiment['compound'],
        "sentiment_pos": sentiment['pos'],
        "sentiment_neu": sentiment['neu'],
        "sentiment_neg": sentiment['neg']
    }

def generate_vignette(condition: str, seed: int = None) -> str:
    """Generate a vignette for the specified condition."""
    if seed is not None:
        random.seed(seed)
    
    if condition not in TEMPLATES:
        raise ValueError(f"Unknown condition: {condition}")
    
    # Select a template variant randomly if multiple exist
    template = random.choice(TEMPLATES[condition])
    return template

def validate_constraints(vignettes: dict, max_diff_readability: float = 2.0, max_diff_sentiment: float = 0.05) -> bool:
    """Validate that generated vignettes meet the constraints."""
    metrics = {k: calculate_metrics(v) for k, v in vignettes.items()}
    
    readability_diff = abs(metrics["Partner"]["flesch_reading_ease"] - metrics["Tool"]["flesch_reading_ease"])
    sentiment_diff = abs(metrics["Partner"]["sentiment_compound"] - metrics["Tool"]["sentiment_compound"])
    
    logger.info(f"Readability difference: {readability_diff:.2f} (Max allowed: {max_diff_readability})")
    logger.info(f"Sentiment difference: {sentiment_diff:.4f} (Max allowed: {max_diff_sentiment})")
    
    if readability_diff > max_diff_readability:
        logger.warning(f"Readability difference {readability_diff:.2f} exceeds threshold {max_diff_readability}")
        return False
    if sentiment_diff > max_diff_sentiment:
        logger.warning(f"Sentiment difference {sentiment_diff:.4f} exceeds threshold {max_diff_sentiment}")
        return False
        
    return True

def run_generation(max_attempts: int = 10) -> tuple:
    """Run the generation loop with validation."""
    for attempt in range(max_attempts):
        logger.info(f"Generation attempt {attempt + 1}/{max_attempts}")
        
        vignettes = {
            "Partner": generate_vignette("Partner"),
            "Tool": generate_vignette("Tool")
        }
        
        if validate_constraints(vignettes):
            metrics = {k: calculate_metrics(v) for k, v in vignettes.items()}
            return vignettes, metrics
        
        logger.info("Constraints not met, retrying...")
    
    logger.critical(f"Failed to generate balanced vignettes after {max_attempts} attempts.")
    raise RuntimeError("Could not generate vignettes meeting constraints.")

def save_vignettes(vignettes: dict, output_dir: str):
    """Save generated vignettes to CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for condition, text in vignettes.items():
        file_path = output_path / f"vignettes_{condition.lower()}.csv"
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["condition", "text", "id"])
            # Assign a generic ID for the stimulus version
            writer.writerow([condition, text, f"v1_{condition.lower()}"])
        
        log_data_operation("write", str(file_path), "csv")
        logger.info(f"Saved vignette for {condition} to {file_path}")

def save_metrics_log(metrics: dict, output_dir: str):
    """Save metrics to a JSON log file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    log_path = output_path / "vignette_metrics.json"
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
        
    log_data_operation("write", str(log_path), "json")
    logger.info(f"Saved metrics to {log_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate and save AI framing vignettes.")
    parser.add_argument("--output-dir", type=str, default="data/stimuli",
                        help="Directory to save output files")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    parser.add_argument("--max-attempts", type=int, default=10,
                        help="Maximum generation attempts")
    
    args = parser.parse_args()
    
    log_script_start("stimulus_generation")
    
    if args.seed is not None:
        set_global_seed(args.seed)
    
    try:
        vignettes, metrics = run_generation(max_attempts=args.max_attempts)
        save_vignettes(vignettes, args.output_dir)
        save_metrics_log(metrics, args.output_dir)
        logger.info("Stimulus generation completed successfully.")
    except Exception as e:
        logger.error(f"Stimulus generation failed: {e}")
        sys.exit(1)
    finally:
        log_script_end("stimulus_generation")

if __name__ == "__main__":
    main()
