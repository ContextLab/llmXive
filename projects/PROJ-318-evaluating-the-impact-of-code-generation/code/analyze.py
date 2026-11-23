"""
Analysis pipeline for evaluating code generation impact.
Handles coverage calculation, semantic similarity, statistical analysis, and final reporting.
"""
import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import argparse
from scipy import stats
import numpy as np

# Local imports based on API surface
from docstring_parser import parse as docstring_parse
from docstring_parser import Docstring

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "analyze.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_logging():
    """Initialize logging configuration."""
    return logger

def strip_type_hints(param_str: str) -> str:
    """
    Strip type hints from a parameter string.
    E.g., 'List[str]' -> 'str', 'Optional[int]' -> 'int'
    """
    if not param_str:
        return ""
    # Simple heuristic: find the last dot or bracket content if it looks like a type
    # For this specific task, we focus on matching the core name.
    # If the string contains '->', it might be a return annotation, ignore.
    # We assume param_str is just the parameter definition or name.
    # Common patterns: 'name: type', 'name', 'name: list[int]'
    if ':' in param_str:
        return param_str.split(':')[0].strip()
    # Remove generic brackets content for matching simplicity if needed, 
    # but usually just the name is enough.
    return param_str

def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents as a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list in {file_path}, got {type(data)}")
    return data

def save_json_file(file_path: Path, data: List[Dict[str, Any]]) -> None:
    """Save a list of dictionaries to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} records to {file_path}")

def calculate_coverage_scores(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate Parameter Coverage Score for each record.
    Score = (matched params / total AST params)
    """
    results = []
    for record in data:
        ast_params = record.get("ast_params", [])
        generated_docstring = record.get("generated_docstring") or ""
        human_docstring = record.get("human_docstring") or ""
        
        # We compare generated docstring against AST params
        # If generated docstring is missing, score is 0
        if not generated_docstring or not generated_docstring.strip():
            score = 0.0
            parse_error = False
        else:
            try:
                parsed = docstring_parse(generated_docstring)
                doc_params = [p.arg_name for p in parsed.params if p.arg_name]
                
                # Normalize AST params (strip type hints)
                normalized_ast = [strip_type_hints(p).lower() for p in ast_params if p]
                normalized_doc = [p.lower() for p in doc_params]
                
                if not normalized_ast:
                    score = 0.0
                else:
                    matched = len(set(normalized_doc) & set(normalized_ast))
                    score = matched / len(normalized_ast)
                parse_error = False
            except Exception as e:
                logger.warning(f"Docstring parsing error: {e}")
                score = 0.0
                parse_error = True

        new_record = record.copy()
        new_record["coverage_score"] = round(score, 4)
        if parse_error:
            new_record["parse_error"] = True
        results.append(new_record)
    
    return results

def calculate_semantic_similarity(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate semantic similarity between human and generated docstrings.
    Uses sentence-transformers/all-MiniLM-L6-v2.
    """
    # Lazy import to avoid loading model if not needed
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except ImportError:
        raise ImportError("sentence-transformers is required for semantic similarity. Run: pip install sentence-transformers")

    results = []
    texts_h = []
    texts_g = []
    indices = []

    for i, record in enumerate(data):
        h = record.get("human_docstring")
        g = record.get("generated_docstring")
        
        # Handle None/empty
        if not h or not h.strip():
            h = ""
        if not g or not g.strip():
            g = ""
        
        texts_h.append(h)
        texts_g.append(g)
        indices.append(i)

    if not texts_h:
        # Return original data with 0.0 similarity if empty
        for i, record in enumerate(data):
            new_record = record.copy()
            new_record["semantic_similarity"] = 0.0
            results.append(new_record)
        return results

    embeddings_h = model.encode(texts_h, convert_to_numpy=True)
    embeddings_g = model.encode(texts_g, convert_to_numpy=True)

    # Cosine similarity
    similarities = np.zeros(len(texts_h))
    for i in range(len(texts_h)):
        if np.linalg.norm(embeddings_h[i]) == 0 or np.linalg.norm(embeddings_g[i]) == 0:
            similarities[i] = 0.0
        else:
            similarities[i] = np.dot(embeddings_h[i], embeddings_g[i]) / (
                np.linalg.norm(embeddings_h[i]) * np.linalg.norm(embeddings_g[i])
            )

    for i, record in enumerate(data):
        new_record = record.copy()
        new_record["semantic_similarity"] = round(float(similarities[i]), 4)
        results.append(new_record)

    return results

def run_wilcoxon_analysis(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test on Human vs LLM coverage scores.
    Returns test statistic and p-value.
    """
    human_scores = []
    llm_scores = []

    for record in data:
        # We compare human docstring coverage vs generated docstring coverage?
        # Actually, the task implies comparing coverage scores derived from human vs generated.
        # But typically, we compare the coverage score of the generated docstring against a baseline?
        # The prompt says: "paired comparison of Human vs. LLM coverage scores".
        # Since we only calculated coverage for the generated docstring in calculate_coverage_scores,
        # we need to calculate it for the human docstring too to have a pair?
        # OR, the task implies the 'coverage_score' in the data IS the LLM score, and we compare it to a theoretical perfect human score?
        # Re-reading T035: "paired comparison of Human vs. LLM coverage scores".
        # This implies we need two scores per record.
        # Let's assume the input data has 'human_coverage_score' and 'generated_coverage_score'.
        # If not, we calculate them on the fly.
        
        # Calculate human coverage
        h_doc = record.get("human_docstring") or ""
        ast_params = record.get("ast_params", [])
        
        h_score = 0.0
        if h_doc.strip() and ast_params:
            try:
                parsed = docstring_parse(h_doc)
                doc_params = [p.arg_name for p in parsed.params if p.arg_name]
                normalized_ast = [strip_type_hints(p).lower() for p in ast_params if p]
                normalized_doc = [p.lower() for p in doc_params]
                if normalized_ast:
                    matched = len(set(normalized_doc) & set(normalized_ast))
                    h_score = matched / len(normalized_ast)
            except:
                h_score = 0.0

        # Get generated coverage (already in record as coverage_score)
        g_score = record.get("coverage_score", 0.0)
        
        human_scores.append(h_score)
        llm_scores.append(g_score)

    if len(human_scores) < 2:
        logger.warning("Not enough data points for Wilcoxon test.")
        return {"statistic": 0.0, "pvalue": 1.0, "n": len(human_scores)}

    # Check sample size warning
    if len(human_scores) < 30:
        logger.warning(f"Statistical power may be low (n < 30). Proceeding with calculation.")

    try:
        stat, pvalue = stats.wilcoxon(human_scores, llm_scores)
        return {
            "statistic": float(stat),
            "pvalue": float(pvalue),
            "n": len(human_scores)
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {"statistic": 0.0, "pvalue": 1.0, "n": len(human_scores), "error": str(e)}

def generate_final_report(data: List[Dict[str, Any]], stats_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate the final report JSON.
    Includes p-value, test statistic, and coverage rates.
    """
    total_records = len(data)
    if total_records == 0:
        avg_human = 0.0
        avg_llm = 0.0
    else:
        # Calculate average coverage for human and llm
        human_scores = []
        llm_scores = []
        for record in data:
            h_doc = record.get("human_docstring") or ""
            ast_params = record.get("ast_params", [])
            h_score = 0.0
            if h_doc.strip() and ast_params:
                try:
                    parsed = docstring_parse(h_doc)
                    doc_params = [p.arg_name for p in parsed.params if p.arg_name]
                    normalized_ast = [strip_type_hints(p).lower() for p in ast_params if p]
                    normalized_doc = [p.lower() for p in doc_params]
                    if normalized_ast:
                        matched = len(set(normalized_doc) & set(normalized_ast))
                        h_score = matched / len(normalized_ast)
                except:
                    h_score = 0.0
            human_scores.append(h_score)
            llm_scores.append(record.get("coverage_score", 0.0))
        
        avg_human = sum(human_scores) / len(human_scores)
        avg_llm = sum(llm_scores) / len(llm_scores)

    report = {
        "total_methods": total_records,
        "average_human_coverage": round(avg_human, 4),
        "average_llm_coverage": round(avg_llm, 4),
        "wilcoxon_test": {
            "statistic": stats_result.get("statistic"),
            "pvalue": stats_result.get("pvalue"),
            "sample_size": stats_result.get("n"),
            "significant": stats_result.get("pvalue", 1.0) < 0.05
        },
        "timestamp": str(Path(__file__).parent.absolute()) # Placeholder for actual timestamp if needed
    }
    return report

def main():
    parser = argparse.ArgumentParser(description="Analysis pipeline for code generation evaluation")
    parser.add_argument("--step", type=str, choices=["coverage", "similarity", "stats", "report"],
                        help="Step to execute")
    parser.add_argument("--input", type=str, help="Input JSON file path")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    
    args = parser.parse_args()

    if args.step == "coverage":
        input_path = Path(args.input) if args.input else Path("data/processed/results.json")
        output_path = Path(args.output) if args.output else Path("data/processed/results_with_coverage.json")
        
        logger.info(f"Loading data from {input_path}")
        data = load_json_file(input_path)
        logger.info(f"Calculated coverage scores for {len(data)} records")
        result_data = calculate_coverage_scores(data)
        save_json_file(output_path, result_data)

    elif args.step == "similarity":
        input_path = Path(args.input) if args.input else Path("data/processed/results_with_coverage.json")
        output_path = Path(args.output) if args.output else Path("data/processed/results_with_scores.json")
        
        logger.info(f"Loading data from {input_path}")
        data = load_json_file(input_path)
        logger.info(f"Calculated semantic similarity for {len(data)} records")
        result_data = calculate_semantic_similarity(data)
        save_json_file(output_path, result_data)

    elif args.step == "stats":
        input_path = Path(args.input) if args.input else Path("data/processed/results_with_scores.json")
        output_path = Path(args.output) if args.output else Path("data/processed/results_with_stats.json")
        
        logger.info(f"Loading data from {input_path}")
        data = load_json_file(input_path)
        logger.info(f"Running Wilcoxon analysis on {len(data)} records")
        stats_result = run_wilcoxon_analysis(data)
        
        # Append stats result to each record? Or just save the stats result?
        # The task says "write to results_with_stats.json". Usually this implies the data with stats appended or just the stats.
        # Given the flow, it likely appends the stats result to the records or creates a summary.
        # Let's append the stats result to each record for consistency, or create a wrapper.
        # Re-reading T035: "write to data/processed/results_with_stats.json".
        # T037 expects "results_with_stats.json" to exist.
        # Let's assume we append the stats result (stat, pvalue) to each record.
        for record in data:
            record["wilcoxon_statistic"] = stats_result.get("statistic")
            record["wilcoxon_pvalue"] = stats_result.get("pvalue")
        
        save_json_file(output_path, data)
        logger.info(f"Stats saved to {output_path}")
        # Also save the raw stats result for the report step
        with open(Path("data/processed/wilcoxon_result.json"), 'w') as f:
            json.dump(stats_result, f, indent=2)

    elif args.step == "report":
        input_path = Path(args.input) if args.input else Path("data/processed/results_with_stats.json")
        output_path = Path(args.output) if args.output else Path("data/processed/final_report.json")
        
        logger.info(f"Loading data from {input_path}")
        if not input_path.exists():
            raise FileNotFoundError(f"Input file for report not found: {input_path}")
        
        data = load_json_file(input_path)
        
        # Load stats result if saved separately, or re-calculate
        stats_path = Path("data/processed/wilcoxon_result.json")
        if stats_path.exists():
            with open(stats_path, 'r') as f:
                stats_result = json.load(f)
        else:
            # Fallback: re-calculate
            stats_result = run_wilcoxon_analysis(data)

        logger.info("Generating final report")
        report = generate_final_report(data, stats_result)
        save_json_file(output_path, [report]) # Save as list for consistency, or just object? T037 says "final_report.json". Usually object.
        # Let's save as object if it's a single report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Final report saved to {output_path}")
        print(json.dumps(report, indent=2))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()