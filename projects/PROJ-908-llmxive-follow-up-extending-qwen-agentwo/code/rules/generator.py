"""
Generator for the Hypothesized Rule Set.

This module orchestrates the extraction, validation, and serialization of rules
derived from LLM CoT traces into a persistent JSON artifact.

It imports from:
  - rules.extractor (RuleExtractor, ExtractedRule)
  - rules.validator (RuleValidator)
  - utils.checksums (generate_checksum_manifest, compute_file_sha256)
"""
import json
import logging
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from local project modules
from rules.extractor import RuleExtractor
from rules.validator import RuleValidator
from utils.checksums import generate_checksum_manifest, compute_file_sha256

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def generate_rules_artifact(
    input_traces_path: Path,
    oracle_graph_path: Path,
    output_path: Path,
    checksum_manifest_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generates the Hypothesized Rule Set artifact.
    
    1. Loads CoT traces.
    2. Extracts rules using RuleExtractor.
    3. Validates rules against the Oracle using RuleValidator.
    4. Serializes the valid rules to `output_path`.
    5. Generates a checksum manifest if `checksum_manifest_path` is provided.
    
    Args:
        input_traces_path: Path to the input CoT traces JSON.
        oracle_graph_path: Path to the Ground Truth Oracle JSON.
        output_path: Path where the extracted_rules.json will be written.
        checksum_manifest_path: Optional path for the checksum manifest.
        
    Returns:
        A dictionary containing the summary of the generation process.
    """
    logger.info(f"Starting rule generation from {input_traces_path}")
    
    if not input_traces_path.exists():
        raise FileNotFoundError(f"Input traces file not found: {input_traces_path}")
    if not oracle_graph_path.exists():
        raise FileNotFoundError(f"Oracle graph file not found: {oracle_graph_path}")

    # 1. Initialize Extractor and Validator
    extractor = RuleExtractor()
    validator = RuleValidator()

    # 2. Load Traces
    logger.info("Loading CoT traces...")
    with open(input_traces_path, "r", encoding="utf-8") as f:
        traces_data = json.load(f)
    
    # Ensure we have a list of traces
    if isinstance(traces_data, dict) and "traces" in traces_data:
        traces = traces_data["traces"]
    elif isinstance(traces_data, list):
        traces = traces_data
    else:
        raise ValueError("Input traces must be a list or a dict with a 'traces' key")

    # 3. Extract Rules
    logger.info("Extracting rules from traces...")
    extracted_rules: List[Dict[str, Any]] = []
    
    for trace in traces:
        # Extract rules for this trace
        rules = extractor.extract(trace)
        for rule in rules:
            # Validate against Oracle immediately
            validation = validator.validate(rule, oracle_graph_path)
            if validation.is_valid:
                # Convert dataclass to dict and add validation metadata
                rule_dict = asdict(rule)
                rule_dict["validation_status"] = "valid"
                rule_dict["confidence_score"] = validation.confidence
                extracted_rules.append(rule_dict)
            else:
                # Log but do not include invalid rules in the primary artifact
                # or include them with a flag if the schema allows.
                # Per FR-002, we focus on the validated set.
                logger.debug(f"Rule skipped due to validation failure: {rule.rule_id}")

    # 4. Construct the Artifact Structure
    artifact = {
        "metadata": {
            "source_traces": str(input_traces_path),
            "oracle_source": str(oracle_graph_path),
            "total_traces_processed": len(traces),
            "total_rules_extracted": len(extracted_rules),
            "generator_version": "1.0.0"
        },
        "rules": extracted_rules
    }

    # 5. Ensure Output Directory Exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 6. Write Artifact
    logger.info(f"Writing {len(extracted_rules)} rules to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)

    # 7. Generate Checksums if requested
    if checksum_manifest_path:
        logger.info("Generating checksum manifest...")
        manifest = generate_checksum_manifest([output_path], output_dir=output_path.parent)
        with open(checksum_manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest written to {checksum_manifest_path}")

    logger.info("Rule generation complete.")
    return {
        "status": "success",
        "output_file": str(output_path),
        "rules_count": len(extracted_rules)
    }

def main():
    """
    Main entry point for running the rule generation script.
    Reads configuration from environment or defaults.
    """
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    traces_path = project_root / "data" / "raw" / "cot_traces.json"
    oracle_path = project_root / "data" / "processed" / "oracle_graph.json"
    output_path = project_root / "data" / "processed" / "extracted_rules.json"
    manifest_path = project_root / "data" / "processed" / "extracted_rules_manifest.json"

    # Allow override via command line args
    if len(sys.argv) > 1:
        traces_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        oracle_path = Path(sys.argv[2])
    if len(sys.argv) > 3:
        output_path = Path(sys.argv[3])

    try:
        result = generate_rules_artifact(
            input_traces_path=traces_path,
            oracle_graph_path=oracle_path,
            output_path=output_path,
            checksum_manifest_path=manifest_path
        )
        print(f"Success: {result['rules_count']} rules generated.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Rule generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
