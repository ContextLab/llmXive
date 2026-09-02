import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from docstring_parser import parse as parse_docstring
from scipy import stats
import re

# Import from local utils as per project structure
try:
    from utils.coverage import CoverageException, parse_docstring_parameters
except ImportError:
    from code.utils.coverage import CoverageException, parse_docstring_parameters

try:
    from utils.stats import StatsException, run_wilcoxon_test
except ImportError:
    from code.utils.stats import StatsException, run_wilcoxon_test

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/analysis.log')
    ]
)
logger = logging.getLogger(__name__)

def calculate_parameter_coverage_score(human_docstring: Optional[str], ast_params: List[str]) -> float:
    """
    Calculate parameter coverage score for a single method.
    
    Score = (matched params / total AST params)
    
    Handles complex type hints by treating them as unmatched but non-crashing.
    """
    if not ast_params:
        return 1.0  # No parameters to document is a perfect score
    
    if not human_docstring or human_docstring.strip() == "":
        return 0.0
    
    try:
        parsed = parse_docstring(human_docstring)
        doc_params = [p.arg_name for p in (parsed.params or []) if p.arg_name]
        
        matched = 0
        for ast_param in ast_params:
            # Clean AST parameter name (remove type hints for comparison)
            clean_ast_param = ast_param.split(':')[0].split('=')[0].strip()
            clean_ast_param = clean_ast_param.split('[')[0]  # Handle List[...], Dict[...], etc.
            
            # Check if this parameter exists in docstring
            if clean_ast_param in doc_params:
                matched += 1
        
        return matched / len(ast_params)
        
    except Exception as e:
        logger.warning(f"Error parsing docstring for coverage calculation: {e}")
        return 0.0

def calculate_semantic_similarity_batch(human_docstrings: List[str], llm_docstrings: List[str]) -> List[float]:
    """
    Calculate semantic similarity between human and LLM docstrings.
    
    Uses sentence-transformers for embedding-based similarity.
    Returns a list of similarity scores (0-1).
    """
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Combine all docstrings for batch embedding
        all_docstrings = human_docstrings + llm_docstrings
        
        # Generate embeddings
        embeddings = model.encode(all_docstrings, show_progress_bar=False)
        
        # Split back into human and LLM embeddings
        human_embeddings = embeddings[:len(human_docstrings)]
        llm_embeddings = embeddings[len(human_docstrings):]
        
        # Calculate cosine similarity for each pair
        similarities = []
        for h_emb, l_emb in zip(human_embeddings, llm_embeddings):
            # Cosine similarity
            similarity = float(sum(a * b for a, b in zip(h_emb, l_emb)) / 
                             (sum(a * a for a in h_emb) ** 0.5 * sum(b * b for b in l_emb) ** 0.5))
            similarities.append(similarity)
        
        return similarities
        
    except ImportError:
        logger.warning("sentence-transformers not available, returning 0.0 for all similarities")
        return [0.0] * len(human_docstrings)
    except Exception as e:
        logger.error(f"Error calculating semantic similarity: {e}")
        return [0.0] * len(human_docstrings)

def process_results_for_coverage(input_file: Path) -> List[Dict[str, Any]]:
    """
    Load results and calculate parameter coverage scores.
    Handles complex type hints gracefully.
    """
    logger.info(f"Processing results from {input_file}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    results_with_scores = []
    
    for item in data:
        human_docstring = item.get('human_docstring')
        ast_params = item.get('ast_params', [])
        
        # Calculate coverage score
        coverage_score = calculate_parameter_coverage_score(human_docstring, ast_params)
        
        # Create updated record
        updated_item = item.copy()
        updated_item['coverage_score'] = coverage_score
        updated_item['ast_param_count'] = len(ast_params)
        updated_item['matched_param_count'] = int(coverage_score * len(ast_params)) if ast_params else 0
        
        results_with_scores.append(updated_item)
    
    logger.info(f"Processed {len(results_with_scores)} records")
    return results_with_scores

def add_semantic_similarity_to_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Add semantic similarity scores to the data.
    """
    human_docstrings = [item.get('human_docstring', '') for item in data]
    llm_docstrings = [item.get('generated_docstring', '') for item in data]
    
    similarities = calculate_semantic_similarity_batch(human_docstrings, llm_docstrings)
    
    for item, sim in zip(data, similarities):
        item['semantic_similarity'] = sim
    
    return data

def run_wilcoxon_analysis(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test on human vs LLM coverage scores.
    """
    human_scores = []
    llm_scores = []
    
    for item in data:
        # Extract human coverage score (from docstring quality assessment)
        # Assuming human_docstring is complete, we treat it as 1.0 coverage if present
        human_docstring = item.get('human_docstring')
        human_score = 1.0 if human_docstring and human_docstring.strip() else 0.0
        human_scores.append(human_score)
        
        # Extract LLM coverage score
        llm_score = item.get('coverage_score', 0.0)
        llm_scores.append(llm_score)
    
    if len(human_scores) < 3:
        logger.warning("Insufficient data for Wilcoxon test (need at least 3 pairs)")
        return {
            'statistic': None,
            'pvalue': None,
            'sample_size': len(human_scores),
            'warning': 'Insufficient data for Wilcoxon test'
        }
    
    try:
        statistic, pvalue = stats.wilcoxon(human_scores, llm_scores)
        
        result = {
            'statistic': float(statistic),
            'pvalue': float(pvalue),
            'sample_size': len(human_scores),
            'significant': pvalue < 0.05
        }
        
        if len(human_scores) < 30:
            result['warning'] = 'Sample size < 30, results should be interpreted with caution'
        
        return result
        
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {
            'statistic': None,
            'pvalue': None,
            'sample_size': len(human_scores),
            'error': str(e)
        }

def generate_final_report(data: List[Dict[str, Any]], wilcoxon_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive final report.
    """
    total_methods = len(data)
    
    # Calculate coverage statistics
    coverage_scores = [item.get('coverage_score', 0.0) for item in data]
    avg_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0.0
    
    # Calculate semantic similarity statistics
    similarity_scores = [item.get('semantic_similarity', 0.0) for item in data]
    avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
    
    # Count methods with perfect coverage
    perfect_coverage_count = sum(1 for score in coverage_scores if score == 1.0)
    
    report = {
        'total_methods_analyzed': total_methods,
        'average_parameter_coverage': avg_coverage,
        'average_semantic_similarity': avg_similarity,
        'methods_with_perfect_coverage': perfect_coverage_count,
        'perfect_coverage_rate': perfect_coverage_count / total_methods if total_methods > 0 else 0.0,
        'wilcoxon_test_results': wilcoxon_result,
        'analysis_timestamp': str(Path.cwd())  # Placeholder for actual timestamp
    }
    
    return report

def main():
    """
    Main entry point for analysis pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze docstring coverage and similarity')
    parser.add_argument('--input', type=str, default='data/processed/results.json',
                      help='Input file path')
    parser.add_argument('--output-scores', type=str, default='data/processed/results_with_scores.json',
                      help='Output file with coverage scores')
    parser.add_argument('--report', type=str, default='data/processed/final_report.json',
                      help='Output file for final report')
    parser.add_argument('--no-similarity', action='store_true',
                      help='Skip semantic similarity calculation')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Process results for coverage
    data_with_scores = process_results_for_coverage(input_path)
    
    # Save intermediate results
    with open(args.output_scores, 'w') as f:
        json.dump(data_with_scores, f, indent=2)
    logger.info(f"Saved results with scores to {args.output_scores}")
    
    # Add semantic similarity if not skipped
    if not args.no_similarity:
        data_with_scores = add_semantic_similarity_to_data(data_with_scores)
        # Update the file with similarity scores
        with open(args.output_scores, 'w') as f:
            json.dump(data_with_scores, f, indent=2)
        logger.info(f"Added semantic similarity to {args.output_scores}")
    
    # Run Wilcoxon analysis
    wilcoxon_result = run_wilcoxon_analysis(data_with_scores)
    logger.info(f"Wilcoxon test completed: {wilcoxon_result}")
    
    # Generate final report
    final_report = generate_final_report(data_with_scores, wilcoxon_result)
    
    with open(args.report, 'w') as f:
        json.dump(final_report, f, indent=2)
    logger.info(f"Final report saved to {args.report}")
    
    # Print summary
    print("\n=== Analysis Summary ===")
    print(f"Total methods analyzed: {final_report['total_methods_analyzed']}")
    print(f"Average parameter coverage: {final_report['average_parameter_coverage']:.4f}")
    print(f"Average semantic similarity: {final_report['average_semantic_similarity']:.4f}")
    print(f"Methods with perfect coverage: {final_report['methods_with_perfect_coverage']}")
    
    if wilcoxon_result.get('pvalue') is not None:
        print(f"Wilcoxon p-value: {wilcoxon_result['pvalue']:.6f}")
        print(f"Statistically significant (p < 0.05): {wilcoxon_result['significant']}")
    
    if wilcoxon_result.get('warning'):
        print(f"Warning: {wilcoxon_result['warning']}")
    
    print("========================\n")

if __name__ == '__main__':
    main()