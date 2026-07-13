import os
import json
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from config import get_config_dict
from retriever import TextRetriever, load_processed_data
from reasoning import process_test_set, generate_response, load_phi3_model, build_prompt, parse_model_response
from metrics import compute_saa, calculate_iou, semantic_similarity
from logging_utils import (
    setup_query_logger,
    get_memory_usage_mb,
    log_query_execution,
    log_batch_summary,
    profile_and_log_query
)

def load_test_set() -> List[Dict[str, Any]]:
    """
    Loads the held-out test set from processed data.
    Expected path: data/processed/test_set.json
    """
    config = get_config_dict()
    processed_dir = Path(config['paths']['processed'])
    test_file = processed_dir / "test_set.json"
    
    if not test_file.exists():
        raise FileNotFoundError(f"Test set not found at {test_file}. "
                              "Run data fetching pipeline first.")
    
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    return test_data

def run_evaluation_loop(
    test_set: List[Dict[str, Any]],
    retriever: TextRetriever,
    model,
    max_queries: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Runs the evaluation loop on the test set with detailed logging.
    
    Args:
        test_set: List of test queries
        retriever: Initialized TextRetriever instance
        model: Loaded Phi-3 model instance
        max_queries: Optional limit on number of queries to process
    
    Returns:
        List of result dictionaries with metrics and logs
    """
    logger = setup_query_logger()
    results = []
    memory_snapshots = []
    
    successful_count = 0
    failed_count = 0
    durations = []
    
    queries_to_process = test_set[:max_queries] if max_queries else test_set
    
    logger.info(f"Starting evaluation on {len(queries_to_process)} queries")
    
    for idx, query_data in enumerate(queries_to_process):
        query_id = query_data.get('query_id', f"query_{idx}")
        query_text = query_data.get('query', '')
        ground_truth = query_data.get('ground_truth', {})
        
        try:
            # Profile memory at start
            memory_start = get_memory_usage_mb()
            start_time = time.time()
            
            # Retrieve relevant chunks
            retrieved_chunks = retriever.retrieve(query_text, top_k=3)
            
            # Build prompt and generate response
            prompt = build_prompt(query_text, retrieved_chunks)
            response_text = generate_response(model, prompt)
            
            # Parse response
            parsed_response = parse_model_response(response_text)
            predicted_answer = parsed_response.get('answer', '')
            predicted_chunk_id = parsed_response.get('chunk_id', '')
            
            # Calculate metrics
            if 'answer' in ground_truth:
                exact_match = (predicted_answer.strip().lower() == 
                             ground_truth['answer'].strip().lower())
                semantic_sim = semantic_similarity(predicted_answer, ground_truth['answer'])
                answer_correct = exact_match or semantic_sim >= 0.85
            else:
                answer_correct = False
                
            if 'chunk_id' in ground_truth and 'bbox' in ground_truth:
                # Calculate IoU if we have bounding box info
                if predicted_chunk_id == ground_truth['chunk_id']:
                    iou = 1.0  # Simplified: exact match = perfect IoU for this task
                else:
                    iou = 0.0
                    # In a full implementation, we would calculate actual IoU
                    # based on predicted vs ground truth bounding boxes
            else:
                iou = 0.0
                
            # Compute SAA
            saa = compute_saa(answer_correct, iou > 0.5)
            
            # Profile memory at end
            end_time = time.time()
            memory_end = get_memory_usage_mb()
            duration = end_time - start_time
            
            # Log query execution
            log_entry = log_query_execution(
                query_id=query_id,
                duration_seconds=duration,
                memory_start_mb=memory_start,
                memory_end_mb=memory_end,
                status="success",
                logger=logger
            )
            
            result = {
                'query_id': query_id,
                'query': query_text,
                'predicted_answer': predicted_answer,
                'predicted_chunk_id': predicted_chunk_id,
                'ground_truth_answer': ground_truth.get('answer', ''),
                'ground_truth_chunk_id': ground_truth.get('chunk_id', ''),
                'answer_correct': answer_correct,
                'spatial_correct': iou > 0.5,
                'saa': saa,
                'iou': iou,
                'semantic_similarity': semantic_similarity(predicted_answer, ground_truth.get('answer', '')) if 'answer' in ground_truth else 0.0,
                'duration_seconds': round(duration, 4),
                'memory_start_mb': round(memory_start, 2),
                'memory_end_mb': round(memory_end, 2),
                'memory_delta_mb': round(memory_end - memory_start, 2),
                'status': 'success'
            }
            
            results.append(result)
            memory_snapshots.append(memory_end)
            durations.append(duration)
            successful_count += 1
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            memory_end = get_memory_usage_mb()
            
            log_entry = log_query_execution(
                query_id=query_id,
                duration_seconds=duration,
                memory_start_mb=memory_start if 'memory_start' in locals() else 0,
                memory_end_mb=memory_end,
                status="failure",
                error_msg=str(e),
                logger=logger
            )
            
            result = {
                'query_id': query_id,
                'status': 'failure',
                'error': str(e),
                'duration_seconds': round(duration, 4),
                'memory_end_mb': round(memory_end, 2)
            }
            
            results.append(result)
            failed_count += 1
            traceback.print_exc()
    
    # Log batch summary
    avg_duration = sum(durations) / len(durations) if durations else 0
    avg_mem_start = sum(r.get('memory_start_mb', 0) for r in results if r.get('status') == 'success') / successful_count if successful_count else 0
    avg_mem_end = sum(r.get('memory_end_mb', 0) for r in results if r.get('status') == 'success') / successful_count if successful_count else 0
    max_mem = max(memory_snapshots) if memory_snapshots else 0
    
    log_batch_summary(
        total_queries=len(queries_to_process),
        successful_queries=successful_count,
        failed_queries=failed_count,
        avg_duration=avg_duration,
        avg_memory_start=avg_mem_start,
        avg_memory_end=avg_mem_end,
        max_memory_observed=max_mem,
        logger=logger
    )
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Saves evaluation results to JSON file.
    """
    if output_path is None:
        config = get_config_dict()
        results_dir = Path(config['paths']['results'])
        output_path = results_dir / "text_pipeline_results.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {output_path}")

def main():
    """
    Main entry point for the text-only evaluation pipeline.
    """
    config = get_config_dict()
    
    # Initialize logger
    logger = setup_query_logger()
    logger.info("Starting Text-Only Evaluation Pipeline")
    
    try:
        # Load test set
        test_set = load_test_set()
        logger.info(f"Loaded {len(test_set)} test queries")
        
        # Initialize retriever
        retriever = TextRetriever(model_name='all-MiniLM-L6-v2')
        logger.info("Initialized retriever")
        
        # Load model
        model = load_phi3_model()
        logger.info("Loaded Phi-3 model")
        
        # Run evaluation
        results = run_evaluation_loop(test_set, retriever, model)
        
        # Save results
        save_results(results)
        
        logger.info("Evaluation complete")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
