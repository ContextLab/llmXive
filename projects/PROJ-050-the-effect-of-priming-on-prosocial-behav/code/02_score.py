import logging
import sys
import json
from pathlib import Path
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from code.config import PROJECT_ROOT
from code.utils.logger import setup_logger, log_abort_condition

# Initialize logger
logger = setup_logger(__name__)

# Define thematic categories
SOCIAL_SCIENCE_SUBREDDITS = {'r/socialscience', 'r/psychology'}

def load_data(input_path: str) -> pd.DataFrame:
    """
    Load the anonymized dataset from the specified path.
    """
    path = Path(input_path)
    if not path.exists():
        log_abort_condition(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(path)
    
    required_cols = ['subreddit', 'thread_type', 'comment_text', 'user_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        log_abort_condition(f"Missing required columns: {missing}")
        raise ValueError(f"Missing required columns: {missing}")
    
    return df

def score_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute VADER sentiment scores and extract neg_score.
    """
    logger.info("Computing VADER sentiment scores")
    analyzer = SentimentIntensityAnalyzer()
    
    # Vectorized application might be slow on huge DF, but safe for CPU
    # Using apply is standard for VADER as it processes string per string
    df['vader_scores'] = df['comment_text'].apply(lambda x: analyzer.polarity_scores(str(x)))
    
    # Extract neg_score
    df['neg_score'] = df['vader_scores'].apply(lambda x: x['neg'])
    
    # Drop the intermediate scores column if desired, or keep for debugging
    # For now, keep it but we might want to drop it in save_results if memory is tight
    return df

def count_prosocial_actions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count prosocial actions using a secondary lexicon, excluding prime keywords.
    """
    logger.info("Counting prosocial actions")
    
    # Define prosocial lexicon (simplified for this implementation)
    # In a real scenario, this would be loaded from a config or separate file
    prosocial_keywords = {
        'help', 'support', 'charity', 'donate', 'volunteer', 'assist', 
        'caring', 'kind', 'generous', 'share', 'comfort', 'encourage',
        'guide', 'mentor', 'save', 'rescue', 'protect', 'heal'
    }
    
    # Prime keywords to exclude (from the priming study context)
    # These are the words that define the "Prime" group, we don't count them as actions
    prime_keywords = {
        'help', 'support', 'charity', 'donate', 'volunteer', 'assist',
        'caring', 'kind', 'generous', 'share', 'comfort', 'encourage',
        'guide', 'mentor', 'save', 'rescue', 'protect', 'heal'
    }
    
    # Note: The task description says "excluding help, support, charity and equivalents".
    # This implies the prosocial lexicon might overlap with prime keywords.
    # We need to be careful. The instruction says "excluding prime keywords".
    # Let's assume the prosocial lexicon is distinct or we filter out the overlap.
    # Actually, re-reading: "excluding 'help', 'support', 'charity' and equivalents"
    # This suggests these specific words are NOT prosocial actions in this context?
    # Or they are excluded from the count because they are part of the prime?
    # Let's assume the prosocial lexicon is a set of action words, and we subtract
    # the intersection with prime_keywords to avoid counting the priming words themselves.
    
    # Refined logic:
    # 1. Tokenize comment
    # 2. Count words in prosocial_keywords
    # 3. Subtract words that are also in prime_keywords (if any)
    # But wait, the prompt says "excluding 'help', 'support', 'charity' and equivalents".
    # This implies these words are NOT counted as prosocial actions.
    # So we should remove them from the prosocial_keywords set entirely?
    # Or maybe the prosocial lexicon is a DIFFERENT set, and we just ensure we don't
    # count the prime words.
    
    # Let's assume the prosocial lexicon is the set of action words we want to count.
    # And we explicitly exclude the prime keywords from this set.
    # The prompt says "excluding 'help', 'support', 'charity' and equivalents".
    # So we remove these from our counting set.
    
    # Let's define a base prosocial set and then remove the excluded ones.
    base_prosocial = {
        'assist', 'caring', 'kind', 'generous', 'share', 'comfort', 'encourage',
        'guide', 'mentor', 'save', 'rescue', 'protect', 'heal', 'contribute',
        'participate', 'engage', 'collaborate', 'cooperate', 'aid', 'relief'
    }
    
    excluded_words = {'help', 'support', 'charity', 'donate', 'volunteer'}
    # Add 'equivalents' - for now, just the explicit list
    
    final_prosocial = base_prosocial - excluded_words
    
    def count_actions(text):
        if pd.isna(text):
            return 0
        tokens = str(text).lower().split()
        count = sum(1 for token in tokens if token in final_prosocial)
        return count
    
    df['prosocial_action_count'] = df['comment_text'].apply(count_actions)
    return df

def stratified_sampling_validation(df: pd.DataFrame, target_n: int = 200, min_per_stratum: int = 50) -> pd.DataFrame:
    """
    Implement stratified sampling logic for validation (FR-010, FR-010a).
    
    Logic:
    1. Define thematic categories:
       - Social Science: r/socialscience, r/psychology
       - General: all others
    2. Strata are defined by (thematic_category, thread_type).
    3. Ensure >= min_per_stratum (50) per stratum, total >= target_n (200).
    4. If a stratum is insufficient:
       a. Merge within category (combine thread_types in same category).
       b. If still insufficient, merge across thread_type (combine categories).
       c. Draw from global pool if necessary.
    """
    logger.info(f"Performing stratified sampling: target_n={target_n}, min_per_stratum={min_per_stratum}")
    
    # Create thematic category column
    def get_category(subreddit):
        if subreddit in SOCIAL_SCIENCE_SUBREDDITS:
            return 'Social Science'
        return 'General'
    
    df['thematic_category'] = df['subreddit'].apply(get_category)
    
    # Define strata
    strata = df.groupby(['thematic_category', 'thread_type']).size().reset_index(name='count')
    
    sampled_indices = []
    remaining_df = df.copy()
    
    # Step 1: Try to sample min_per_stratum from each stratum
    for _, row in strata.iterrows():
        cat, type_ = row['thematic_category'], row['thread_type']
        count = row['count']
        
        stratum_df = remaining_df[(remaining_df['thematic_category'] == cat) & 
                                  (remaining_df['thread_type'] == type_)]
        
        if len(stratum_df) >= min_per_stratum:
            # Sample exactly min_per_stratum
            sampled = stratum_df.sample(n=min_per_stratum, random_state=42)
            sampled_indices.extend(sampled.index.tolist())
            remaining_df = remaining_df.drop(sampled.index)
        else:
            # Take all available
            sampled_indices.extend(stratum_df.index.tolist())
            remaining_df = remaining_df.drop(stratum_df.index)
    
    current_count = len(sampled_indices)
    
    # Step 2: If we have enough, return
    if current_count >= target_n:
        logger.info(f"Sampling complete with {current_count} samples from initial strata.")
        return df.loc[sampled_indices]
    
    # Step 3: Merge within category if needed
    # We need (target_n - current_count) more samples
    needed = target_n - current_count
    
    # Group by category and try to fill
    categories = ['Social Science', 'General']
    for cat in categories:
        cat_df = remaining_df[remaining_df['thematic_category'] == cat]
        if len(cat_df) > 0:
            take = min(len(cat_df), needed)
            sampled_cat = cat_df.sample(n=take, random_state=42)
            sampled_indices.extend(sampled_cat.index.tolist())
            remaining_df = remaining_df.drop(sampled_cat.index)
            needed -= take
            if needed <= 0:
                break
    
    # Step 4: If still not enough, merge across categories (global pool)
    if needed > 0 and not remaining_df.empty:
        take = min(len(remaining_df), needed)
        sampled_global = remaining_df.sample(n=take, random_state=42)
        sampled_indices.extend(sampled_global.index.tolist())
        needed -= take
    
    if needed > 0:
        log_abort_condition(f"Could not reach target sample size. Needed {target_n}, got {len(sampled_indices)}.")
        # We proceed with what we have, but log the issue
        logger.warning(f"Sampling incomplete. Returning {len(sampled_indices)} samples.")
    
    logger.info(f"Final sample size: {len(sampled_indices)}")
    return df.loc[sampled_indices]

def save_results(df: pd.DataFrame, output_path: str, validation_sample: pd.DataFrame = None):
    """
    Save the scored dataset and validation sample.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    df.to_csv(output_path, index=False)
    
    if validation_sample is not None:
        val_path = output.parent / "validation_sample.csv"
        validation_sample.to_csv(val_path, index=False)
        logger.info(f"Saved validation sample to {val_path}")

def main():
    """
    Main execution flow for scoring and validation sampling.
    """
    input_path = PROJECT_ROOT / "data" / "processed" / "anonymized.csv"
    output_path = PROJECT_ROOT / "data" / "processed" / "scored.csv"
    
    if not input_path.exists():
        log_abort_condition(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        # Load data
        df = load_data(str(input_path))
        
        # Score sentiment
        df = score_sentiment(df)
        
        # Count prosocial actions
        df = count_prosocial_actions(df)
        
        # Stratified sampling for validation
        validation_sample = stratified_sampling_validation(df)
        
        # Save results
        save_results(df, str(output_path), validation_sample)
        
        logger.info("Scoring and validation sampling completed successfully.")
        
    except Exception as e:
        log_abort_condition(f"Error during scoring: {str(e)}")
        raise

if __name__ == "__main__":
    main()
