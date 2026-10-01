"""
Generate the final interpretability report for feature importance.

This script reads the SHAP analysis and permutation importance results,
maps top bits to substructures, and generates a Markdown report listing
the top bits, their scores, substructures, and collision warnings.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path_results, get_path_validation, ensure_directory
from logging_config import setup_logging, get_logger

# Configure logger
logger = get_logger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def load_shap_analysis() -> Dict[str, Any]:
    """Load SHAP analysis results."""
    shap_path = get_path_results("shap_analysis.json")
    logger.info(f"Loading SHAP analysis from: {shap_path}")
    return load_json_file(shap_path)

def load_permutation_importance() -> Dict[str, Any]:
    """Load permutation importance results."""
    perm_path = get_path_results("permutation_importance.json")
    logger.info(f"Loading permutation importance from: {perm_path}")
    return load_json_file(perm_path)

def load_substructure_mapping() -> Dict[str, Any]:
    """Load substructure mapping results."""
    mapping_path = get_path_results("substructure_mapping.json")
    logger.info(f"Loading substructure mapping from: {mapping_path}")
    return load_json_file(mapping_path)

def merge_importance_scores(
    shap_data: Dict[str, Any], 
    perm_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Merge SHAP and permutation importance scores into a unified list.
    
    Prioritize SHAP mean absolute values as the primary score,
    supplementing with permutation importance where available.
    """
    # Extract SHAP mean absolute values for RF model (Space Group classification)
    shap_rf = shap_data.get("rf_model", {}).get("shap_values", [])
    shap_scores = {}
    for item in shap_rf:
        bit_idx = item.get("feature_index")
        mean_abs = item.get("mean_abs_shap_value", 0.0)
        shap_scores[bit_idx] = {
            "shap_mean_abs": mean_abs,
            "source": "SHAP"
        }
    
    # Extract permutation importance
    perm_scores = perm_data.get("rf_model", {}).get("importance", [])
    for item in perm_scores:
        bit_idx = item.get("feature_index")
        score = item.get("importance", 0.0)
        
        if bit_idx in shap_scores:
            # Combine scores: use SHAP as primary, add permutation as secondary
            shap_scores[bit_idx]["perm_importance"] = score
            shap_scores[bit_idx]["source"] = "SHAP + Permutation"
        else:
            shap_scores[bit_idx] = {
                "perm_importance": score,
                "source": "Permutation"
            }
    
    # Convert to list and sort by SHAP mean_abs (primary) or perm_importance (secondary)
    merged_list = []
    for bit_idx, scores in shap_scores.items():
        primary_score = scores.get("shap_mean_abs", scores.get("perm_importance", 0.0))
        merged_list.append({
            "feature_index": bit_idx,
            "primary_score": primary_score,
            "scores": scores
        })
    
    # Sort by primary score descending
    merged_list.sort(key=lambda x: x["primary_score"], reverse=True)
    
    return merged_list

def map_substructures(
    importance_list: List[Dict[str, Any]], 
    mapping_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Map substructures to top bits from importance list.
    
    Returns enriched list with substructure information and collision flags.
    """
    substructure_map = mapping_data.get("bit_to_substructure", {})
    result = []
    
    for item in importance_list:
        bit_idx = item["feature_index"]
        substructure_info = substructure_map.get(str(bit_idx), {})
        
        # Check for collisions (multiple possible mappings)
        collisions = substructure_info.get("collisions", False)
        collision_details = substructure_info.get("possible_mappings", [])
        
        enriched_item = {
            "feature_index": bit_idx,
            "primary_score": item["primary_score"],
            "scores": item["scores"],
            "substructure": substructure_info.get("primary_smiles", "Unknown"),
            "substructure_description": substructure_info.get("description", "Not mapped"),
            "has_collisions": collisions,
            "collision_count": len(collision_details) if collisions else 0,
            "collision_warnings": collision_details if collisions else []
        }
        
        result.append(enriched_item)
    
    return result

def generate_markdown_report(
    enriched_data: List[Dict[str, Any]], 
    output_path: Path
) -> None:
    """
    Generate a Markdown report with the top features, their scores,
    substructures, and collision warnings.
    """
    lines = []
    lines.append("# Feature Importance Report")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("This report lists the top fingerprint bits identified as important")
    lines.append("for predicting crystal structures from molecular fingerprints.")
    lines.append("Features are sorted by importance score (SHAP mean absolute value).")
    lines.append("")
    lines.append("## Top Predictive Features")
    lines.append("")
    lines.append("| Rank | Bit Index | Importance Score | Substructure (SMILES) | Description | Collision Warning |")
    lines.append("|------|-----------|------------------|-----------------------|-------------|-------------------|")
    
    for rank, item in enumerate(enriched_data, 1):
        bit_idx = item["feature_index"]
        score = f"{item['primary_score']:.6f}"
        smiles = item["substructure"]
        description = item["substructure_description"]
        
        # Handle collision warnings
        if item["has_collisions"]:
            collision_note = f"⚠️ {item['collision_count']} possible mappings"
            # Add detailed warning in description if needed
            if len(item["collision_warnings"]) > 0:
                description += f" [See below for details]"
        else:
            collision_note = "None"
        
        # Escape pipe characters in description and smiles
        smiles = smiles.replace("|", "\\|")
        description = description.replace("|", "\\|")
        
        lines.append(f"| {rank} | {bit_idx} | {score} | `{smiles}` | {description} | {collision_note} |")
    
    lines.append("")
    lines.append("## Collision Details")
    lines.append("")
    lines.append("The following bits have multiple possible substructure mappings (collisions):")
    lines.append("")
    
    collision_items = [item for item in enriched_data if item["has_collisions"]]
    
    if not collision_items:
        lines.append("*No collisions detected.*")
    else:
        for item in collision_items:
            bit_idx = item["feature_index"]
            lines.append(f"### Bit {bit_idx}")
            lines.append("")
            lines.append("Possible substructures:")
            for i, mapping in enumerate(item["collision_warnings"], 1):
                mapping_smiles = mapping.get("smiles", "Unknown")
                mapping_desc = mapping.get("description", "No description")
                lines.append(f"{i}. `{mapping_smiles}` - {mapping_desc}")
            lines.append("")
    
    lines.append("## Methodology")
    lines.append("")
    lines.append("1. **SHAP Analysis**: Mean absolute SHAP values computed for the Random Forest model.")
    lines.append("2. **Permutation Importance**: Feature importance via permutation on the Random Forest model.")
    lines.append("3. **Substructure Mapping**: Top bits mapped to representative chemical substructures using RDKit.")
    lines.append("4. **Collision Detection**: Bits with multiple valid substructure mappings flagged as collisions.")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Features are sorted by importance score (descending).")
    lines.append("- Collision warnings indicate bits that may represent multiple chemical substructures.")
    lines.append("- The presence of collisions does not invalidate the feature's predictive power but suggests ambiguity in chemical interpretation.")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated at: {Path(__file__).stem} execution*")
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    
    logger.info(f"Report generated: {output_path}")

def validate_report(output_path: Path, min_bits: int = 20) -> bool:
    """
    Validate that the report contains at least min_bits annotated features.
    Returns True if validation passes, False otherwise.
    """
    if not output_path.exists():
        logger.error(f"Report file not found: {output_path}")
        return False
    
    with open(output_path, 'r') as f:
        content = f.read()
    
    # Count table rows (excluding header)
    lines = content.split('\n')
    table_start = None
    for i, line in enumerate(lines):
        if line.startswith("| Rank |"):
            table_start = i
            break
    
    if table_start is None:
        logger.error("Could not find table header in report")
        return False
    
    # Count data rows (lines starting with | and not being separator)
    data_rows = 0
    for line in lines[table_start + 1:]:
        if line.strip().startswith("|") and not line.strip().startswith("|---"):
            data_rows += 1
    
    if data_rows < min_bits:
        logger.warning(f"Report contains only {data_rows} features, expected at least {min_bits}")
        return False
    
    logger.info(f"Report validation passed: {data_rows} features found (min: {min_bits})")
    return True

def main():
    """Main entry point for report generation."""
    setup_logging()
    logger.info("Starting feature importance report generation")
    
    try:
        # Load required data
        shap_data = load_shap_analysis()
        perm_data = load_permutation_importance()
        mapping_data = load_substructure_mapping()
        
        # Merge importance scores
        importance_list = merge_importance_scores(shap_data, perm_data)
        
        # Map substructures
        enriched_data = map_substructures(importance_list, mapping_data)
        
        # Generate report
        report_path = get_path_results("feature_importance_report.md")
        generate_markdown_report(enriched_data, report_path)
        
        # Validate report
        if validate_report(report_path, min_bits=20):
            logger.info("Report generation and validation completed successfully")
        else:
            logger.warning("Report validation failed - check feature count")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during report generation: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())