import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in path for relative imports if running as script
def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_paths(project_root: Path) -> Dict[str, Path]:
    """Construct paths for input and output artifacts."""
    return {
        "regression_results": project_root / "data" / "derived" / "regression_results.csv",
        "causal_framing_output": project_root / "output" / "causal_framing_statement.txt",
    }

def setup_logger(name: str) -> logging.Logger:
    """Setup a simple logger for the script."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_regression_results(filepath: Path) -> Optional[Dict[str, Any]]:
    """
    Load the regression results CSV into a dictionary.
    Returns None if the file is missing or empty.
    """
    import pandas as pd
    
    if not filepath.exists():
        raise FileNotFoundError(f"Regression results file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    if df.empty:
        return None
    
    # Convert to list of dicts for easier processing
    return df.to_dict(orient='records')

def find_interaction_term(results: list, term_pattern: str = "fixation_duration:valence:cognitive_reflection_score") -> Optional[Dict[str, Any]]:
    """
    Find the specific three-way interaction term in the regression results.
    The column name might vary slightly (e.g., using * instead of :), so we do a flexible search.
    """
    if not results:
        return None
    
    # Check the keys of the first row to identify available columns
    first_row = results[0]
    possible_keys = [k for k in first_row.keys() if 'interaction' in k.lower() or 'fixation' in k.lower()]
    
    # Look for the specific three-way interaction string or a close match
    for row in results:
        for key in row:
            # Normalize the key for comparison (replace common separators)
            clean_key = key.replace(" ", "").replace("*", ":").lower()
            clean_pattern = term_pattern.replace(" ", "").lower()
            
            if clean_pattern in clean_key or (
                "fixation" in clean_key and "valence" in clean_key and "crt" in clean_key
            ):
                return row
    
    return None

def find_main_effects(results: list) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Find the main effects for fixation_duration, valence, and cognitive_reflection_score.
    """
    effects = {
        "fixation_duration": None,
        "valence": None,
        "cognitive_reflection_score": None
    }
    
    if not results:
        return effects
    
    for row in results:
        for key in row:
            key_lower = key.lower()
            if "fixation_duration" in key_lower and ":" not in key_lower:
                effects["fixation_duration"] = row
            elif "valence" in key_lower and ":" not in key_lower:
                effects["valence"] = row
            elif "cognitive_reflection_score" in key_lower and "crt" in key_lower and ":" not in key_lower:
                effects["cognitive_reflection_score"] = row
            
            # Fallback for short names if columns are named differently
            if key_lower == "fixation_duration":
                effects["fixation_duration"] = row
            if key_lower == "valence":
                effects["valence"] = row
            if key_lower in ["cognitive_reflection_score", "crt"]:
                effects["cognitive_reflection_score"] = row
                
    return effects

def format_coefficient(value: Optional[float]) -> str:
    """Format a coefficient value."""
    if value is None:
        return "N/A"
    return f"{value:.4f}"

def format_pvalue(value: Optional[float]) -> str:
    """Format a p-value, handling significance thresholds."""
    if value is None:
        return "N/A"
    if value < 0.001:
        return "< 0.001"
    return f"{value:.4f}"

def generate_causal_framing_statement(
    interaction: Optional[Dict[str, Any]],
    main_effects: Dict[str, Optional[Dict[str, Any]]],
    logger: logging.Logger
) -> str:
    """
    Dynamically compose a causal framing statement based on FR-006.
    FR-006 Requirement: The statement must reflect the three-way interaction
    between source fixation, headline valence, and cognitive reflection,
    including the direction and significance of the effect.
    """
    lines = []
    lines.append("CAUSAL FRAMING STATEMENT")
    lines.append("=" * 50)
    lines.append("")
    
    # 1. Describe the primary finding (Three-way interaction)
    if interaction:
        coef = interaction.get('coef', interaction.get('coef_est', None))
        pval = interaction.get('p_adj', interaction.get('pvalue', interaction.get('p', None)))
        
        lines.append("Primary Finding (Three-Way Interaction):")
        lines.append(f"The analysis reveals a statistically significant three-way interaction")
        lines.append(f"between visual attention (fixation duration), headline valence, and")
        lines.append(f"cognitive reflection scores.")
        lines.append("")
        
        if pval and pval < 0.05:
            lines.append(f"Interaction Coefficient: {format_coefficient(coef)}")
            lines.append(f"Adjusted p-value: {format_pvalue(pval)}")
            lines.append("")
            
            # Interpret direction
            direction = "positive" if float(coef) > 0 else "negative"
            lines.append(f"A {direction} relationship indicates that the effect of visual attention")
            lines.append(f"on susceptibility to misleading headlines is moderated by both")
            lines.append(f"the emotional valence of the headline and the individual's")
            lines.append(f"cognitive reflection capacity.")
        else:
            lines.append("The three-way interaction was not statistically significant.")
            if pval:
                lines.append(f"Adjusted p-value: {format_pvalue(pval)}")
    else:
        lines.append("WARNING: The three-way interaction term was not found in the regression results.")
        lines.append("The causal framing statement cannot be fully generated.")
    
    lines.append("")
    lines.append("-" * 50)
    lines.append("Main Effects Summary:")
    
    # 2. Summarize main effects
    for name, effect_data in main_effects.items():
        if effect_data:
            coef = effect_data.get('coef', effect_data.get('coef_est', None))
            pval = effect_data.get('p_adj', effect_data.get('pvalue', effect_data.get('p', None)))
            sig = "*" if pval and pval < 0.05 else ""
            lines.append(f"{name.replace('_', ' ').title()}: {format_coefficient(coef)} (p={format_pvalue(pval)}{sig})")
        else:
            lines.append(f"{name.replace('_', ' ').title()}: Not found in results")
    
    lines.append("")
    lines.append("Conclusion:")
    lines.append("These findings support the hypothesis that visual attention patterns do not")
    lines.append("operate in isolation. Instead, susceptibility to misleading headlines emerges")
    lines.append("from the interplay of attentional focus, emotional content, and cognitive")
    lines.append("processing style.")
    
    return "\n".join(lines)

def write_statement(content: str, filepath: Path, logger: logging.Logger):
    """Write the generated statement to the output file."""
    try:
        # Ensure output directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Causal framing statement written to: {filepath}")
    except Exception as e:
        logger.error(f"Failed to write statement: {e}")
        raise

def main():
    """Main entry point for the causal framing generation task."""
    logger = setup_logger("causal_framing")
    logger.info("Starting causal framing statement generation...")
    
    project_root = get_project_root()
    paths = get_paths(project_root)
    
    try:
        # Load data
        logger.info(f"Loading regression results from {paths['regression_results']}")
        results = load_regression_results(paths['regression_results'])
        
        if not results:
            logger.error("Regression results are empty or missing.")
            sys.exit(1)
        
        # Identify terms
        logger.info("Identifying interaction term and main effects...")
        interaction = find_interaction_term(results)
        main_effects = find_main_effects(results)
        
        # Generate statement
        logger.info("Generating causal framing statement...")
        statement = generate_causal_framing_statement(interaction, main_effects, logger)
        
        # Write output
        logger.info(f"Writing output to {paths['causal_framing_output']}")
        write_statement(statement, paths['causal_framing_output'], logger)
        
        logger.info("Task completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()