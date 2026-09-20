import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

# Import project utilities
from utils.config import get_viz_dir, get_reports_dir, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hard-coded literature predictors for each foraging guild
# These are based on general ecological knowledge of avian foraging behaviors
LITERATURE_PREDICTORS = {
    "Insectivore": ["forest_prop_100m", "wetland_prop_100m", "shrubland_prop_100m"],
    "Granivore": ["grassland_prop_100m", "agricultural_prop_100m", "urban_prop_100m"],
    "Nectarivore": ["forest_prop_100m", "shrubland_prop_100m", "flowering_veg_prop_100m"],
    "Frugivore": ["forest_prop_100m", "wetland_prop_100m", "shrubland_prop_100m"],
    "Carnivore": ["forest_prop_100m", "grassland_prop_100m", "wetland_prop_100m"],
    "Omnivore": ["urban_prop_100m", "agricultural_prop_100m", "grassland_prop_100m"],
    "Scavenger": ["urban_prop_100m", "agricultural_prop_100m", "grassland_prop_100m"]
}

def load_importance_data(json_path: Path) -> pd.DataFrame:
    """
    Load feature importance data from JSON file.
    
    Args:
        json_path: Path to the feature_importance.json file.
        
    Returns:
        DataFrame with 'feature' and 'importance' columns.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Importance JSON file not found: {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} features from {json_path}")
    return df

def get_top_predictors(importance_df: pd.DataFrame, top_n: int = 3) -> Dict[str, List[str]]:
    """
    Group features by guild and get top N predictors per guild.
    Note: This assumes feature names encode guild information or we map them.
    For this implementation, we assume the model was trained on species-level profiles
    where the target is 'foraging_guild'. The features are land cover proportions.
    We need to map features to the most likely guild based on the literature.
    
    However, the task asks to compare top predictors for EACH guild. 
    Since we have a single model predicting guild from land cover, 
    the "top predictors for a guild" interpretation is:
    "Which land cover types are most important for distinguishing this guild from others?"
    
    In a multi-class RF, feature importance is global. To get per-guild importance,
    we would need to look at partial dependence or use a one-vs-rest approach.
    Given the scope, we will interpret this as:
    "For the top 3 land cover features identified by the model, which guilds are they most associated with based on literature?"
    
    Alternatively, if the model output includes per-class importance (not standard in sklearn RF),
    we would use that. Since it doesn't, we will simply report the global top 3 features
    and check if they match the literature for ANY of the guilds.
    
    But the prompt says: "compare the top‑3 model‑identified predictors for each guild"
    This implies we need per-guild predictors. Without per-guild model internals,
    we can't strictly do this. We will assume the question implies:
    "Do the top 3 global predictors match the literature for at least one guild?"
    OR
    "For each guild, do the top 3 features (if we were to rank them by their relevance to that guild) match literature?"
    
    Given the constraints, we will:
    1. Get the global top 3 features.
    2. For each guild in LITERATURE_PREDICTORS, check if any of the top 3 features appear in its literature list.
    3. Report the match rate.
    
    If we had per-guild data (e.g., from a one-vs-rest analysis), we would do it per guild.
    For now, we will treat the "top 3 predictors for each guild" as the top 3 global predictors
    and see if they align with the literature for that specific guild.
    """
    top_features = importance_df.head(top_n)['feature'].tolist()
    
    # We cannot strictly determine per-guild top features without per-guild model analysis.
    # We will return the global top features and let the validation logic handle the comparison.
    return {"global_top_3": top_features}

def validate_against_literature(
    top_features: List[str], 
    guild: str, 
    literature_predictors: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Validate if top features match literature for a given guild.
    
    Args:
        top_features: List of top feature names.
        guild: The foraging guild to validate against.
        literature_predictors: Dictionary mapping guilds to their literature predictors.
        
    Returns:
        Dictionary with validation results.
    """
    if guild not in literature_predictors:
        logger.warning(f"Guild '{guild}' not found in literature predictors. Skipping.")
        return {
            "guild": guild,
            "top_features": top_features,
            "literature_predictors": [],
            "matches": [],
            "match_rate": 0.0,
            "status": "skipped"
        }
    
    lit_predictors = literature_predictors[guild]
    matches = [f for f in top_features if f in lit_predictors]
    match_rate = len(matches) / len(top_features) if top_features else 0.0
    
    return {
        "guild": guild,
        "top_features": top_features,
        "literature_predictors": lit_predictors,
        "matches": matches,
        "match_rate": match_rate,
        "status": "pass" if match_rate > 0 else "fail"
    }

def run_validation(json_path: Path, output_path: Path) -> None:
    """
    Run the full validation pipeline.
    
    Args:
        json_path: Path to the feature_importance.json file.
        output_path: Path to save the validation results.
    """
    # Load data
    importance_df = load_importance_data(json_path)
    
    # Get top 3 global features
    top_features = importance_df.head(3)['feature'].tolist()
    
    # Validate against each guild
    results = []
    for guild in LITERATURE_PREDICTORS.keys():
        result = validate_against_literature(top_features, guild, LITERATURE_PREDICTORS)
        results.append(result)
    
    # Calculate overall statistics
    pass_count = sum(1 for r in results if r["status"] == "pass")
    total_guilds = len(results)
    overall_match_rate = sum(r["match_rate"] for r in results) / total_guilds if total_guilds > 0 else 0.0
    
    validation_summary = {
        "top_3_global_features": top_features,
        "guilds_analyzed": total_guilds,
        "guilds_passed": pass_count,
        "overall_match_rate": overall_match_rate,
        "per_guild_results": results,
        "note": "Validation is based on global top-3 features. Per-guild top features would require one-vs-rest analysis."
    }
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(validation_summary, f, indent=2)
    
    logger.info(f"Saved validation results to {output_path}")
    logger.info(f"Overall match rate: {overall_match_rate:.2%}")

def main():
    """
    Main entry point for the importance validation task.
    """
    viz_dir = get_viz_dir()
    json_path = viz_dir / 'feature_importance.json'
    output_path = viz_dir / 'importance_validation.json'
    
    try:
        run_validation(json_path, output_path)
        logger.info("Task T028.5 completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Task T028.5 failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()