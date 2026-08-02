import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.lib.config import ensure_directories
from src.lib.data_loader import load_dataset, validate_dataset
from src.lib.tool_mapper import load_tool_mapping, get_tool_descriptions, get_all_problem_ids
from src.services.retrieval_service import create_retrieval_service, retrieve_top_tools
from src.models.divergence_model import get_model_and_tokenizer, process_problem, DivergenceResult
from src.lib.resource_tracker import enforce_limits, TimeoutExceededError, MemoryLimitExceededError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DiagnosticError(Exception):
    """Custom exception for diagnostic errors."""
    pass

def load_and_validate_data(dataset_path: str) -> List[Dict[str, Any]]:
    """
    Load and validate the dataset.
    
    Args:
        dataset_path: Path to the dataset file.
        
    Returns:
        List of validated records.
    """
    logger.info(f"Loading dataset from {dataset_path}...")
    data = load_dataset(dataset_path)
    validate_dataset(data)
    logger.info(f"Loaded and validated {len(data)} records")
    return data

def run_retrieval_and_scoring(
    data: List[Dict[str, Any]],
    tool_descriptions: List[str],
    problem_ids: List[str],
    tokenizer,
    model
) -> List[DivergenceResult]:
    """
    Run retrieval and scoring for all problems.
    
    Args:
        data: List of problem records.
        tool_descriptions: List of all tool descriptions.
        problem_ids: List of all problem IDs.
        tokenizer: DistilBertTokenizer.
        model: DistilBertModel.
        
    Returns:
        List of DivergenceResult objects.
    """
    retrieval_service = create_retrieval_service(tool_descriptions, problem_ids)
    results = []
    
    for record in data:
        problem_id = record.get('problem_id')
        thinking_prefix = record.get('thinking_prefix')
        
        if not thinking_prefix:
            logger.warning(f"Skipping problem {problem_id}: missing thinking_prefix")
            continue
        
        # Retrieve top tools
        retrieved_ids, scores, embedding_dim = retrieval_service.retrieve_top_tools(thinking_prefix, top_k=5)
        
        if not retrieved_ids:
            logger.warning(f"No tools retrieved for problem {problem_id}. Setting divergence to 1.0.")
            # Handle zero-retrieval: return zero vector for centroid, similarity=0, divergence=1.0
            tool_embeddings = [np.zeros(768) for _ in range(1)] # Dummy to trigger zero centroid
            retrieval_stats = {
                "num_tools_retrieved": 0,
                "embedding_dimension": embedding_dim,
                "status": "no_tools_retrieved"
            }
            # Manually construct result for zero-retrieval case
            result = DivergenceResult(
                problem_id=problem_id,
                thinking_embedding=np.zeros(768).tolist(),
                tool_centroid_embedding=np.zeros(768).tolist(),
                cosine_similarity=0.0,
                semantic_divergence_score=1.0,
                retrieval_stats=retrieval_stats
            )
            results.append(result)
            continue
        
        # Get embeddings for retrieved tools
        tool_embeddings = []
        for tid in retrieved_ids:
            # Find the description for this tool ID
            # Note: In a real scenario, we'd map ID -> Description more efficiently
            # For now, we assume tool_descriptions and problem_ids are aligned and we need to find the index
            try:
                idx = problem_ids.index(tid)
                desc = tool_descriptions[idx]
                emb = process_problem.__globals__['encode_text'](desc, tokenizer, model) # Accessing helper
                tool_embeddings.append(emb)
            except ValueError:
                logger.warning(f"Tool ID {tid} not found in problem_ids list")
                continue
        
        if not tool_embeddings:
            logger.warning(f"No valid tool embeddings for problem {problem_id}")
            continue
        
        retrieval_stats = {
            "num_tools_retrieved": len(retrieved_ids),
            "embedding_dimension": embedding_dim,
            "status": "success"
        }
        
        result = process_problem(problem_id, thinking_prefix, tool_embeddings, retrieval_stats, tokenizer, model)
        results.append(result)
        
        # Log retrieval stats and embedding dimensions
        logger.info(
            f"Problem {problem_id}: "
            f"retrieved {retrieval_stats['num_tools_retrieved']} tools, "
            f"embedding dimension = {retrieval_stats['embedding_dimension']}"
        )
    
    return results

def save_results(results: List[DivergenceResult], output_path: str):
    """
    Save results to a JSON file.
    
    Args:
        results: List of DivergenceResult objects.
        output_path: Path to output file.
    """
    logger.info(f"Saving results to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    
    logger.info(f"Saved {len(results)} results")

def run_diagnostic(dataset_path: str, output_path: str):
    """
    Main entry point for the diagnostic pipeline.
    
    Args:
        dataset_path: Path to input dataset.
        output_path: Path to output results.
    """
    logger.info("Starting Semantic Divergence Diagnostic...")
    
    try:
        # Enforce limits
        with enforce_limits(timeout_seconds=300, memory_gb=7):
            # Load data
            data = load_and_validate_data(dataset_path)
            
            # Load tool mapping
            tool_mapping_path = "data/tool_mappings/mathvista_tool_map.json"
            tool_map = load_tool_mapping(tool_mapping_path)
            tool_descriptions = get_tool_descriptions(tool_map)
            problem_ids = get_all_problem_ids(tool_map)
            
            # Load model
            tokenizer, model = get_model_and_tokenizer()
            
            # Run retrieval and scoring
            results = run_retrieval_and_scoring(data, tool_descriptions, problem_ids, tokenizer, model)
            
            # Save results
            save_results(results, output_path)
            
        logger.info("Diagnostic completed successfully.")
        
    except TimeoutExceededError:
        logger.error("Diagnostic timed out.")
        raise
    except MemoryLimitExceededError:
        logger.error("Diagnostic exceeded memory limit.")
        raise
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        raise

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Semantic Divergence Diagnostic")
    parser.add_argument("--dataset", required=True, help="Path to dataset JSON")
    parser.add_argument("--output", required=True, help="Path to output JSON")
    args = parser.parse_args()
    
    run_diagnostic(args.dataset, args.output)

if __name__ == "__main__":
    main()
