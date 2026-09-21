import json
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats
import numpy as np
from docstring_parser import parse
import argparse

# Import local utilities
from utils.coverage import parse_docstring_parameters, calculate_parameter_coverage
from utils.stats import run_wilcoxon_test, StatsException

def setup_logging(log_file: str = "logs/analysis.log") -> logging.Logger:
    """Configure logging for the analysis pipeline."""
    logger = logging.getLogger("analyze")
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def strip_type_hints(param_str: str) -> str:
    """Remove type hints from a parameter string (e.g., 'List[str]' -> 'str')."""
    if not param_str:
        return param_str
    # Simple heuristic: take the last word if it looks like a type, 
    # but docstring_parser usually handles this. 
    # We'll rely on docstring_parser's output which is usually clean 'name'
    return param_str

def calculate_coverage_scores(data: List[Dict[str, Any]], logger: logging.Logger) -> List[Dict[str, Any]]:
    """Calculate parameter coverage scores for each record."""
    results = []
    for record in data:
        ast_params = record.get("ast_params", [])
        docstring_text = record.get("generated_docstring") or record.get("human_docstring")
        
        if not ast_params:
            score = 0.0
            results.append({**record, "coverage_score": score})
            continue
        
        try:
            doc = parse(docstring_text) if docstring_text else None
            if not doc:
                score = 0.0
            else:
                # Extract param names from docstring
                doc_params = [p.arg_name for p in doc.params if p.arg_name]
                # Match case-insensitively
                ast_param_names = [p.lower() for p in ast_params]
                doc_param_names = [p.lower() for p in doc_params]
                
                matched = sum(1 for name in doc_param_names if name in ast_param_names)
                score = matched / len(ast_params) if ast_params else 0.0
        except Exception as e:
            logger.warning(f"Parse error for record: {e}")
            score = 0.0
            record["parse_error"] = True
        
        results.append({**record, "coverage_score": score})
    
    return results

def run_wilcoxon_analysis(data: List[Dict[str, Any]], logger: logging.Logger) -> Dict[str, Any]:
    """Run Wilcoxon signed-rank test on human vs LLM coverage scores."""
    human_scores = []
    llm_scores = []
    
    for record in data:
        # We need human coverage score. 
        # In this pipeline, 'coverage_score' in the input file (from T033/T034) 
        # was calculated on the generated docstring. 
        # We need to re-calculate or assume the input file has both.
        # However, T033 calculates coverage on the generated docstring.
        # To do a paired test, we need Human Coverage vs LLM Coverage.
        # Let's assume the input data has 'human_docstring' and 'generated_docstring'.
        # We will calculate human coverage on the fly if not present, or assume 
        # the previous step calculated both. 
        # Given the task description: "paired comparison of Human vs. LLM coverage scores".
        # We will calculate human coverage score now if missing.
        
        human_doc = record.get("human_docstring")
        gen_doc = record.get("generated_docstring")
        ast_params = record.get("ast_params", [])
        
        if not ast_params:
            continue
        
        # Calculate Human Score
        h_score = 0.0
        if human_doc:
            try:
                doc = parse(human_doc)
                if doc:
                    doc_params = [p.arg_name for p in doc.params if p.arg_name]
                    ast_param_names = [p.lower() for p in ast_params]
                    doc_param_names = [p.lower() for p in doc_params]
                    matched = sum(1 for name in doc_param_names if name in ast_param_names)
                    h_score = matched / len(ast_params)
            except:
                h_score = 0.0
        
        # Calculate LLM Score (use existing coverage_score if present, else recalc)
        l_score = record.get("coverage_score", 0.0)
        if l_score == 0.0 and gen_doc:
             try:
                doc = parse(gen_doc)
                if doc:
                    doc_params = [p.arg_name for p in doc.params if p.arg_name]
                    ast_param_names = [p.lower() for p in ast_params]
                    doc_param_names = [p.lower() for p in doc_params]
                    matched = sum(1 for name in doc_param_names if name in ast_param_names)
                    l_score = matched / len(ast_params)
             except:
                l_score = 0.0

        human_scores.append(h_score)
        llm_scores.append(l_score)
    
    if len(human_scores) < 2:
        logger.warning("Insufficient data for Wilcoxon test (n < 2).")
        return {
            "statistic": 0.0,
            "pvalue": 1.0,
            "n_pairs": len(human_scores),
            "warning": "Insufficient data"
        }
    
    try:
        # Log small dataset warning
        if len(human_scores) < 30:
            logger.warning(f"Statistical power may be low (n = {len(human_scores)} < 30)")
        
        statistic, pvalue = stats.wilcoxon(human_scores, llm_scores)
        return {
            "statistic": float(statistic),
            "pvalue": float(pvalue),
            "n_pairs": len(human_scores),
            "warning": "Statistical power may be low (n < 30)" if len(human_scores) < 30 else None
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return {
            "statistic": 0.0,
            "pvalue": 1.0,
            "n_pairs": len(human_scores),
            "error": str(e)
        }

def generate_final_report(data: List[Dict[str, Any]], stats_results: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """Generate the final report with p-value, test statistic, and coverage rates."""
    total_records = len(data)
    if total_records == 0:
        return {"error": "No data available for report"}
    
    # Calculate average coverage rates
    human_scores = []
    llm_scores = []
    
    for record in data:
        ast_params = record.get("ast_params", [])
        if not ast_params:
            continue
        
        # Human Score
        h_score = 0.0
        human_doc = record.get("human_docstring")
        if human_doc:
            try:
                doc = parse(human_doc)
                if doc:
                    doc_params = [p.arg_name for p in doc.params if p.arg_name]
                    ast_param_names = [p.lower() for p in ast_params]
                    doc_param_names = [p.lower() for p in doc_params]
                    matched = sum(1 for name in doc_param_names if name in ast_param_names)
                    h_score = matched / len(ast_params)
            except: pass
        human_scores.append(h_score)
        
        # LLM Score
        l_score = record.get("coverage_score", 0.0)
        if l_score == 0.0 and record.get("generated_docstring"):
            try:
                doc = parse(record["generated_docstring"])
                if doc:
                    doc_params = [p.arg_name for p in doc.params if p.arg_name]
                    ast_param_names = [p.lower() for p in ast_params]
                    doc_param_names = [p.lower() for p in doc_params]
                    matched = sum(1 for name in doc_param_names if name in ast_param_names)
                    l_score = matched / len(ast_params)
            except: pass
        llm_scores.append(l_score)
    
    avg_human = np.mean(human_scores) if human_scores else 0.0
    avg_llm = np.mean(llm_scores) if llm_scores else 0.0
    
    report = {
        "total_records": total_records,
        "valid_pairs": len(human_scores),
        "average_human_coverage": float(avg_human),
        "average_llm_coverage": float(avg_llm),
        "wilcoxon_test": stats_results
    }
    
    logger.info(f"Report generated: {total_records} records, p-value={stats_results.get('pvalue')}")
    return report

def main():
    parser = argparse.ArgumentParser(description="Analysis pipeline for code documentation evaluation")
    parser.add_argument("--step", type=str, choices=["coverage", "similarity", "stats", "report"], 
                      help="Step to execute")
    parser.add_argument("--input-dir", type=str, default="data/processed", help="Input directory")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    args = parser.parse_args()
    
    logger = setup_logging()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine input file based on step
    if args.step == "coverage":
        input_file = input_dir / "results.json"
        output_file = output_dir / "results_with_coverage.json"
    elif args.step == "similarity":
        input_file = output_dir / "results_with_coverage.json"
        output_file = output_dir / "results_with_scores.json"
    elif args.step == "stats":
        input_file = output_dir / "results_with_scores.json"
        output_file = output_dir / "results_with_stats.json"
    elif args.step == "report":
        input_file = output_dir / "results_with_stats.json"
        output_file = output_dir / "final_report.json"
    else:
        logger.error("No step specified")
        sys.exit(1)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    with open(input_file, "r") as f:
        data = json.load(f)
    
    logger.info(f"Processing {len(data)} records from {input_file}")
    
    if args.step == "coverage":
        processed_data = calculate_coverage_scores(data, logger)
        with open(output_file, "w") as f:
            json.dump(processed_data, f, indent=2)
        logger.info(f"Wrote coverage scores to {output_file}")
    
    elif args.step == "similarity":
        # Placeholder for semantic similarity if needed, but task T034 handles it.
        # Assuming data already has 'semantic_similarity' from T034 if we are here.
        # If T034 is skipped, we might need to implement it here.
        # For T037, we assume T034 ran.
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Copied data to {output_file} (similarity step skipped or already done)")
    
    elif args.step == "stats":
        stats_results = run_wilcoxon_analysis(data, logger)
        # Add stats results to every record or just save separately? 
        # Task says "write to results_with_stats.json". Usually implies appending stats to records.
        # But Wilcoxon is a summary. Let's append the summary to each record for consistency 
        # or just save the summary. The task says "paired comparison... write to ...json".
        # Let's append the test results to the data structure.
        # To be safe, we'll save the list of records with the stats summary attached as a metadata field 
        # or just save the summary. The previous tasks output lists of records.
        # Let's add the stats summary to each record for uniformity, or better:
        # The task T035 says "write to results_with_stats.json". 
        # We will output the original data with an additional 'stats_summary' field if needed, 
        # but typically statistical reports are separate.
        # However, to keep the pipeline consistent (list of records), we will add the stats result 
        # to the records, but since it's the same for all, we'll just save the stats result 
        # as a single object if the file is meant to be the report.
        # Re-reading T035: "write to data/processed/results_with_stats.json". 
        # Let's assume this file contains the records with the stats summary attached or just the summary.
        # Given T037 reads it to generate final_report.json, let's store the summary.
        # But T037 says "Verify ... exists". 
        # Let's save the stats summary as the content of the file? 
        # No, T033/T034 output lists of records. T035 should likely do the same.
        # Let's add the stats result to each record.
        for record in data:
            record["stats_summary"] = stats_results
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Wrote stats analysis to {output_file}")
    
    elif args.step == "report":
        stats_summary = None
        # Extract stats from the first record if they were attached, or read a separate file?
        # If T035 attached it to records:
        if data and "stats_summary" in data[0]:
            stats_summary = data[0]["stats_summary"]
        else:
            # Fallback: re-run if not present (should not happen in correct flow)
            logger.warning("Stats summary not found in records, re-running analysis.")
            stats_summary = run_wilcoxon_analysis(data, logger)
        
        report = generate_final_report(data, stats_summary, logger)
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Final report written to {output_file}")
    
    else:
        logger.error("Invalid step")
        sys.exit(1)

if __name__ == "__main__":
    main()