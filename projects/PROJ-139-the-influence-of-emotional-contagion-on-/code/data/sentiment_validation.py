"""
Sentiment validation pipeline for VADER sentiment analysis.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import pandas as pd
import numpy as np
from code.config.settings import get_config
from code.data.annotate_corpus import load_extracted_data, sample_comments, get_vader_label
from code.data.calculate_reliability import load_annotations, prepare_ratings, compute_cohen_kappa, compute_cohen_kappa_aggregated, interpret_kappa, generate_report

logger = logging.getLogger(__name__)

def load_annotated_corpus() -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Load the annotated corpus from the annotations file.
    
    Returns:
        Tuple of (extracted data DataFrame, list of annotations).
    """
    config = get_config()
    annotations_path = Path(config.dataset_paths.raw) / "annotations.json"
    
    if not annotations_path.exists():
        raise FileNotFoundError(f"Annotations file not found at {annotations_path}. Run sampling pipeline first.")
    
    with open(annotations_path, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    df = load_extracted_data()
    return df, annotations

def apply_vader_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply VADER sentiment analysis to the dataset.
    
    Args:
        df: DataFrame containing comments with text.
        
    Returns:
        DataFrame with added sentiment scores.
    """
    df = df.copy()
    df['vader_label'] = df['text'].apply(get_vader_label)
    return df

def validate_vader_against_corpus(
    df: pd.DataFrame, 
    annotations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate VADER sentiment against annotated corpus.
    
    Args:
        df: DataFrame with VADER sentiment labels.
        annotations: List of annotation dictionaries with ground truth labels.
        
    Returns:
        Dictionary containing validation metrics.
    """
    # Create a mapping of comment_id to annotation label
    annotation_map = {ann['comment_id']: ann['label'] for ann in annotations}
    
    # Filter df to only include commented items
    valid_df = df[df['comment_id'].isin(annotation_map.keys())].copy()
    valid_df['ground_truth'] = valid_df['comment_id'].map(annotation_map)
    
    # Calculate agreement
    agreement = (valid_df['vader_label'] == valid_df['ground_truth']).mean()
    
    # Calculate per-class metrics
    metrics = {
        'overall_agreement': float(agreement),
        'total_samples': len(valid_df),
        'vader_positive': int((valid_df['vader_label'] == 'positive').sum()),
        'vader_negative': int((valid_df['vader_label'] == 'negative').sum()),
        'vader_neutral': int((valid_df['vader_label'] == 'neutral').sum()),
        'ground_truth_positive': int((valid_df['ground_truth'] == 'positive').sum()),
        'ground_truth_negative': int((valid_df['ground_truth'] == 'negative').sum()),
        'ground_truth_neutral': int((valid_df['ground_truth'] == 'neutral').sum()),
    }
    
    return metrics

def compute_bootstrapped_ci(
    df: pd.DataFrame, 
    annotations: List[Dict[str, Any]], 
    n_iterations: int = 1000, 
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Compute bootstrapped confidence intervals for Kappa statistic.
    
    Args:
        df: DataFrame with VADER sentiment labels.
        annotations: List of annotation dictionaries.
        n_iterations: Number of bootstrap iterations.
        confidence_level: Confidence level for intervals.
        
    Returns:
        Dictionary containing confidence interval bounds.
    """
    # Create annotation mapping
    annotation_map = {ann['comment_id']: ann['label'] for ann in annotations}
    valid_df = df[df['comment_id'].isin(annotation_map.keys())].copy()
    valid_df['ground_truth'] = valid_df['comment_id'].map(annotation_map)
    
    # Calculate Kappa for each bootstrap iteration
    kappa_values = []
    for i in range(n_iterations):
        # Sample with replacement
        sample_indices = np.random.choice(len(valid_df), size=len(valid_df), replace=True)
        sample_df = valid_df.iloc[sample_indices]
        
        # Prepare ratings for Kappa calculation
        ratings = []
        for _, row in sample_df.iterrows():
            ratings.append({
                'comment_id': row['comment_id'],
                'annotator_1': row['vader_label'],
                'annotator_2': row['ground_truth']
            })
        
        if len(ratings) < 2:
            continue
            
        kappa = compute_cohen_kappa(ratings, 'annotator_1', 'annotator_2')
        if kappa is not None:
            kappa_values.append(kappa)
    
    if not kappa_values:
        return {
            'kappa_ci_lower': 0.0,
            'kappa_ci_upper': 0.0,
            'kappa_mean': 0.0
        }
    
    # Calculate confidence intervals
    alpha = 1 - confidence_level
    ci_lower = np.percentile(kappa_values, 100 * alpha / 2)
    ci_upper = np.percentile(kappa_values, 100 * (1 - alpha / 2))
    kappa_mean = np.mean(kappa_values)
    
    return {
        'kappa_ci_lower': float(ci_lower),
        'kappa_ci_upper': float(ci_upper),
        'kappa_mean': float(kappa_mean)
    }

def generate_validation_justification(
    metrics: Dict[str, Any],
    ci_results: Dict[str, float]
) -> Dict[str, Any]:
    """
    Generate justification for validation subset validity.
    
    Args:
        metrics: Validation metrics dictionary.
        ci_results: Confidence interval results.
        
    Returns:
        Dictionary containing justification report.
    """
    report = {
        'subset_size': metrics['total_samples'],
        'overall_agreement': metrics['overall_agreement'],
        'kappa_mean': ci_results['kappa_mean'],
        'kappa_ci_lower': ci_results['kappa_ci_lower'],
        'kappa_ci_upper': ci_results['kappa_ci_upper'],
        'justification': f"Validation subset of {metrics['total_samples']} samples shows "
                        f"overall agreement of {metrics['overall_agreement']:.3f} with "
                        f"bootstrapped Kappa mean of {ci_results['kappa_mean']:.3f} "
                        f"(95% CI: [{ci_results['kappa_ci_lower']:.3f}, {ci_results['kappa_ci_upper']:.3f}]).",
        'validity_status': 'valid' if ci_results['kappa_mean'] >= 0.4 else 'questionable'
    }
    
    return report

def main():
    """
    Main function to run the sentiment validation pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    
    try:
        config = get_config()
        
        # Load annotated corpus
        df, annotations = load_annotated_corpus()
        logger.info(f"Loaded {len(annotations)} annotations")
        
        # Apply VADER sentiment
        df_with_sentiment = apply_vader_sentiment(df)
        logger.info("Applied VADER sentiment analysis")
        
        # Validate VADER against corpus
        validation_metrics = validate_vader_against_corpus(df_with_sentiment, annotations)
        logger.info(f"Validation metrics: {validation_metrics}")
        
        # Compute bootstrapped confidence intervals
        ci_results = compute_bootstrapped_ci(df_with_sentiment, annotations)
        logger.info(f"Confidence intervals: {ci_results}")
        
        # Generate validation report
        validation_report = {
            'metrics': validation_metrics,
            'kappa_statistics': ci_results
        }
        
        report_path = Path(config.dataset_paths.processed) / "vader_validation_report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(validation_report, f, indent=2)
        logger.info(f"Saved validation report to {report_path}")
        
        # Generate justification
        justification = generate_validation_justification(validation_metrics, ci_results)
        justification_path = Path(config.dataset_paths.processed) / "validation_justification.json"
        with open(justification_path, 'w', encoding='utf-8') as f:
            json.dump(justification, f, indent=2)
        logger.info(f"Saved validation justification to {justification_path}")
        
        logger.info("Sentiment validation pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Sentiment validation pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
