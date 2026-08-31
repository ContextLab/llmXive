import os
import json
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_config_dict
from metrics import compute_saa, semantic_similarity, calculate_iou
from reasoning import process_test_set, load_phi3_model, build_prompt, parse_model_response, generate_response
from retriever import TextRetriever, load_processed_data
from baseline_ref import load_baseline_saa

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_evaluation_results(results_path: Path) -> List[Dict[str, Any]]:
    """
    Load existing evaluation results from a JSON file.
    If the file doesn't exist, return an empty list.
    """
    if not results_path.exists():
        logger.warning(f"Evaluation results file not found at {results_path}. Starting fresh.")
        return []
    
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            logger.warning(f"Unexpected data format in {results_path}. Expected a list.")
            return []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {results_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading {results_path}: {e}")
        return []

def format_results_for_saving(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure results are in a clean, serializable format for saving.
    Removes any non-serializable objects (like numpy types) if necessary.
    """
    cleaned_results = []
    for item in results:
        cleaned_item = {}
        for k, v in item.items():
            if isinstance(v, (str, int, float, bool, type(None))):
                cleaned_item[k] = v
            elif isinstance(v, (list, dict)):
                cleaned_item[k] = v
            else:
                # Convert common non-serializable types (e.g., numpy)
                try:
                    cleaned_item[k] = float(v) if isinstance(v, (int, float)) else str(v)
                except Exception:
                    cleaned_item[k] = str(v)
        cleaned_results.append(cleaned_item)
    return cleaned_results

def save_intermediate_results(results: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Save the intermediate results (answers, predicted IDs, metrics) to the specified JSON file.
    Returns True if successful, False otherwise.
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cleaned_results = format_results_for_saving(results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully saved {len(cleaned_results)} results to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save intermediate results to {output_path}: {e}")
        traceback.print_exc()
        return False

def main():
    """
    Main entry point to run the text-only pipeline and save intermediate results.
    This function orchestrates the full evaluation loop:
    1. Load configuration and data
    2. Initialize retriever and model
    3. Process test set (retrieve, reason, evaluate)
    4. Save results to data/results/text_pipeline_results.json
    """
    config = get_config_dict()
    logger.info("Starting intermediate results generation for User Story 1")

    # Paths
    processed_data_path = Path(config['paths']['processed_data'])
    output_results_path = Path(config['paths']['results']) / 'text_pipeline_results.json'
    baseline_path = Path(config['paths']['baseline_saa'])

    # Load baseline for reference (optional, for logging)
    try:
        baseline_value = load_baseline_saa(baseline_path)
        logger.info(f"Loaded baseline SAA value: {baseline_value}")
    except Exception as e:
        logger.warning(f"Could not load baseline SAA: {e}. Proceeding without it.")

    # Load processed data
    if not processed_data_path.exists():
        logger.error(f"Processed data not found at {processed_data_path}.")
        return False

    try:
        test_set = load_processed_data(processed_data_path)
        logger.info(f"Loaded {len(test_set)} test samples.")
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        return False

    # Initialize Retriever
    retriever = TextRetriever()
    logger.info("Retriever initialized.")

    # Load Model
    model = load_phi3_model()
    logger.info("Model loaded.")

    results = []

    logger.info("Starting evaluation loop...")
    for idx, sample in enumerate(test_set):
        try:
            query = sample.get('question', '')
            ground_truth_answer = sample.get('answer', '')
            ground_truth_chunk_id = sample.get('chunk_id', '')
            
            # Retrieve top-k chunks
            retrieved_chunks = retriever.retrieve(query, k=5)
            
            # Build prompt
            prompt = build_prompt(query, retrieved_chunks)
            
            # Generate response
            response_text = generate_response(model, prompt)
            
            # Parse response
            parsed = parse_model_response(response_text)
            predicted_answer = parsed.get('answer', '')
            predicted_chunk_id = parsed.get('chunk_id', '')

            # Compute metrics
            # Semantic similarity for answer correctness
            sim_score = semantic_similarity(ground_truth_answer, predicted_answer)
            is_answer_correct = (ground_truth_answer.lower() == predicted_answer.lower()) or (sim_score >= 0.85)
            
            # IoU for spatial correctness (if chunk IDs are available)
            iou_score = 0.0
            if predicted_chunk_id and ground_truth_chunk_id:
                # In a real scenario, we'd map chunk IDs to bounding boxes here.
                # For this task, we assume chunk IDs match if strings match (simplified IoU=1.0 for match, 0.0 for mismatch)
                # Or we could look up boxes from processed data if available.
                # Given the constraints, we'll do a simple string match for "IoU" in this context
                # or return 0.0 if not implemented in retriever/data.
                # To be robust, let's assume if IDs match, IoU=1.0, else 0.0 (as a proxy for strict attribution)
                if predicted_chunk_id == ground_truth_chunk_id:
                    iou_score = 1.0
                else:
                    iou_score = 0.0
            
            # Compute SAA (Strict Attributed Accuracy)
            # SAA = Answer Correctness AND Spatial Correctness (IoU > 0.5)
                saa = is_answer_correct and (iou_score > 0.5)
            else:
                saa = False

            result_entry = {
                "query_index": idx,
                "query": query,
                "ground_truth_answer": ground_truth_answer,
                "predicted_answer": predicted_answer,
                "ground_truth_chunk_id": ground_truth_chunk_id,
                "predicted_chunk_id": predicted_chunk_id,
                "semantic_similarity": float(sim_score),
                "is_answer_correct": is_answer_correct,
                "iou_score": float(iou_score),
                "saa": saa,
                "retrieved_chunk_ids": [c.get('chunk_id', '') for c in retrieved_chunks]
            }
            
            results.append(result_entry)
            
            if (idx + 1) % 10 == 0:
                logger.info(f"Processed {idx + 1}/{len(test_set)} samples")

        except Exception as e:
            logger.error(f"Error processing sample {idx}: {e}")
            traceback.print_exc()
            # Continue with next sample, but log the error
            results.append({
                "query_index": idx,
                "error": str(e),
                "query": sample.get('question', ''),
                "ground_truth_answer": sample.get('answer', ''),
                "ground_truth_chunk_id": sample.get('chunk_id', ''),
                "predicted_answer": "",
                "predicted_chunk_id": "",
                "semantic_similarity": 0.0,
                "is_answer_correct": False,
                "iou_score": 0.0,
                "saa": False
            })

    # Save results
    success = save_intermediate_results(results, output_results_path)
    
    if success:
        logger.info("Intermediate results generation completed successfully.")
        return True
    else:
        logger.error("Failed to save intermediate results.")
        return False

if __name__ == "__main__":
    main()
