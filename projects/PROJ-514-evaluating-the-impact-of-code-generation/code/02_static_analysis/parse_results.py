"""
Parse PMD CLI raw output (XML/JSON) into structured analysis results.

This module implements T022: Parse PMD XML/JSON output into data/intermediate/analysis_results.json.
It maps PMD violations to SmellMetric entities defined in code/utils/data_models.py.

Dependencies:
    - code/02_static_analysis/run_pmd.py (produces raw XML/JSON output)
    - code/utils/data_models.py (SmellMetric definition)
    - code/utils/logger.py (logging infrastructure)
"""

import os
import sys
import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_models import SmellMetric
from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)


def load_pmd_raw_results(raw_output_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load raw PMD output from a file. Handles both XML and JSON formats.

    Args:
        raw_output_path: Path to the raw PMD output file.

    Returns:
        Parsed data as a dictionary, or None if loading fails.
    """
    if not raw_output_path.exists():
        logger.error(f"Raw PMD output file not found: {raw_output_path}")
        return None

    try:
        suffix = raw_output_path.suffix.lower()
        with open(raw_output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if suffix == '.json':
            return json.loads(content)
        elif suffix == '.xml':
            # Parse XML and convert to a dictionary structure
            root = ET.fromstring(content)
            return _xml_to_dict(root)
        else:
            # Try JSON first, fallback to XML
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                root = ET.fromstring(content)
                return _xml_to_dict(root)

    except ET.ParseError as e:
        logger.error(f"Failed to parse XML from {raw_output_path}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {raw_output_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading {raw_output_path}: {e}")
        return None


def _xml_to_dict(element: ET.Element) -> Dict[str, Any]:
    """
    Convert an XML element to a nested dictionary.

    Args:
        element: The root XML element.

    Returns:
        Dictionary representation of the XML.
    """
    result = {}
    # Add attributes
    if element.attrib:
        result['@attributes'] = element.attrib
    
    # Add children
    for child in element:
        child_data = _xml_to_dict(child)
        if child.tag in result:
            # If tag already exists, convert to list
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data
    
    # Add text if present and no children
    if element.text and element.text.strip():
        if result:
            result['#text'] = element.text.strip()
        else:
            return element.text.strip()
    
    return result


def map_smell_type(pmd_rule: str) -> Optional[str]:
    """
    Map PMD rule names to our standard smell categories.

    Mapping based on PMD rulesets for:
    - LongMethod
    - DuplicatedCode
    - FeatureEnvy
    - LongParameterList

    Args:
        pmd_rule: The PMD rule name (e.g., 'LongMethod', 'ExcessiveParameterList').

    Returns:
        Standardized smell type string, or None if unmapped.
    """
    mapping = {
        # Long Method
        'LongMethod': 'LongMethod',
        'LongMethod': 'LongMethod',
        
        # Duplicated Code
        'DuplicateCode': 'DuplicatedCode',
        'CodeClone': 'DuplicatedCode',
        'DuplicatedCode': 'DuplicatedCode',
        
        # Feature Envy
        'FeatureEnvy': 'FeatureEnvy',
        
        # Long Parameter List
        'ExcessiveParameterList': 'LongParameterList',
        'LongParameterList': 'LongParameterList',
    }
    
    return mapping.get(pmd_rule)


def parse_violations(pmd_data: Dict[str, Any], file_path: str) -> List[SmellMetric]:
    """
    Parse violations from PMD output into SmellMetric objects.

    Args:
        pmd_data: Parsed PMD output (dictionary).
        file_path: The file path that was analyzed.

    Returns:
        List of SmellMetric objects representing detected smells.
    """
    metrics = []
    
    # Handle different PMD output structures
    violations = []
    
    if isinstance(pmd_data, dict):
        # Try common keys for violations
        if 'pmd' in pmd_data:
            pmd_root = pmd_data['pmd']
            if 'file' in pmd_root:
                file_data = pmd_root['file']
                if isinstance(file_data, list):
                    for f in file_data:
                        if 'violation' in f:
                            violations.extend(f['violation'])
                elif isinstance(file_data, dict) and 'violation' in file_data:
                    v = file_data['violation']
                    violations.append(v if isinstance(v, list) else [v])
            elif 'violation' in pmd_root:
                violations.extend(pmd_root['violation'])
        elif 'violations' in pmd_data:
            violations = pmd_data['violations']
        elif 'violation' in pmd_data:
            v = pmd_data['violation']
            violations.append(v if isinstance(v, list) else [v])
    
    # Flatten if necessary
    if violations and not isinstance(violations[0], dict):
        violations = [violations]
    
    for violation in violations:
        if not isinstance(violation, dict):
            continue
        
        # Extract rule name
        rule_name = violation.get('@attributes', {}).get('ruleset') or violation.get('ruleset')
        if not rule_name:
            rule_name = violation.get('rule', {}).get('@attributes', {}).get('name') or violation.get('rule', {}).get('name')
        
        # Try to get rule name directly if structure is flat
        if not rule_name and 'rule' in violation:
            rule_name = violation['rule']
        
        # Extract specific rule name from attributes or text
        specific_rule = violation.get('@attributes', {}).get('rule')
        if not specific_rule and 'rule' in violation:
            rule_obj = violation['rule']
            if isinstance(rule_obj, dict):
                specific_rule = rule_obj.get('@attributes', {}).get('name') or rule_obj.get('name')
            else:
                specific_rule = str(rule_obj)
        
        # If still no specific rule, try to extract from the violation dict itself
        if not specific_rule:
            for key in ['rule', 'rule_name', 'name']:
                if key in violation:
                    specific_rule = violation[key]
                    if isinstance(specific_rule, dict):
                        specific_rule = specific_rule.get('@attributes', {}).get('name') or specific_rule.get('name')
                    break
        
        # Fallback: use any key that looks like a rule name
        if not specific_rule:
            for key in violation:
                if key not in ['@attributes', '#text', 'violation', 'file', 'pmd', 'ruleset', 'rule']:
                    specific_rule = key
                    break
        
        if not specific_rule:
            continue
        
        smell_type = map_smell_type(specific_rule)
        if not smell_type:
            logger.debug(f"Skipping unmapped rule: {specific_rule}")
            continue
        
        # Extract location info
        line = violation.get('@attributes', {}).get('beginline') or violation.get('@attributes', {}).get('line')
        if line:
            line = int(line)
        
        # Extract description or message
        description = violation.get('#text') or violation.get('description', {}).get('#text') or violation.get('@attributes', {}).get('message')
        if not description and isinstance(violation, dict):
            for key in violation:
                if key not in ['@attributes', 'rule', 'ruleset']:
                    val = violation[key]
                    if isinstance(val, dict):
                        description = val.get('#text') or val.get('description', {}).get('#text')
                    elif isinstance(val, str):
                        description = val
                    if description:
                        break
        
        # Create SmellMetric
        metric = SmellMetric(
            sample_id=Path(file_path).stem,
            smell_type=smell_type,
            count=1,
            threshold_used="PMD-default",
            continuous_metric_value=1.0,
            line_number=line,
            description=description,
            file_path=file_path
        )
        metrics.append(metric)
    
    return metrics


def aggregate_metrics_by_sample(raw_results: Dict[str, Path]) -> Dict[str, List[SmellMetric]]:
    """
    Aggregate metrics by sample file.

    Args:
        raw_results: Dictionary mapping sample_id to raw PMD output file path.

    Returns:
        Dictionary mapping sample_id to list of SmellMetric objects.
    """
    aggregated = {}
    
    for sample_id, raw_path in raw_results.items():
        pmd_data = load_pmd_raw_results(raw_path)
        if pmd_data is None:
            logger.warning(f"No data loaded for {sample_id}, skipping.")
            continue
        
        metrics = parse_violations(pmd_data, str(raw_path))
        if metrics:
            aggregated[sample_id] = metrics
        else:
            # Even if no violations, record the sample with zero metrics
            aggregated[sample_id] = []
    
    return aggregated


def generate_analysis_results(
    raw_results_dir: Path,
    output_path: Path,
    sample_id_prefix: str = "sample_"
) -> Dict[str, Any]:
    """
    Generate the final analysis results JSON file.

    Reads all raw PMD output files from a directory, parses them, and
    writes a consolidated JSON file with all smell metrics.

    Args:
        raw_results_dir: Directory containing raw PMD output files.
        output_path: Path for the output JSON file.
        sample_id_prefix: Prefix for sample IDs (to match file naming).

    Returns:
        Dictionary containing the generated analysis results.
    """
    if not raw_results_dir.exists():
        logger.error(f"Raw results directory not found: {raw_results_dir}")
        return {}
    
    # Collect all raw result files
    raw_files = {}
    for file in raw_results_dir.iterdir():
        if file.suffix in ['.xml', '.json']:
            # Derive sample_id from filename
            sample_id = file.stem
            raw_files[sample_id] = file
    
    logger.info(f"Found {len(raw_files)} raw result files.")
    
    # Aggregate metrics
    aggregated = aggregate_metrics_by_sample(raw_files)
    
    # Build output structure
    results = {
        "metadata": {
            "generated_at": str(Path(__file__).parent),
            "tool": "PMD",
            "smell_categories": ["LongMethod", "DuplicatedCode", "FeatureEnvy", "LongParameterList"],
            "total_samples_analyzed": len(aggregated),
            "total_violations": sum(len(v) for v in aggregated.values())
        },
        "samples": {}
    }
    
    for sample_id, metrics in aggregated.items():
        sample_data = {
            "sample_id": sample_id,
            "violation_count": len(metrics),
            "smells": []
        }
        
        for metric in metrics:
            sample_data["smells"].append({
                "smell_type": metric.smell_type,
                "count": metric.count,
                "threshold_used": metric.threshold_used,
                "continuous_metric_value": metric.continuous_metric_value,
                "line_number": metric.line_number,
                "description": metric.description,
                "file_path": metric.file_path
            })
        
        results["samples"][sample_id] = sample_data
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis results written to {output_path}")
    return results


def main():
    """Main entry point for parsing PMD results."""
    project_root = get_project_root()
    
    # Define paths
    raw_results_dir = project_root / "data" / "intermediate" / "pmd_raw"
    output_path = project_root / "data" / "intermediate" / "analysis_results.json"
    
    # Ensure raw results directory exists (create empty if not)
    raw_results_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Parsing PMD results from {raw_results_dir}")
    logger.info(f"Output will be written to {output_path}")
    
    # Run parsing
    results = generate_analysis_results(raw_results_dir, output_path)
    
    if not results:
        logger.warning("No results generated. Check if raw PMD files exist.")
        sys.exit(1)
    
    logger.info(f"Successfully processed {results['metadata']['total_samples_analyzed']} samples "
               f"with {results['metadata']['total_violations']} total violations.")


if __name__ == "__main__":
    main()
