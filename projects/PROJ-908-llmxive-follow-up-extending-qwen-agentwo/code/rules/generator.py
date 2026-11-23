import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from rules.extractor import RuleExtractor, ExtractedRule
from rules.validator import RuleValidator

logger = logging.getLogger("rules.generator")

def generate_rules_artifact(input_traces_path: Path, output_rules_path: Path, oracle_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point to generate the rules artifact.
    1. Load traces.
    2. Extract rules.
    3. Validate against Oracle (if available).
    4. Save results.
    """
    logger.info(f"Generating rules from {input_traces_path}...")
    
    if not input_traces_path.exists():
        raise FileNotFoundError(f"Input traces not found: {input_traces_path}")
    
    with open(input_traces_path, 'r') as f:
        traces = json.load(f)
    
    # Extract rules
    extractor = RuleExtractor()
    extracted_rules = extractor.extract(traces)
    
    # Validate if oracle exists
    if oracle_path and oracle_path.exists():
        with open(oracle_path, 'r') as f:
            oracle_graph = json.load(f)
        
        validator = RuleValidator(oracle_graph)
        validation_results = validator.validate(extracted_rules)
    else:
        validation_results = []
    
    # Prepare artifact
    artifact = {
        "metadata": {
            "source_traces": str(input_traces_path),
            "validation_source": str(oracle_path) if oracle_path else None,
            "total_rules": len(extracted_rules),
            "validation_passed": len([v for v in validation_results if v.passed])
        },
        "rules": [asdict(r) for r in extracted_rules],
        "validation": validation_results
    }
    
    # Save
    output_path = Path(output_rules_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(artifact, f, indent=2)
    
    logger.info(f"Rules artifact saved to {output_path}")
    return artifact

def main():
    logger.info("Starting Rule Generation...")
    input_path = Path("data/raw/cot_traces.json")
    output_path = Path("data/processed/extracted_rules.json")
    oracle_path = Path("data/processed/oracle_graph.json")
    
    generate_rules_artifact(input_path, output_path, oracle_path)
    logger.info("Rule generation complete.")

if __name__ == "__main__":
    main()
