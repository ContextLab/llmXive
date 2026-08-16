import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
from scipy import stats
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Correlation Logic (from T012) ---

def compute_pairwise_correlations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Compute pairwise Pearson correlations for all numeric columns.
    Returns a list of dicts with x, y, r, p, n.
    """
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    correlations = []

    for i, col_x in enumerate(numeric_cols):
        for col_y in numeric_cols[i+1:]:
            # Drop pairs with missing values
            mask = df[col_x].notna() & df[col_y].notna()
            x_vals = df.loc[mask, col_x]
            y_vals = df.loc[mask, col_y]
            n = len(x_vals)

            if n < 2:
                continue

            r, p_value = stats.pearsonr(x_vals, y_vals)
            
            correlations.append({
                "var_x": col_x,
                "var_y": col_y,
                "r_value": float(r),
                "p_value": float(p_value),
                "n": n
            })
    
    return correlations

def identify_strongest_relationship(correlations: List[Dict[str, Any]], alpha: float = 0.05) -> Optional[Dict[str, Any]]:
    """
    Identify the relationship with the highest absolute correlation 
    that is statistically significant (p < alpha).
    """
    significant = [c for c in correlations if c["p_value"] < alpha]
    if not significant:
        return None
    
    # Sort by absolute r value descending
    significant.sort(key=lambda x: abs(x["r_value"]), reverse=True)
    return significant[0]

# --- LLM Narrative Generation (T013 Implementation) ---

def generate_narrative(top_relationship: Dict[str, Any], df_stats: Optional[Dict[str, Any]] = None) -> str:
    """
    Uses a lightweight local LLM (Phi-3-mini via HuggingFace) to summarize 
    the top correlation into a textual story.
    
    Falls back to a deterministic template if the LLM is unavailable or fails,
    ensuring the pipeline always produces a result without hallucinating data.
    """
    var_x = top_relationship["var_x"]
    var_y = top_relationship["var_y"]
    r_val = top_relationship["r_value"]
    p_val = top_relationship["p_value"]
    n = top_relationship["n"]

    direction = "positive" if r_val > 0 else "negative"
    strength = "weak"
    if abs(r_val) > 0.7:
        strength = "strong"
    elif abs(r_val) > 0.4:
        strength = "moderate"
    
    # Prepare context for the LLM
    context = f"""
    Dataset Statistics Summary:
    - Total samples: {n}
    - Variable X: {var_x}
    - Variable Y: {var_y}
    - Correlation Coefficient (r): {r_val:.4f} ({direction} {strength} correlation)
    - P-value: {p_val:.6f} (Significant at p < 0.05)
    
    Task: Write a single-sentence, neutral, data-driven narrative describing this relationship. 
    Do not imply causation. Use phrases like "is associated with" or "correlates with".
    """

    try:
        # Load tokenizer and model
        # Using a small, efficient model suitable for local execution
        model_name = "microsoft/Phi-3-mini-4k-instruct"
        
        logger.info(f"Loading LLM model: {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)
        
        logger.info("Generating narrative...")
        messages = [
            {"role": "user", "content": context}
        ]
        
        input_ids = tokenizer.apply_chat_template(messages, return_tensors="pt")
        
        # Generate with constraints to ensure brevity and neutrality
        output = model.generate(
            input_ids, 
            max_new_tokens=50, 
            do_sample=True, 
            temperature=0.3, 
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )
        
        response = tokenizer.decode(output[0][input_ids.shape[1]:], skip_special_tokens=True)
        
        # Basic sanitization: ensure no "causes" or "drives" slips through
        # (LLMs can sometimes be causal, so we enforce associational language)
        sanitized_response = response.replace("causes", "is associated with").replace("drives", "correlates with")
        
        return sanitized_response.strip()

    except Exception as e:
        logger.warning(f"LLM generation failed ({e}). Falling back to deterministic template.")
        # Fallback template that is strictly compliant with FR-007 (associational)
        return (
            f"A {strength} {direction} correlation (r={r_val:.4f}, p={p_val:.6f}, n={n}) "
            f"was observed between {var_x} and {var_y}, indicating they are statistically associated."
        )

# --- Pipeline Integration ---

def run_baseline_analysis(df: pd.DataFrame, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Orchestrates the full baseline analysis: correlation -> identification -> narrative.
    """
    config = get_config()
    alpha = config.get("statistical_significance_threshold", 0.05)
    
    logger.info("Computing pairwise correlations...")
    correlations = compute_pairwise_correlations(df)
    
    if not correlations:
        logger.error("No numeric correlations found.")
        return {
            "status": "no_data",
            "primary_narrative": "No numeric data available for correlation analysis."
        }
    
    logger.info("Identifying strongest relationship...")
    top_rel = identify_strongest_relationship(correlations, alpha)
    
    if not top_rel:
        logger.warning("No statistically significant relationships found.")
        return {
            "status": "no_significance",
            "primary_narrative": "No statistically significant correlations (p < 0.05) were found in the dataset."
        }
    
    logger.info("Generating narrative...")
    narrative_text = generate_narrative(top_rel)
    
    result = {
        "status": "success",
        "primary_narrative": narrative_text,
        "top_relationship": {
            "var_x": top_rel["var_x"],
            "var_y": top_rel["var_y"],
            "r_value": top_rel["r_value"],
            "p_value": top_rel["p_value"],
            "significance": "significant" if top_rel["p_value"] < alpha else "not_significant"
        },
        "all_correlations": correlations # Optional: include full list if needed for debugging
    }
    
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Baseline results written to {output_path}")
    
    return result

def main():
    """
    CLI Entry point for baseline analysis.
    Expects a processed CSV file path as argument or uses config defaults.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run Baseline Narrative Analysis")
    parser.add_argument("--input", type=str, required=True, help="Path to processed CSV")
    parser.add_argument("--output", type=str, default="output/baseline_result.json", help="Path to output JSON")
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.input}...")
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return 1
    
    result = run_baseline_analysis(df, args.output)
    
    if result["status"] == "success":
        print(json.dumps(result, indent=2))
        return 0
    else:
        print(json.dumps(result, indent=2))
        return 0 # Still return 0 as the pipeline completed, just found no signal

if __name__ == "__main__":
    main()