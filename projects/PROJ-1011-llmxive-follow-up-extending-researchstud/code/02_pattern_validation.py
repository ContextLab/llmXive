"""
Pattern Validation Module for User Story 2.

This module enforces the strict two-group design constraint (Pattern-guided vs. Baseline)
as defined in FR-003. It validates that the generation pipeline configuration and
execution logic do not contain or produce any 'random-pattern' logic.
"""
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from utils.error_handling import ValidationError
from utils.logging_config import get_logger

# Constants for allowed groups
ALLOWED_GROUPS: Set[str] = {"pattern-guided", "baseline"}
FORBIDDEN_GROUPS: Set[str] = {"random-pattern"}

logger = get_logger(__name__)


def validate_group_config(config_path: Optional[str] = None) -> None:
    """
    Validates the generation configuration file to ensure no 'random-pattern'
    logic is enabled.
    
    Args:
        config_path: Path to the generation config JSON. If None, checks 
                     standard locations or assumes default valid state if 
                     no config exists (fallback to strict mode).
                     
    Raises:
        ValidationError: If 'random-pattern' is found in the configuration.
    """
    logger.info("Validating generation group configuration...")
    
    # Default config path if not provided
    if config_path is None:
        config_path = "data/results/generation_config.json"
        
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"Config file {config_path} not found. Assuming strict two-group mode by default.")
        return

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in generation config: {e}")
    
    # Check for explicit forbidden flags
    if config.get("enable_random_pattern", False):
        logger.error("Configuration enables 'random-pattern' group.")
        raise ValidationError(
            "Configuration violation: 'enable_random_pattern' is True. "
            "FR-003 requires strict two-group design (pattern-guided vs baseline)."
        )
        
    # Check for allowed groups list
    allowed_groups = set(config.get("allowed_groups", []))
    if FORBIDDEN_GROUPS.intersection(allowed_groups):
        logger.error("Configuration includes forbidden group 'random-pattern'.")
        raise ValidationError(
            "Configuration violation: 'random-pattern' is in allowed_groups. "
            "Only 'pattern-guided' and 'baseline' are permitted."
        )
        
    # Ensure required groups are present if groups are specified
    if allowed_groups:
        if not ALLOWED_GROUPS.issubset(allowed_groups):
            logger.warning(
                f"Configured allowed_groups {allowed_groups} does not include "
                f"all required groups {ALLOWED_GROUPS}. Proceeding with strict check."
            )
        
    logger.info("Configuration validation passed: Two-group design enforced.")


def validate_generated_proposals(
    proposals_path: str,
    group_field: str = "group"
) -> Dict[str, Any]:
    """
    Validates the generated proposals file to ensure every proposal belongs
    to an allowed group ('pattern-guided' or 'baseline') and none belong
    to a forbidden group ('random-pattern').
    
    Args:
        proposals_path: Path to the generated proposals JSONL file.
        group_field: The key name in the proposal JSON that indicates the group.
                     
    Returns:
        A summary dictionary with counts of valid and invalid entries.
        
    Raises:
        ValidationError: If any proposal contains a forbidden group or an 
                         unexpected group type.
    """
    logger.info(f"Validating generated proposals at {proposals_path}...")
    path = Path(proposals_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Proposals file not found: {proposals_path}")
    
    valid_count = 0
    invalid_count = 0
    forbidden_found = []
    unexpected_found = []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    proposal = json.loads(line)
                except json.JSONDecodeError:
                    invalid_count += 1
                    unexpected_found.append(f"Line {line_num}: Invalid JSON")
                    continue
                    
                group = proposal.get(group_field)
                
                if group is None:
                    invalid_count += 1
                    unexpected_found.append(f"Line {line_num}: Missing '{group_field}' field")
                    continue
                
                if group in FORBIDDEN_GROUPS:
                    invalid_count += 1
                    forbidden_found.append(f"Line {line_num}: Found forbidden group '{group}'")
                elif group not in ALLOWED_GROUPS:
                    invalid_count += 1
                    unexpected_found.append(f"Line {line_num}: Unexpected group '{group}'")
                else:
                    valid_count += 1
                    
    except Exception as e:
        logger.error(f"Error reading proposals file: {e}")
        raise ValidationError(f"Failed to read proposals file: {e}")
        
    summary = {
        "total_processed": valid_count + invalid_count,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "forbidden_groups_found": len(forbidden_found),
        "unexpected_groups_found": len(unexpected_found)
    }
    
    if invalid_count > 0:
        error_details = []
        if forbidden_found:
            error_details.append(f"Forbidden groups detected: {forbidden_found[:5]}...")
        if unexpected_found:
            error_details.append(f"Unexpected groups detected: {unexpected_found[:5]}...")
            
        raise ValidationError(
            f"Proposal validation failed. Found {invalid_count} invalid entries.\n"
            + "\n".join(error_details)
        )
        
    logger.info(
        f"Validation passed: {valid_count} proposals verified. "
        f"Strict two-group design confirmed."
    )
    return summary


def run_full_validation(
    config_path: Optional[str] = None,
    proposals_path: str = "data/results/generated_proposals.jsonl"
) -> bool:
    """
    Runs the full validation suite for the two-group design constraint.
    
    1. Validates the generation configuration.
    2. Validates the generated output file.
    
    Args:
        config_path: Path to the generation config.
        proposals_path: Path to the generated proposals.
        
    Returns:
        True if validation passes.
        
    Raises:
        ValidationError: If any check fails.
    """
    logger.info("Starting full two-group design validation...")
    
    try:
        validate_group_config(config_path)
        validate_generated_proposals(proposals_path)
        logger.info("Full validation successful.")
        return True
    except (ValidationError, FileNotFoundError) as e:
        logger.error(f"Validation failed: {e}")
        raise


def main() -> int:
    """
    CLI entry point for running the validation.
    Expects arguments: --config <path> --proposals <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate two-group design constraint for proposal generation."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to generation config JSON (optional, defaults to data/results/generation_config.json)"
    )
    parser.add_argument(
        "--proposals",
        type=str,
        default="data/results/generated_proposals.jsonl",
        help="Path to generated proposals JSONL file"
    )
    
    args = parser.parse_args()
    
    try:
        run_full_validation(config_path=args.config, proposals_path=args.proposals)
        return 0
    except Exception as e:
        logger.critical(f"Validation failed: {e}")
        return 1


if __name__ == "__main__":
    # Initialize logging for standalone execution
    from utils.logging_config import initialize_pipeline_logging
    initialize_pipeline_logging()
    exit(main())
