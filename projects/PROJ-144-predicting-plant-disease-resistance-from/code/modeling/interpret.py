"""
T043: Verify KEGG API fallback/retry in code/modeling/interpret.py (Integrated into T026b).

This module implements the pathway mapping logic with robust retry mechanisms and
fallback strategies as specified in T026b and T043.
"""
import os
import sys
import json
import pickle
import logging
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
KEGG_BASE_URL = "https://rest.kegg.jp"
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 10.0  # seconds
RETRY_MULTIPLIER = 2

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Required input file missing: {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        raise

def save_json_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    output_dir = os.path.dirname(filepath)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_top_metabolites(filepath: str) -> List[Dict[str, Any]]:
    """Load top metabolites from the feature importance ranking."""
    data = load_json_file(filepath)
    # Ensure we have a list of metabolites with at least name and importance
    if 'metabolites' in data:
        return data['metabolites']
    elif isinstance(data, list):
        return data
    else:
        logger.warning("Unexpected format in top_metabolites.json, attempting to adapt")
        return [data] if isinstance(data, dict) else []

def fetch_kegg_metabolite(inchikey: str) -> Optional[Dict[str, Any]]:
    """
    Fetch metabolite information from KEGG API using InChIKey.
    Implements retry logic with exponential backoff.
    
    Args:
        inchikey: The InChIKey of the metabolite
        
    Returns:
        Dictionary with metabolite info or None if failed
    """
    url = f"{KEGG_BASE_URL}/find/compound/{inchikey}"
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.debug(f"Attempt {attempt}/{MAX_RETRIES} for KEGG lookup: {inchikey}")
            req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-PlantDiseaseResistance/1.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    result = response.read().decode('utf-8').strip()
                    # KEGG returns "ENTRY\t<entry_id>\n..." or just the entry ID
                    if result and not result.startswith("ERROR"):
                        # Parse the response to extract compound ID
                        lines = result.split('\n')
                        entry_line = next((l for l in lines if l.startswith('ENTRY')), None)
                        if entry_line:
                            parts = entry_line.split()
                            if len(parts) >= 2:
                                compound_id = parts[1]
                                return {"compound_id": compound_id, "raw_entry": result}
                        return {"compound_id": result.split()[0] if result else None, "raw_entry": result}
                
        except urllib.error.URLError as e:
            logger.warning(f"URLError for {inchikey} (attempt {attempt}): {e}")
        except urllib.error.HTTPError as e:
            logger.warning(f"HTTPError {e.code} for {inchikey} (attempt {attempt})")
        except Exception as e:
            logger.warning(f"Unexpected error for {inchikey} (attempt {attempt}): {e}")
        
        if attempt < MAX_RETRIES:
            delay = min(BASE_DELAY * (RETRY_MULTIPLIER ** (attempt - 1)), MAX_DELAY)
            logger.info(f"Retrying in {delay:.1f}s...")
            time.sleep(delay)
    
    logger.error(f"Failed to fetch KEGG data for {inchikey} after {MAX_RETRIES} attempts")
    return None

def fetch_kegg_compound_info(compound_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed compound information given a compound ID.
    
    Args:
        compound_id: KEGG compound ID (e.g., C00001)
        
    Returns:
        Dictionary with detailed info or None
    """
    url = f"{KEGG_BASE_URL}/get/{compound_id}"
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-PlantDiseaseResistance/1.0'})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    result = response.read().decode('utf-8')
                    return parse_kegg_entry(result)
                
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            logger.warning(f"Error fetching compound info for {compound_id} (attempt {attempt}): {e}")
        except Exception as e:
            logger.warning(f"Unexpected error for {compound_id} (attempt {attempt}): {e}")
        
        if attempt < MAX_RETRIES:
            delay = min(BASE_DELAY * (RETRY_MULTIPLIER ** (attempt - 1)), MAX_DELAY)
            time.sleep(delay)
    
    return None

def parse_kegg_entry(entry_text: str) -> Dict[str, Any]:
    """
    Parse a KEGG entry text block into a structured dictionary.
    
    Args:
        entry_text: Raw KEGG entry text
        
    Returns:
        Parsed dictionary with fields like 'NAME', 'PATHWAY', 'FORMULA', etc.
    """
    parsed = {}
    lines = entry_text.split('\n')
    current_field = None
    current_value = []
    
    for line in lines:
        if not line.strip():
            continue
        
        # Check if this is a new field (starts with a keyword like NAME, PATHWAY, etc.)
        if re.match(r'^[A-Z]+\s', line):
            # Save previous field
            if current_field:
                parsed[current_field] = '\n'.join(current_value).strip()
            
            # Start new field
            parts = line.split(None, 1)
            current_field = parts[0]
            current_value = [parts[1].strip()] if len(parts) > 1 else []
        else:
            # Continuation of current field
            if current_field:
                current_value.append(line.strip())
    
    # Save last field
    if current_field:
        parsed[current_field] = '\n'.join(current_value).strip()
    
    return parsed

def map_metabolite_to_pathways(metabolite_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Map a metabolite to its pathways using KEGG data.
    
    Args:
        metabolite_info: Dictionary with metabolite details (may include compound_id)
        
    Returns:
        List of pathway mappings
    """
    pathways = []
    compound_id = metabolite_info.get('compound_id')
    
    if not compound_id:
        logger.warning(f"No compound_id found for metabolite: {metabolite_info.get('name', 'unknown')}")
        return pathways
    
    # Fetch detailed info if we don't have it
    if 'pathway' not in metabolite_info:
        detailed_info = fetch_kegg_compound_info(compound_id)
        if detailed_info:
            metabolite_info.update(detailed_info)
    
    # Extract pathway information
    pathway_str = metabolite_info.get('PATHWAY', '')
    if pathway_str:
        # Parse pathway entries (format: "path:ko00010  Glycolysis / Gluconeogenesis ...")
        for line in pathway_str.split('\n'):
            if line.startswith('path:'):
                parts = line.split(None, 1)
                if len(parts) >= 2:
                    pathway_id = parts[0]
                    pathway_name = parts[1]
                    pathways.append({
                        'pathway_id': pathway_id,
                        'pathway_name': pathway_name,
                        'source': 'KEGG'
                    })
    
    return pathways

def enrich_metabolite_info(metabolite: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a metabolite entry with KEGG pathway information.
    
    Args:
        metabolite: Dictionary with metabolite details
        
    Returns:
        Enriched dictionary with pathway mappings
    """
    result = metabolite.copy()
    
    # Try to get InChIKey from various possible fields
    inchikey = None
    for key in ['inchikey', 'InChIKey', 'inchi_key', 'InChI_Key', 'inchi']:
        if key in metabolite:
            inchikey = str(metabolite[key])
            break
    
    if inchikey:
        # Normalize InChIKey (remove extra spaces, etc.)
        inchikey = inchikey.strip()
        
        # Fetch KEGG data
        kegg_data = fetch_kegg_metabolite(inchikey)
        if kegg_data:
            result['kegg_data'] = kegg_data
            result['compound_id'] = kegg_data.get('compound_id')
            
            # Map to pathways
            pathways = map_metabolite_to_pathways(result)
            result['pathways'] = pathways
            result['mapping_success'] = len(pathways) > 0
        else:
            result['mapping_success'] = False
            result['mapping_error'] = f"Failed to fetch KEGG data for InChIKey: {inchikey}"
    else:
        result['mapping_success'] = False
        result['mapping_error'] = "No InChIKey found for metabolite"
    
    return result

def generate_narrative_report(pathway_analysis: Dict[str, Any]) -> str:
    """
    Generate a narrative report from pathway analysis results.
    
    Args:
        pathway_analysis: Full pathway analysis dictionary
        
    Returns:
        Narrative report string
    """
    report_lines = [
        "# Pathway Analysis Report",
        "",
        "## Overview",
        "",
        f"This report summarizes the pathway mappings for the top metabolites identified",
        f"in the plant disease resistance prediction model.",
        "",
        f"Total metabolites analyzed: {len(pathway_analysis.get('metabolite_mappings', []))}",
        f"Successfully mapped: {sum(1 for m in pathway_analysis.get('metabolite_mappings', []) if m.get('mapping_success'))}",
        f"Mapping success rate: {pathway_analysis.get('mapping_success_rate', 0):.1%}",
        "",
        "## Key Findings",
        ""
    ]
    
    # Group by pathway
    pathway_counts = {}
    for mapping in pathway_analysis.get('metabolite_mappings', []):
        for pathway in mapping.get('pathways', []):
            pid = pathway['pathway_id']
            pathway_counts[pid] = pathway_counts.get(pid, 0) + 1
    
    # Sort pathways by frequency
    sorted_pathways = sorted(pathway_counts.items(), key=lambda x: x[1], reverse=True)
    
    if sorted_pathways:
        report_lines.append("The most frequently associated pathways are:")
        report_lines.append("")
        for pid, count in sorted_pathways[:5]:
            # Extract pathway name from ID if possible
            name = pid.split(':')[1] if ':' in pid else pid
            report_lines.append(f"- **{name}**: Associated with {count} metabolite(s)")
        report_lines.append("")
    else:
        report_lines.append("No pathway associations were identified.")
        report_lines.append("")
    
    report_lines.extend([
        "## Limitations",
        "",
        "These findings represent statistical associations between pre-challenge metabolite profiles",
        "and disease resistance phenotypes. No causal claims are made.",
        "",
        "Pathway mapping relies on the availability of InChIKeys and their presence in the KEGG database.",
        "Some metabolites may not have been mapped due to missing identifiers or database limitations.",
        ""
    ])
    
    return "\n".join(report_lines)

def save_pathway_analysis(output_path: str, metabolite_mappings: List[Dict[str, Any]], success_rate: float) -> None:
    """
    Save the complete pathway analysis to a JSON file.
    
    Args:
        output_path: Path to the output JSON file
        metabolite_mappings: List of enriched metabolite dictionaries
        success_rate: Overall mapping success rate
    """
    analysis = {
        'metabolite_mappings': metabolite_mappings,
        'mapping_success_rate': success_rate,
        'total_metabolites': len(metabolite_mappings),
        'mapped_metabolites': sum(1 for m in metabolite_mappings if m.get('mapping_success')),
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    save_json_file(output_path, analysis)
    logger.info(f"Pathway analysis saved to {output_path}")

def main():
    """Main entry point for pathway interpretation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Interpret model results via pathway mapping')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to top_metabolites.json (or other input with metabolite list)')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output pathway_analysis.json')
    args = parser.parse_args()
    
    logger.info("Starting T043: Verifying KEGG API fallback/retry in pathway interpretation")
    
    # Load top metabolites
    try:
        top_metabolites = load_top_metabolites(args.input)
        logger.info(f"Loaded {len(top_metabolites)} top metabolites")
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading input file: {e}")
        sys.exit(1)
    
    # Enrich each metabolite with KEGG data
    metabolite_mappings = []
    success_count = 0
    
    for i, metabolite in enumerate(top_metabolites):
        logger.info(f"Processing metabolite {i+1}/{len(top_metabolites)}: {metabolite.get('name', 'unknown')}")
        enriched = enrich_metabolite_info(metabolite)
        metabolite_mappings.append(enriched)
        if enriched.get('mapping_success'):
            success_count += 1
        
        # Small delay to avoid rate limiting
        if i < len(top_metabolites) - 1:
            time.sleep(0.5)
    
    # Calculate success rate
    success_rate = success_count / len(top_metabolites) if top_metabolites else 0.0
    
    # Save pathway analysis
    save_pathway_analysis(args.output, metabolite_mappings, success_rate)
    
    # Generate and save narrative report
    analysis_data = {
        'metabolite_mappings': metabolite_mappings,
        'mapping_success_rate': success_rate
    }
    narrative = generate_narrative_report(analysis_data)
    
    # Save narrative report
    report_path = str(Path(args.output).with_suffix('.md'))
    with open(report_path, 'w') as f:
        f.write(narrative)
    logger.info(f"Narrative report saved to {report_path}")
    
    logger.info(f"Pathway mapping complete. Success rate: {success_rate:.1%}")
    
    # Log warnings if success rate is low
    if success_rate < 0.5:
        logger.warning(f"Low mapping success rate ({success_rate:.1%}). Consider checking InChIKey quality.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
