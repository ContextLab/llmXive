import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

# Import from existing API surface
from utils.config import get_config, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_cohort_data(
    prompt_cohort_path: str,
    classified_snippets_path: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the prompt-based cohort and the classified snippets dataset.
    
    Args:
        prompt_cohort_path: Path to prompt_cohort.parquet
        classified_snippets_path: Path to classified_snippets.parquet
        
    Returns:
        Tuple of (prompt_cohort_df, classified_snippets_df)
        
    Raises:
        FileNotFoundError: If required input files do not exist
        ValueError: If data loading fails
    """
    prompt_cohort_file = Path(prompt_cohort_path)
    classified_snippets_file = Path(classified_snippets_path)
    
    if not prompt_cohort_file.exists():
        raise FileNotFoundError(
            f"Prompt cohort file not found: {prompt_cohort_path}. "
            "Ensure T014b has completed successfully."
        )
    
    if not classified_snippets_file.exists():
        raise FileNotFoundError(
            f"Classified snippets file not found: {classified_snippets_path}. "
            "Ensure T014 has completed successfully."
        )
    
    try:
        prompt_cohort_df = pd.read_parquet(prompt_cohort_path)
        logger.info(f"Loaded prompt cohort: {len(prompt_cohort_df)} rows")
    except Exception as e:
        raise ValueError(f"Failed to load prompt cohort: {e}")
    
    try:
        classified_snippets_df = pd.read_parquet(classified_snippets_path)
        logger.info(f"Loaded classified snippets: {len(classified_snippets_df)} rows")
    except Exception as e:
        raise ValueError(f"Failed to load classified snippets: {e}")
    
    return prompt_cohort_df, classified_snippets_df

def segment_cohorts(
    prompt_cohort_df: pd.DataFrame,
    classified_snippets_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Segment the combined data into three cohorts:
    1. "Prompt-Based" - from the prompt cohort generation (T014b)
    2. "LLM-like" - from classified snippets where classification = "LLM"
    3. "Human" - from classified snippets where classification = "Human"
    
    Args:
        prompt_cohort_df: DataFrame from prompt generation
        classified_snippets_df: DataFrame with classification labels
        
    Returns:
        Combined DataFrame with a 'cohort_type' column
    """
    # Validate prompt cohort has required columns
    required_prompt_cols = ['snippet_id', 'code_content']
    missing_prompt_cols = [col for col in required_prompt_cols 
                           if col not in prompt_cohort_df.columns]
    if missing_prompt_cols:
        raise ValueError(
            f"Prompt cohort missing required columns: {missing_prompt_cols}"
        )
    
    # Validate classified snippets has required columns
    required_classified_cols = ['snippet_id', 'code_content', 'classification']
    missing_classified_cols = [col for col in required_classified_cols 
                               if col not in classified_snippets_df.columns]
    if missing_classified_cols:
        raise ValueError(
            f"Classified snippets missing required columns: {missing_classified_cols}"
        )
    
    # Create Prompt-Based cohort
    prompt_cohort_df = prompt_cohort_df.copy()
    prompt_cohort_df['cohort_type'] = 'Prompt-Based'
    
    # Filter and label LLM-like cohort
    llm_like_df = classified_snippets_df[classified_snippets_df['classification'] == 'LLM'].copy()
    llm_like_df['cohort_type'] = 'LLM-like'
    
    # Filter and label Human cohort
    human_df = classified_snippets_df[classified_snippets_df['classification'] == 'Human'].copy()
    human_df['cohort_type'] = 'Human'
    
    # Combine all cohorts
    combined_df = pd.concat([prompt_cohort_df, llm_like_df, human_df], ignore_index=True)
    
    logger.info(f"Segmented cohorts - Prompt-Based: {len(prompt_cohort_df)}, "
               f"LLM-like: {len(llm_like_df)}, Human: {len(human_df)}")
    
    return combined_df

def analyze_cohort_properties(
    cohort_df: pd.DataFrame
) -> Dict[str, Dict[str, Any]]:
    """
    Perform descriptive analysis of stylistic properties across cohorts.
    
    This function computes summary statistics for key features by cohort type.
    It does NOT make causal claims, only descriptive comparisons.
    
    Args:
        cohort_df: Combined DataFrame with 'cohort_type' column
        
    Returns:
        Dictionary with cohort-level statistics
    """
    cohort_types = ['Prompt-Based', 'LLM-like', 'Human']
    analysis_results = {}
    
    for cohort_type in cohort_types:
        subset = cohort_df[cohort_df['cohort_type'] == cohort_type]
        
        if len(subset) == 0:
            logger.warning(f"No data for cohort: {cohort_type}")
            analysis_results[cohort_type] = {"count": 0}
            continue
        
        stats = {
            "count": len(subset),
            "cohort_type": cohort_type
        }
        
        # Calculate statistics for numeric columns if they exist
        numeric_cols = subset.select_dtypes(include=['number']).columns.tolist()
        for col in numeric_cols:
            if col in ['count', 'snippet_id']:
                continue
            stats[f"{col}_mean"] = subset[col].mean()
            stats[f"{col}_std"] = subset[col].std()
            stats[f"{col}_min"] = subset[col].min()
            stats[f"{col}_max"] = subset[col].max()
        
        analysis_results[cohort_type] = stats
    
    return analysis_results

def run_cohort_segmentation(
    prompt_cohort_path: Optional[str] = None,
    classified_snippets_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main pipeline function to segment cohorts and perform descriptive analysis.
    
    Args:
        prompt_cohort_path: Path to prompt_cohort.parquet (default from config)
        classified_snippets_path: Path to classified_snippets.parquet (default from config)
        output_path: Path for output cohort_segments.parquet (default from config)
        
    Returns:
        Tuple of (segmented_dataframe, analysis_results_dict)
    """
    config = get_config()
    
    # Use config defaults if paths not provided
    if prompt_cohort_path is None:
        prompt_cohort_path = config.get('paths', {}).get('prompt_cohort', 'data/processed/prompt_cohort.parquet')
    if classified_snippets_path is None:
        classified_snippets_path = config.get('paths', {}).get('classified_snippets', 'data/processed/classified_snippets.parquet')
    if output_path is None:
        output_path = config.get('paths', {}).get('cohort_segments', 'data/processed/cohort_segments.parquet')
    
    logger.info(f"Loading data from: {prompt_cohort_path}, {classified_snippets_path}")
    
    # Load data
    prompt_cohort_df, classified_snippets_df = load_cohort_data(
        prompt_cohort_path, 
        classified_snippets_path
    )
    
    # Segment cohorts
    logger.info("Segmenting cohorts...")
    segmented_df = segment_cohorts(prompt_cohort_df, classified_snippets_df)
    
    # Perform descriptive analysis
    logger.info("Analyzing cohort properties...")
    analysis_results = analyze_cohort_properties(segmented_df)
    
    # Ensure output directory exists
    output_file = Path(output_path)
    ensure_directories([str(output_file.parent)])
    
    # Save segmented data
    segmented_df.to_parquet(output_path, index=False)
    logger.info(f"Saved segmented cohorts to: {output_path}")
    
    return segmented_df, analysis_results

def main():
    """Entry point for cohort analyzer script."""
    try:
        logger.info("Starting cohort analysis pipeline...")
        segmented_df, analysis_results = run_cohort_segmentation()
        
        # Log summary
        print("\n=== Cohort Segmentation Summary ===")
        for cohort_type, stats in analysis_results.items():
            if stats.get("count", 0) > 0:
                print(f"{cohort_type}: {stats['count']} snippets")
            else:
                print(f"{cohort_type}: No data available")
        
        print(f"\nOutput saved to: data/processed/cohort_segments.parquet")
        logger.info("Cohort analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()