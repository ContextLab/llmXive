import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/cohort_analyzer.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants for cohort identification
HUMAN_COHORT_LABEL = 'human'
LLM_CONTEXT_COHORT_LABEL = 'llm-context'
LLM_PROMPT_COHORT_LABEL = 'llm-prompt'

def load_cohort_data(prompt_based_path: Path, context_based_path: Path, human_path: Path) -> pd.DataFrame:
    """
    Loads data from three distinct parquet files and combines them into a single DataFrame.
    
    Args:
        prompt_based_path: Path to prompt_based_snippets.parquet
        context_based_path: Path to context_based_snippets.parquet
        human_path: Path to classified_snippets.parquet (containing human/llm-like)
        
    Returns:
        Combined DataFrame with 'generation_source' column populated.
        
    Raises:
        FileNotFoundError: If any of the input files do not exist.
        ValueError: If the expected columns are missing.
    """
    if not prompt_based_path.exists():
        raise FileNotFoundError(f"Prompt-based snippets file not found: {prompt_based_path}")
    if not context_based_path.exists():
        raise FileNotFoundError(f"Context-based snippets file not found: {context_based_path}")
    if not human_path.exists():
        raise FileNotFoundError(f"Human snippets file not found: {human_path}")

    logger.info(f"Loading prompt-based snippets from {prompt_based_path}")
    df_prompt = pd.read_parquet(prompt_based_path)
    
    logger.info(f"Loading context-based snippets from {context_based_path}")
    df_context = pd.read_parquet(context_based_path)
    
    logger.info(f"Loading human snippets from {human_path}")
    df_human = pd.read_parquet(human_path)

    # Validate required columns exist
    required_cols = ['snippet_id', 'code_content']
    for name, df in [('prompt', df_prompt), ('context', df_context), ('human', df_human)]:
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns {missing} in {name} dataset")

    # Assign generation_source labels
    df_prompt['generation_source'] = LLM_PROMPT_COHORT_LABEL
    df_context['generation_source'] = LLM_CONTEXT_COHORT_LABEL
    
    # For human dataset, we need to ensure we only take the 'human' cohort if it contains 'llm-like'
    # The task description implies we are segmenting into the three specific cohorts.
    # Assuming the human dataset from T014 contains both 'human' and 'llm-like' in 'author_type'.
    # We filter for 'human' to strictly match the cohort definition.
    if 'author_type' in df_human.columns:
        df_human = df_human[df_human['author_type'] == HUMAN_COHORT_LABEL].copy()
        logger.info(f"Filtered human dataset to {len(df_human)} rows (author_type='human')")
    else:
        # If author_type doesn't exist, assume all are human as per T014 output expectation for this specific merge
        logger.warning("author_type column not found in human dataset, assuming all are human.")
    
    df_human['generation_source'] = HUMAN_COHORT_LABEL

    # Combine
    combined_df = pd.concat([df_prompt, df_context, df_human], ignore_index=True)
    
    # Reset index to ensure clean integer index
    combined_df.reset_index(drop=True, inplace=True)
    
    logger.info(f"Combined dataset shape: {combined_df.shape}")
    logger.info(f"Generation source distribution:\n{combined_df['generation_source'].value_counts()}")
    
    return combined_df

def segment_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures the DataFrame is properly segmented and adds any derived segment columns if necessary.
    Currently, the 'generation_source' column acts as the primary segment identifier.
    
    Args:
        df: The combined DataFrame.
        
    Returns:
        The DataFrame with verified segmentation.
    """
    # Verify that all rows have a valid generation_source
    valid_sources = {LLM_PROMPT_COHORT_LABEL, LLM_CONTEXT_COHORT_LABEL, HUMAN_COHORT_LABEL}
    invalid_mask = ~df['generation_source'].isin(valid_sources)
    if invalid_mask.any():
        logger.warning(f"Found {invalid_mask.sum()} rows with invalid generation_source values. Dropping them.")
        df = df[~invalid_mask]
    
    return df

def analyze_cohort_properties(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes basic statistics for each cohort to verify data integrity.
    
    Args:
        df: The segmented DataFrame.
        
    Returns:
        A dictionary containing counts and basic stats per cohort.
    """
    stats = {}
    for source in [LLM_PROMPT_COHORT_LABEL, LLM_CONTEXT_COHORT_LABEL, HUMAN_COHORT_LABEL]:
        subset = df[df['generation_source'] == source]
        stats[source] = {
            'count': len(subset),
            'columns': list(subset.columns),
            'dtypes': subset.dtypes.astype(str).to_dict()
        }
        if 'file_size' in subset.columns:
            stats[source]['avg_file_size'] = subset['file_size'].mean()
        if 'complexity_score' in subset.columns:
            stats[source]['avg_complexity'] = subset['complexity_score'].mean()
    
    return stats

def run_cohort_segmentation(
    prompt_based_path: Optional[Path] = None,
    context_based_path: Optional[Path] = None,
    human_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main entry point to run the full cohort segmentation pipeline.
    
    Args:
        prompt_based_path: Path to prompt_based_snippets.parquet. Defaults to data/processed/prompt_based_snippets.parquet.
        context_based_path: Path to context_based_snippets.parquet. Defaults to data/processed/context_based_snippets.parquet.
        human_path: Path to classified_snippets.parquet. Defaults to data/processed/classified_snippets.parquet.
        output_path: Path to write the output parquet. Defaults to data/processed/cohort_segments.parquet.
        
    Returns:
        The segmented DataFrame.
    """
    # Default paths
    data_dir = Path('data/processed')
    if prompt_based_path is None:
        prompt_based_path = data_dir / 'prompt_based_snippets.parquet'
    if context_based_path is None:
        context_based_path = data_dir / 'context_based_snippets.parquet'
    if human_path is None:
        human_path = data_dir / 'classified_snippets.parquet'
    if output_path is None:
        output_path = data_dir / 'cohort_segments.parquet'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting Cohort Segmentation Pipeline")
    
    try:
        # Load
        df = load_cohort_data(prompt_based_path, context_based_path, human_path)
        
        # Segment
        df = segment_cohorts(df)
        
        # Analyze
        analysis = analyze_cohort_properties(df)
        logger.info("Cohort Analysis Results:")
        for source, stats in analysis.items():
            logger.info(f"  {source}: count={stats['count']}")
        
        # Verify output requirement: exactly three unique values
        unique_sources = set(df['generation_source'].unique())
        expected_sources = {LLM_PROMPT_COHORT_LABEL, LLM_CONTEXT_COHORT_LABEL, HUMAN_COHORT_LABEL}
        
        if unique_sources != expected_sources:
            logger.error(f"Verification Failed: Expected {expected_sources}, got {unique_sources}")
            raise ValueError(f"Cohort segmentation failed: Missing or extra cohorts. Expected {expected_sources}, found {unique_sources}")
        
        # Write output
        logger.info(f"Writing segmented data to {output_path}")
        df.to_parquet(output_path, index=False)
        
        logger.info("Cohort Segmentation Pipeline completed successfully.")
        return df

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        raise
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during cohort segmentation: {e}", exc_info=True)
        raise

def main():
    """
    CLI entry point for the cohort analyzer.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Segment code snippets into LLM-Prompt, LLM-Context, and Human cohorts.')
    parser.add_argument('--prompt-path', type=str, help='Path to prompt_based_snippets.parquet')
    parser.add_argument('--context-path', type=str, help='Path to context_based_snippets.parquet')
    parser.add_argument('--human-path', type=str, help='Path to classified_snippets.parquet')
    parser.add_argument('--output-path', type=str, help='Path to output cohort_segments.parquet')
    
    args = parser.parse_args()
    
    try:
        run_cohort_segmentation(
            prompt_based_path=Path(args.prompt_path) if args.prompt_path else None,
            context_based_path=Path(args.context_path) if args.context_path else None,
            human_path=Path(args.human_path) if args.human_path else None,
            output_path=Path(args.output_path) if args.output_path else None
        )
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()