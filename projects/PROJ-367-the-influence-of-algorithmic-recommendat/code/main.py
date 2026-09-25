"""
Main orchestration script for the Influence of Algorithmic Recommendations Analysis.

This script implements the full pipeline for User Story 1:
1. Load real verified dataset from T015
2. Validate schema (T047)
3. Merge similar categories (T040)
4. Compute diversity scores (T018)
5. Perform sensitivity analysis (T041)
6. Output results to data/processed/
"""

import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from project modules
from config import ProjectConfig, setup_logging
from ingestion import DataSchemaError, validate_schema, load_project_data, ingest_and_save
from merger import merge_similar_categories, load_embedding_model
from metrics import calculate_diversity_score
from sensitivity import run_analysis_for_threshold, main as sensitivity_main
from robustness import sensitivity_analysis_thresholds

# Set up logging
logger = setup_logging("main_orchestration")

def load_and_validate_data(config: ProjectConfig) -> Any:
    """Load and validate the real dataset."""
    logger.info("Loading real verified dataset...")
    
    data_path = config.data_raw_dir / "verified_dataset.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Verified dataset not found at {data_path}. Run T015 first.")
    
    df = load_project_data(data_path)
    logger.info(f"Loaded dataset with {len(df)} rows")
    
    # Validate schema
    logger.info("Validating schema...")
    validate_schema(df)
    logger.info("Schema validation passed")
    
    return df

def merge_categories(df: Any, config: ProjectConfig, threshold: float = 0.7) -> Any:
    """Merge similar categories based on semantic similarity."""
    logger.info("Merging similar categories...")
    
    # Load embedding model
    model = load_embedding_model(config.embedding_model_name)
    
    # Perform merging
    df_merged = merge_similar_categories(df, model, threshold=threshold)
    logger.info(f"Merged categories with threshold {threshold}")
    
    return df_merged

def compute_diversity_scores(df: Any, config: ProjectConfig) -> List[Dict[str, Any]]:
    """Compute Shannon entropy-based diversity scores."""
    logger.info("Computing diversity scores...")
    
    results = []
    for _, row in df.iterrows():
        rec_categories = row.get('recommended_categories', [])
        enr_categories = row.get('enrolled_categories', [])
        
        # Handle empty enrollments
        if not enr_categories:
            learner_score = None
            logger.warning(f"Empty enrollments for user {row.get('user_id')}, session {row.get('session_id')}")
        else:
            learner_score = calculate_diversity_score(enr_categories)
        
        rec_score = calculate_diversity_score(rec_categories)
        
        results.append({
            'user_id': str(row.get('user_id', '')),
            'session_id': str(row.get('session_id', '')),
            'recommendation_diversity_score': float(rec_score) if rec_score is not None else None,
            'learner_diversity_score': float(learner_score) if learner_score is not None else None
        })
    
    logger.info(f"Computed diversity scores for {len(results)} sessions")
    return results

def run_sensitivity_analysis(df: Any, config: ProjectConfig) -> Any:
    """Run sensitivity analysis over multiple thresholds."""
    logger.info("Running sensitivity analysis...")
    
    # Define thresholds to sweep
    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    results = []
    
    for threshold in thresholds:
        logger.info(f"Running analysis for threshold {threshold}")
        
        # Merge categories
        df_merged = merge_categories(df, config, threshold=threshold)
        
        # Compute diversity scores
        scores = compute_diversity_scores(df_merged, config)
        
        # Run modeling to get coefficient and p-value
        # Note: This is a simplified version - in full implementation,
        # we would fit the weighted regression model here
        try:
            from modeling import fit_weighted_regression
            # Prepare data for regression
            rec_scores = [s['recommendation_diversity_score'] for s in scores if s['recommendation_diversity_score'] is not None]
            learner_scores = [s['learner_diversity_score'] for s in scores if s['learner_diversity_score'] is not None]
            
            if len(rec_scores) > 10 and len(learner_scores) > 10:
                # Create a simple DataFrame for regression
                import pandas as pd
                reg_df = pd.DataFrame({
                    'rec_score': rec_scores[:len(learner_scores)],
                    'learner_score': learner_scores
                })
                
                result = fit_weighted_regression(reg_df, 'learner_score', 'rec_score')
                coeff = result.coefficient
                pval = result.p_value
            else:
                coeff = None
                pval = None
        except Exception as e:
            logger.warning(f"Modeling failed for threshold {threshold}: {e}")
            coeff = None
            pval = None
        
        results.append({
            'threshold': threshold,
            'coefficient': coeff,
            'p_value': pval
        })
    
    logger.info(f"Sensitivity analysis complete for {len(results)} thresholds")
    return results

def save_results(config: ProjectConfig, diversity_scores: List[Dict], sensitivity_results: List[Dict]):
    """Save results to output files."""
    logger.info("Saving results...")
    
    # Ensure output directory exists
    config.data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Save diversity scores as JSON
    diversity_path = config.data_processed_dir / "diversity_scores.json"
    with open(diversity_path, 'w') as f:
        json.dump(diversity_scores, f, indent=2)
    logger.info(f"Saved diversity scores to {diversity_path}")
    
    # Save sensitivity analysis as CSV
    import pandas as pd
    sensitivity_df = pd.DataFrame(sensitivity_results)
    sensitivity_path = config.data_processed_dir / "sensitivity_analysis.csv"
    sensitivity_df.to_csv(sensitivity_path, index=False)
    logger.info(f"Saved sensitivity analysis to {sensitivity_path}")

def main():
    """Main orchestration function."""
    start_time = time.time()
    
    # Load configuration
    config = ProjectConfig()
    logger.info(f"Starting pipeline with config: {config.project_root}")
    
    try:
        # Step 1: Load and validate data
        df = load_and_validate_data(config)
        
        # Step 2: Merge categories (using default threshold for main run)
        df_merged = merge_categories(df, config, threshold=0.7)
        
        # Step 3: Compute diversity scores
        diversity_scores = compute_diversity_scores(df_merged, config)
        
        # Step 4: Run sensitivity analysis
        sensitivity_results = run_sensitivity_analysis(df, config)
        
        # Step 5: Save results
        save_results(config, diversity_scores, sensitivity_results)
        
        # Log runtime
        end_time = time.time()
        duration = end_time - start_time
        
        runtime_log = {
            'start': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(start_time)),
            'end': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(end_time)),
            'duration_seconds': duration,
            'status': 'success'
        }
        
        runtime_log_path = config.data_processed_dir / "runtime_log.json"
        with open(runtime_log_path, 'w') as f:
            json.dump(runtime_log, f, indent=2)
        
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
        return 0
        
    except DataSchemaError as e:
        logger.error(f"Schema validation failed: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())