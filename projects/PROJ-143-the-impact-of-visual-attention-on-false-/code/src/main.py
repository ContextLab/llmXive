"""
Main orchestration script for the Visual Attention on False Memory study.

This script runs the end-to-end pipeline for User Story 1:
1. Compute saliency scores for Visual Genome images (T014)
2. Pre-filter false memory candidates (T015)
3. Run human consensus workflow (T015a)
4. Calculate correlation and mixed-effects regression (T016)

Output:
    data/processed/correlation_results.json
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_config, StudyConfig
from src.data.preprocessing import load_linked_data, filter_false_memory_candidates, save_candidates
from src.analysis.saliency import process_visual_genome_dataset
from src.utils.consensus import run_consensus_workflow
from src.utils.validation import run_validation_workflow
from src.analysis.metrics import run_mixed_effects_logistic_regression, pearson_correlation_with_ci, load_and_prepare_data
from src.utils.logging import log_study_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'main_orchestration.log')
    ]
)
logger = logging.getLogger(__name__)


def run_saliency_pipeline(config: StudyConfig) -> Dict[str, Any]:
    """
    Run saliency map computation for Visual Genome images.
    
    Returns:
        Dict containing path to saliency scores file and status.
    """
    logger.info("Starting saliency computation pipeline...")
    
    try:
        # Process Visual Genome dataset to get saliency scores
        saliency_result = process_visual_genome_dataset(
            vg_images_path=config.paths.vg_images,
            vg_annotations_path=config.paths.vg_annotations,
            output_path=config.paths.saliency_scores
        )
        
        logger.info(f"Saliency computation completed. Output: {config.paths.saliency_scores}")
        return {
            "status": "success",
            "output_path": str(config.paths.saliency_scores),
            "details": saliency_result
        }
    except Exception as e:
        logger.error(f"Saliency pipeline failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


def run_false_memory_preprocessing(config: StudyConfig) -> Dict[str, Any]:
    """
    Run false memory candidate filtering.
    
    Returns:
        Dict containing path to candidate file and status.
    """
    logger.info("Starting false memory pre-filtering...")
    
    try:
        # Load linked data from T010
        linked_data = load_linked_data(config.paths.linked_data)
        
        if not linked_data:
            logger.warning("No linked data found. Skipping preprocessing.")
            return {
                "status": "skipped",
                "reason": "No linked data available"
            }
        
        # Filter candidates
        candidates = filter_false_memory_candidates(linked_data)
        
        # Save candidates
        save_candidates(candidates, config.paths.candidate_false_memories)
        
        logger.info(f"Preprocessing completed. Output: {config.paths.candidate_false_memories}")
        return {
            "status": "success",
            "output_path": str(config.paths.candidate_false_memories),
            "candidate_count": len(candidates)
        }
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


def run_consensus_workflow(config: StudyConfig) -> Dict[str, Any]:
    """
    Run human consensus workflow for candidate verification.
    
    Returns:
        Dict containing path to verification results and status.
    """
    logger.info("Starting human consensus workflow...")
    
    try:
        results = run_consensus_workflow(
            input_path=config.paths.candidate_false_memories,
            output_path=config.paths.human_verification_results
        )
        
        logger.info(f"Consensus workflow completed. Output: {config.paths.human_verification_results}")
        return {
            "status": "success",
            "output_path": str(config.paths.human_verification_results),
            "details": results
        }
    except Exception as e:
        logger.error(f"Consensus workflow failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


def run_validation_workflow(config: StudyConfig) -> Dict[str, Any]:
    """
    Run validation to check for inconclusive flags.
    
    Returns:
        Dict containing validation status and flag.
    """
    logger.info("Starting validation workflow...")
    
    try:
        status = run_validation_workflow(
            input_path=config.paths.human_verification_results,
            output_path=config.paths.validation_status
        )
        
        logger.info(f"Validation completed. Output: {config.paths.validation_status}")
        return {
            "status": "success",
            "output_path": str(config.paths.validation_status),
            "details": status
        }
    except Exception as e:
        logger.error(f"Validation workflow failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


def run_correlation_analysis(config: StudyConfig) -> Dict[str, Any]:
    """
    Run correlation and mixed-effects regression analysis.
    
    Returns:
        Dict containing path to correlation results and status.
    """
    logger.info("Starting correlation analysis...")
    
    try:
        # Load and prepare data from consensus results and saliency scores
        data = load_and_prepare_data(
            verification_path=config.paths.human_verification_results,
            saliency_path=config.paths.saliency_scores
        )
        
        if not data or len(data) == 0:
            logger.warning("No data available for correlation analysis.")
            return {
                "status": "skipped",
                "reason": "No valid data found"
            }
        
        # Calculate Pearson correlation
        correlation_result = pearson_correlation_with_ci(
            x=data['saliency_scores'],
            y=data['false_memory_labels'],
            alpha=config.thresholds.alpha
        )
        
        # Run mixed-effects logistic regression
        regression_result = run_mixed_effects_logistic_regression(
            data=data,
            alpha=config.thresholds.alpha
        )
        
        # Apply Benjamini-Hochberg FDR correction if multiple tests
        if 'p_values' in regression_result:
            corrected_result = pearson_correlation_with_ci(
                x=data['saliency_scores'],
                y=data['false_memory_labels'],
                alpha=config.thresholds.alpha
            )
            # Note: Full FDR implementation would go here for multiple comparisons
        
        # Compile results
        results = {
            "pearson_correlation": correlation_result,
            "mixed_effects_regression": regression_result,
            "sample_size": len(data),
            "analysis_timestamp": config.analysis_timestamp
        }
        
        # Save results
        output_path = Path(config.paths.correlation_results)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Correlation analysis completed. Output: {output_path}")
        return {
            "status": "success",
            "output_path": str(output_path),
            "correlation_r": correlation_result.get('r'),
            "p_value": correlation_result.get('p_value')
        }
    except Exception as e:
        logger.error(f"Correlation analysis failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


def main():
    """
    Main orchestration function to run the complete pipeline.
    """
    logger.info("=== Starting Visual Attention False Memory Study Pipeline ===")
    
    # Load configuration
    config = get_config()
    
    # Initialize study status log
    log_study_status("pipeline_started", config.paths.study_status)
    
    # Define pipeline steps
    pipeline_steps = [
        ("Saliency Computation", run_saliency_pipeline),
        ("False Memory Preprocessing", run_false_memory_preprocessing),
        ("Human Consensus Workflow", run_consensus_workflow),
        ("Validation Workflow", run_validation_workflow),
        ("Correlation Analysis", run_correlation_analysis)
    ]
    
    overall_status = "success"
    step_results = {}
    
    # Execute pipeline steps
    for step_name, step_func in pipeline_steps:
        logger.info(f"\n--- Executing: {step_name} ---")
        try:
            result = step_func(config)
            step_results[step_name] = result
            
            if result.get("status") == "failed":
                logger.error(f"{step_name} failed: {result.get('error', 'Unknown error')}")
                overall_status = "failed"
                break
            elif result.get("status") == "skipped":
                logger.warning(f"{step_name} skipped: {result.get('reason', 'Unknown reason')}")
                
        except Exception as e:
            logger.error(f"{step_name} threw exception: {str(e)}")
            step_results[step_name] = {"status": "failed", "error": str(e)}
            overall_status = "failed"
            break
    
    # Finalize study status
    log_study_status(overall_status, config.paths.study_status)
    
    # Log summary
    logger.info("\n=== Pipeline Execution Summary ===")
    logger.info(f"Overall Status: {overall_status}")
    for step_name, result in step_results.items():
        logger.info(f"{step_name}: {result.get('status')}")
    
    if overall_status == "success":
        logger.info(f"Pipeline completed successfully. Results saved to: {config.paths.correlation_results}")
    else:
        logger.error("Pipeline failed. Check logs for details.")
    
    return 0 if overall_status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())