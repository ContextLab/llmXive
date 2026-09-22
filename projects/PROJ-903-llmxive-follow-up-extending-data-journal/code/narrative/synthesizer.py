import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def run_synthesis_pipeline(baseline_result: Dict[str, Any], 
                           counterfactual_result: Dict[str, Any],
                           low_power_flag: bool = False) -> Dict[str, Any]:
    """
    Synthesize baseline and counterfactual results into a final narrative.
    
    Args:
        baseline_result: Output from baseline analysis (T012/T013)
        counterfactual_result: Output from inspector analysis (T021b)
        low_power_flag: Boolean indicating if low power warning is needed
        
    Returns:
        Dictionary containing the synthesized story and metadata
    """
    story_parts = []
    
    # 1. Primary Narrative
    if baseline_result and "primary_narrative" in baseline_result:
        story_parts.append(f"### Primary Narrative\n{baseline_result['primary_narrative']}")
    else:
        story_parts.append("### Primary Narrative\nNo significant baseline correlations found.")
        
    # 2. Counterfactual Insights
    story_parts.append("\n### Counterfactual Analysis")
    if counterfactual_result and "results" in counterfactual_result:
        results = counterfactual_result["results"]
        if results:
            for item in results:
                claim = item.get("claim", "No significant counterfactual found.")
                p_val = item.get("p_value", "N/A")
                r_val = item.get("partial_r", "N/A")
                story_parts.append(f"- **Claim**: {claim} (p={p_val}, r={r_val})")
        else:
            story_parts.append("- No significant counterfactuals found.")
    else:
        story_parts.append("- No counterfactual analysis performed.")
        
    # 3. Low Power Warning
    if low_power_flag:
        story_parts.append("\n### ⚠️ Caution: Low Power")
        story_parts.append("This analysis was conducted under low statistical power conditions. Interpret results with caution.")
        
    final_story = "\n".join(story_parts)
    
    return {
        "story": final_story,
        "baseline_summary": baseline_result,
        "counterfactual_summary": counterfactual_result,
        "low_power_flag": low_power_flag
    }

def main():
    """
    Main entry point for running the synthesis pipeline.
    Expects input files: data/processed/baseline_result.json, data/processed/inspector_result.json
    Outputs: output/synthesis_story.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run narrative synthesis pipeline")
    parser.add_argument("--baseline", type=str, default="data/processed/baseline_result.json", help="Path to baseline result")
    parser.add_argument("--counterfactual", type=str, default="data/processed/inspector_result.json", help="Path to counterfactual result")
    parser.add_argument("--output", type=str, default="output/synthesis_story.json", help="Output path")
    parser.add_argument("--low_power", action="store_true", help="Set low power flag")
    args = parser.parse_args()
    
    # Load inputs
    baseline_result = None
    if os.path.exists(args.baseline):
        with open(args.baseline, 'r') as f:
            baseline_result = json.load(f)
    else:
        logger.warning(f"Baseline result not found at {args.baseline}")
        
    counterfactual_result = None
    if os.path.exists(args.counterfactual):
        with open(args.counterfactual, 'r') as f:
            counterfactual_result = json.load(f)
    else:
        logger.warning(f"Counterfactual result not found at {args.counterfactual}")
        
    # Run synthesis
    result = run_synthesis_pipeline(baseline_result, counterfactual_result, args.low_power)
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Synthesis complete. Output written to {output_path}")

if __name__ == "__main__":
    main()