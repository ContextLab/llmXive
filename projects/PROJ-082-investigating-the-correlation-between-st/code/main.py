import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import get_project_root, ensure_directory
from utils.logger import get_logger
from extraction.parser import parse_input
from analysis.meta_analysis import run_meta_analysis
from analysis.narrative import generate_narrative_summary
from analysis.bias import run_bias_assessment
from analysis.heterogeneity import run_heterogeneity_analysis, update_output_json
from visualization.plots import run_visualization_analysis

logger = get_logger(__name__)

def run_pipeline(
    input_path: Path,
    output_dir: Path,
    force_narrative: bool = False
) -> Dict[str, Any]:
    """Run the complete meta-analysis pipeline."""
    ensure_directory(output_dir)
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "pipeline_version": "1.0.0",
        "input_file": str(input_path)
    }
    
    # Step 1: Parse input data
    logger.info(f"Parsing input file: {input_path}")
    studies = parse_input(input_path)
    results["study_count"] = len(studies)
    
    if len(studies) == 0:
        logger.warning("No studies found in input file.")
        results["status"] = "no_data"
        # Generate narrative for zero studies
        narrative_output = output_dir / "narrative_summary.md"
        # Create a temporary CSV for narrative generator
        import csv
        temp_csv = output_dir / "temp_studies.csv"
        with open(temp_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['study_id', 'qualitative_desc', 'narrative_pool'])
            writer.writeheader()
        generate_narrative_summary(temp_csv, narrative_output)
        results["synthesis_mode"] = "narrative"
        results["narrative_summary"] = str(narrative_output)
        return results
    
    # Save intermediate studies for meta-analysis
    studies_json = output_dir / "studies_for_analysis.json"
    with open(studies_json, 'w') as f:
        json.dump(studies, f, indent=2)
    
    # Step 2: Check study count and decide synthesis mode
    n = len(studies)
    if n < 10 or force_narrative:
        logger.info(f"Study count ({n}) < 10. Generating narrative summary.")
        results["synthesis_mode"] = "narrative"
        
        # Generate narrative summary
        # Convert studies to CSV format for narrative generator
        import csv
        temp_csv = output_dir / "temp_studies.csv"
        with open(temp_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['study_id', 'qualitative_desc', 'narrative_pool'])
            writer.writeheader()
            for study in studies:
                writer.writerow({
                    'study_id': study.get('study_id', ''),
                    'qualitative_desc': study.get('qualitative_desc', ''),
                    'narrative_pool': study.get('narrative_pool', False)
                })
        
        narrative_output = output_dir / "narrative_summary.md"
        generate_narrative_summary(temp_csv, narrative_output)
        results["narrative_summary"] = str(narrative_output)
        
        # Still run meta-analysis for reference (but mark as not used)
        meta_output = output_dir / "meta_analysis_results.json"
        meta_results = run_meta_analysis(studies_json, meta_output)
        results["meta_analysis"] = meta_results
        
    else:
        logger.info(f"Study count ({n}) >= 10. Proceeding with quantitative analysis.")
        results["synthesis_mode"] = "quantitative"
        
        # Run meta-analysis
        meta_output = output_dir / "meta_analysis_results.json"
        meta_results = run_meta_analysis(studies_json, meta_output)
        results["meta_analysis"] = meta_results
        
        # Run heterogeneity analysis
        hetero_output = output_dir / "heterogeneity_results.json"
        hetero_results = run_heterogeneity_analysis(studies_json, meta_output)
        update_output_json(hetero_results, meta_output)
        results["heterogeneity"] = hetero_results
        
        # Run bias assessment
        bias_output = output_dir / "bias_results.json"
        bias_results = run_bias_assessment(studies_json, bias_output, meta_output)
        results["bias"] = bias_results
        
        # Generate plots
        plots_dir = output_dir
        run_visualization_analysis(meta_output, plots_dir)
    
    # Final results
    final_output = output_dir / "results.json"
    with open(final_output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Pipeline complete. Results saved to {final_output}")
    return results

def main() -> None:
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Meta-analysis pipeline for brain connectivity and music preferences")
    parser.add_argument("--input", type=str, required=True, help="Input data file (CSV or JSON)")
    parser.add_argument("--output", type=str, default="data/derived", help="Output directory")
    parser.add_argument("--force-narrative", action="store_true", help="Force narrative synthesis even if N >= 10")
    args = parser.parse_args()
    
    root = get_project_root()
    input_path = root / args.input
    output_dir = root / args.output
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    results = run_pipeline(input_path, output_dir, args.force_narrative)
    print(f"Pipeline completed. Synthesis mode: {results.get('synthesis_mode', 'unknown')}")

if __name__ == "__main__":
    main()