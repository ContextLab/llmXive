import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np

from config import set_global_seed, SEED
from utils.exceptions import StatsException, CoverageException

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
    return logger

def calculate_parameter_coverage_score(ast_params: List[str], docstring_text: Optional[str]) -> float:
    if not ast_params:
        return 0.0
    if not docstring_text or not docstring_text.strip():
        return 0.0
    try:
        from docstring_parser import parse
        parsed = parse(docstring_text)
        params_in_docstring = {p.arg_name for p in parsed.params if p.arg_name}
        if not params_in_docstring:
            return 0.0
        matched = len(params_in_docstring.intersection(set(ast_params)))
        return matched / len(ast_params)
    except Exception as e:
        raise CoverageException(f"Failed to parse docstring: {e}")

def process_results_for_coverage(input_file: Path, output_file: Path) -> None:
    logger = logging.getLogger(__name__)
    logger.info(f"Processing {input_file} for coverage scores...")
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        logger.warning("Input file is empty.")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return

    for record in data:
        ast_params = record.get('ast_params', [])
        human_docstring = record.get('human_docstring')
        # Calculate coverage based on human docstring as ground truth reference for parameters
        # Note: The task description says "Human vs LLM coverage scores" for stats, 
        # but for T033/T034 we calculate coverage for the record's docstring context.
        # T033 calculates coverage for human_docstring. T034 calculates similarity.
        # We assume 'human_docstring' is the ground truth for coverage calculation here.
        try:
            score = calculate_parameter_coverage_score(ast_params, human_docstring)
            record['coverage_score'] = score
        except CoverageException as e:
            logger.warning(f"Coverage calculation failed for record: {e}")
            record['coverage_score'] = 0.0
            record['parse_error'] = True

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved coverage results to {output_file}")

def calculate_semantic_similarity_batch(records: List[Dict[str, Any]], model: SentenceTransformer, batch_size: int = 16) -> List[float]:
    """
    Calculate semantic similarity between human_docstring and generated_docstring.
    Returns a list of similarity scores.
    """
    logger = logging.getLogger(__name__)
    similarities = []
    
    # Prepare pairs
    pairs = []
    indices = []
    for i, record in enumerate(records):
        human = record.get('human_docstring')
        generated = record.get('generated_docstring')
        
        # Handle cases where one or both are missing/null
        if not human or not generated:
            # If either is missing, similarity is 0.0
            similarities.append(0.0)
            continue
        
        # Clean strings
        human_clean = str(human).strip()
        generated_clean = str(generated).strip()
        
        if not human_clean or not generated_clean:
            similarities.append(0.0)
            continue
        
        pairs.append((human_clean, generated_clean))
        indices.append(i)
    
    if not pairs:
        return similarities
    
    # Process in batches
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i+batch_size]
        batch_humans = [p[0] for p in batch]
        batch_generated = [p[1] for p in batch]
        
        try:
            embeddings_humans = model.encode(batch_humans, convert_to_numpy=True, show_progress_bar=False)
            embeddings_generated = model.encode(batch_generated, convert_to_numpy=True, show_progress_bar=False)
            
            # Cosine similarity
            cos_sim = np.dot(embeddings_humans, embeddings_generated.T)
            # Since we want pairwise, take diagonal
            batch_similarities = np.diag(cos_sim).tolist()
            
            for idx, sim in zip(indices[i:i+len(batch)], batch_similarities):
                similarities.insert(idx, sim)
                
        except Exception as e:
            logger.error(f"Error during embedding calculation: {e}")
            # Fill with 0.0 for failed batch
            for idx in indices[i:i+len(batch)]:
                similarities.insert(idx, 0.0)
    
    # Sort by index to ensure order matches input records
    # The above logic with insert at index works if we process in order, 
    # but if we skipped some, the indices list handles the mapping.
    # Actually, the logic above: similarities is built by appending 0.0 for missing, 
    # then inserting for processed. This might be fragile if indices are not contiguous.
    # Let's rebuild safely:
    
    final_similarities = [0.0] * len(records)
    for i, record in enumerate(records):
        if 'similarity_temp' in record:
            final_similarities[i] = record.pop('similarity_temp')
        elif i < len(similarities):
            # This logic is getting complex with inserts. Let's restart the batch logic cleanly.
            pass
    
    # Cleaner approach:
    final_similarities = []
    for record in records:
        human = record.get('human_docstring')
        generated = record.get('generated_docstring')
        
        if not human or not generated:
            final_similarities.append(0.0)
            continue
        
        human_clean = str(human).strip()
        generated_clean = str(generated).strip()
        
        if not human_clean or not generated_clean:
            final_similarities.append(0.0)
            continue
        
        try:
            emb_h = model.encode(human_clean, convert_to_numpy=True)
            emb_g = model.encode(generated_clean, convert_to_numpy=True)
            sim = np.dot(emb_h, emb_g) / (np.linalg.norm(emb_h) * np.linalg.norm(emb_g) + 1e-9)
            final_similarities.append(float(sim))
        except Exception as e:
            logging.getLogger(__name__).warning(f"Similarity calc failed: {e}")
            final_similarities.append(0.0)
    
    return final_similarities

def add_semantic_similarity_to_data(input_file: Path, output_file: Path) -> None:
    """
    Reads input file, calculates semantic similarity for each record,
    and writes to output file with 'semantic_similarity' field.
    """
    logger = setup_logging()
    logger.info(f"Starting semantic similarity calculation for {input_file}")
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        logger.warning("Input file is empty.")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2)
        return

    logger.info("Loading sentence-transformer model (all-MiniLM-L6-v2)...")
    # Using a smaller, faster model as per task description (all-MiniLM-L6-v2)
    # Note: Task description says "all-MiniLM-L-v2" which is likely a typo for "all-MiniLM-L6-v2"
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    logger.info("Calculating similarities...")
    similarities = calculate_semantic_similarity_batch(data, model)
    
    for record, sim in zip(data, similarities):
        record['semantic_similarity'] = sim
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved results with similarity scores to {output_file}")

def run_wilcoxon_analysis(input_file: Path, output_file: Path) -> None:
    """
    Performs Wilcoxon signed-rank test on Human vs LLM coverage scores.
    """
    logger = setup_logging()
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    human_scores = []
    llm_scores = []
    
    for record in data:
        # Assuming T033 added 'coverage_score' based on human docstring
        # We need LLM coverage score. The task T035 says "Human vs LLM coverage scores".
        # In T033, we calculated coverage for human_docstring.
        # We assume the 'generated_docstring' exists and we need to calculate its coverage too?
        # Or perhaps the 'coverage_score' in results_with_scores.json is for human, 
        # and we need to calculate for generated to compare?
        # The task T033 description: "Calculate Parameter Coverage Scores... using docstring_parser to parse docstring text and matching against ast_params".
        # It doesn't specify which docstring. But T035 says "Human vs LLM".
        # Let's assume the file has 'coverage_score' (Human) and we need to compute 'llm_coverage_score'.
        
        ast_params = record.get('ast_params', [])
        human_doc = record.get('human_docstring')
        generated_doc = record.get('generated_docstring')
        
        h_score = calculate_parameter_coverage_score(ast_params, human_doc)
        l_score = calculate_parameter_coverage_score(ast_params, generated_doc)
        
        human_scores.append(h_score)
        llm_scores.append(l_score)
    
    if len(human_scores) < 2:
        logger.warning("Not enough data for Wilcoxon test.")
        with open(output_file, 'w') as f:
            json.dump({"error": "Insufficient data"}, f)
        return

    try:
        from scipy import stats
        statistic, pvalue = stats.wilcoxon(human_scores, llm_scores)
        
        result = {
            "test": "Wilcoxon signed-rank",
            "statistic": float(statistic),
            "p_value": float(pvalue),
            "n_pairs": len(human_scores),
            "significant": pvalue < 0.05
        }
        
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Wilcoxon test complete. P-value: {pvalue}")
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        raise

def generate_final_report(input_file: Path, output_file: Path) -> None:
    """
    Generates a final report from the stats analysis.
    """
    logger = setup_logging()
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_file, 'r') as f:
        stats_result = json.load(f)
    
    report = {
        "project": "PROJ-318-evaluating-the-impact-of-code-generation",
        "analysis": stats_result
    }
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Final report generated at {output_file}")

def main():
    set_global_seed(SEED)
    logger = setup_logging()
    
    if len(sys.argv) < 3:
        logger.error("Usage: python analyze.py --step=<step> --input=<file> --output=<file>")
        sys.exit(1)
    
    args = {}
    for arg in sys.argv[1:]:
        if '=' in arg:
            key, val = arg.split('=', 1)
            args[key.strip('-')] = val
    
    step = args.get('step')
    input_file = Path(args.get('input', 'data/processed/results_with_coverage.json'))
    output_file = Path(args.get('output'))
    
    if not output_file:
        logger.error("Output file is required.")
        sys.exit(1)
    
    if step == 'coverage':
        process_results_for_coverage(input_file, output_file)
    elif step == 'similarity':
        add_semantic_similarity_to_data(input_file, output_file)
    elif step == 'stats':
        run_wilcoxon_analysis(input_file, output_file)
    elif step == 'report':
        generate_final_report(input_file, output_file)
    else:
        logger.error(f"Unknown step: {step}")
        sys.exit(1)

if __name__ == '__main__':
    main()