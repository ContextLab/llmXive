"""
Gate Task T038: Validate trait data sufficiency.

This task implements the gate logic defined in T038:
1. Read target species from data/processed/post_qc_species_list.json
2. Read trait availability from data/processed/trait_fallback_summary.json
3. Compute missing fraction (species missing from BOTH primary and fallback)
4. If missing_fraction > 0.30:
   - Write data/manifests/human_input_needed.flag
   - Raise SystemExit with specific message
"""
import json
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> dict:
    """Load and parse a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(file_path: Path, data: dict) -> None:
    """Save data to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def check_trait_sufficiency(
    post_qc_path: Path,
    trait_summary_path: Path,
    threshold: float = 0.30
) -> dict:
    """
    Check if trait data is sufficient for analysis.

    Args:
        post_qc_path: Path to post_qc_species_list.json
        trait_summary_path: Path to trait_fallback_summary.json
        threshold: Maximum allowed missing fraction (default 0.30)

    Returns:
        Dictionary with gate results

    Raises:
        SystemExit: If missing_fraction > threshold
    """
    logger.info(f"Loading target species from: {post_qc_path}")
    post_qc_data = load_json_file(post_qc_path)
    
    # Extract target species list
    if isinstance(post_qc_data, list):
        target_species = [item.get('species', item) for item in post_qc_data]
    elif isinstance(post_qc_data, dict) and 'species' in post_qc_data:
        target_species = post_qc_data['species'] if isinstance(post_qc_data['species'], list) else [post_qc_data['species']]
    else:
        # Handle potential schema variations
        target_species = list(post_qc_data.keys()) if isinstance(post_qc_data, dict) else []
    
    total_species = len(target_species)
    logger.info(f"Found {total_species} target species")

    if total_species == 0:
        logger.warning("No target species found. Gate cannot proceed.")
        return {
            'gate_passed': False,
            'reason': 'No target species found',
            'missing_fraction': 1.0,
            'threshold': threshold
        }

    logger.info(f"Loading trait fallback summary from: {trait_summary_path}")
    trait_data = load_json_file(trait_summary_path)

    # Identify species missing from BOTH primary and fallback sources
    missing_species = []
    
    # Check primary source (TRY)
    primary_results = trait_data.get('primary_source_results', {})
    missing_from_try = trait_data.get('missing_from_try', [])
    
    # Check fallback results
    fallback_results = trait_data.get('fallback_results', {})
    
    # Determine which species have data in either source
    species_with_data = set()
    
    # Add species with primary data
    if isinstance(primary_results, dict):
        species_with_data.update(primary_results.keys())
    
    # Add species with fallback data
    if isinstance(fallback_results, dict):
        species_with_data.update(fallback_results.keys())
    
    # Also check if missing_from_try is populated but fallback found data
    # In trait_fallback.py, missing_from_try is updated if fallback finds data
    # So we need to check the actual fallback_results more carefully
    
    # Re-evaluate: species in missing_from_try that were NOT recovered by fallback
    # The trait_fallback_summary.json should have:
    # - primary_source_results: species that got data from TRY
    # - missing_from_try: species that didn't get data from TRY
    # - fallback_results: species that got data from fallback sources
    # - missing_from_all_sources: species that got data from neither (final list)
    
    # If missing_from_all_sources exists, use it directly
    if 'missing_from_all_sources' in trait_data:
        missing_species = trait_data['missing_from_all_sources']
        logger.info(f"Using missing_from_all_sources list: {len(missing_species)} species")
    else:
        # Fallback logic: species in missing_from_try that are NOT in fallback_results
        missing_species = [
            sp for sp in missing_from_try 
            if sp not in fallback_results
        ]
        logger.info(f"Calculated missing species: {len(missing_species)} species")

    missing_fraction = len(missing_species) / total_species
    
    logger.info(f"Missing fraction: {missing_fraction:.2%} ({len(missing_species)}/{total_species})")
    logger.info(f"Threshold: {threshold:.2%}")

    result = {
        'gate_passed': missing_fraction <= threshold,
        'missing_fraction': missing_fraction,
        'total_species': total_species,
        'missing_species_count': len(missing_species),
        'missing_species': missing_species,
        'threshold': threshold,
        'trait_summary_path': str(trait_summary_path),
        'post_qc_path': str(post_qc_path)
    }

    # Write gate report
    gate_report_path = post_qc_path.parent / 'trait_gate_report.json'
    save_json_file(gate_report_path, result)
    logger.info(f"Wrote gate report to: {gate_report_path}")

    if not result['gate_passed']:
        # Write human_input_needed.flag FIRST
        flag_path = post_qc_path.parent.parent / 'manifests' / 'human_input_needed.flag'
        flag_path.parent.mkdir(parents=True, exist_ok=True)
        
        flag_content = {
            'reason': 'Insufficient trait data',
            'missing_fraction': missing_fraction,
            'threshold': threshold,
            'missing_species': missing_species,
            'required_action': 'Acquire trait data for missing species or reduce scope'
        }
        
        with open(flag_path, 'w') as f:
            json.dump(flag_content, f, indent=2)
        
        logger.warning(f"Written human_input_needed.flag: {flag_path}")
        
        # Raise SystemExit with specific message
        error_msg = f"Insufficient trait data (missing > {threshold:.0%}): {missing_fraction:.2%} of {total_species} species missing traits"
        logger.error(error_msg)
        raise SystemExit(error_msg)

    logger.info("Gate PASSED: Sufficient trait data available")
    return result

def main():
    """Main entry point for the trait gate task."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    post_qc_path = project_root / 'data' / 'processed' / 'post_qc_species_list.json'
    trait_summary_path = project_root / 'data' / 'processed' / 'trait_fallback_summary.json'
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Post-QC species list: {post_qc_path}")
    logger.info(f"Trait summary: {trait_summary_path}")

    try:
        result = check_trait_sufficiency(
            post_qc_path=post_qc_path,
            trait_summary_path=trait_summary_path,
            threshold=0.30
        )
        
        # Print summary
        print("\n" + "="*60)
        print("TRAIT DATA GATE RESULTS")
        print("="*60)
        print(f"Total target species: {result['total_species']}")
        print(f"Missing species: {result['missing_species_count']}")
        print(f"Missing fraction: {result['missing_fraction']:.2%}")
        print(f"Threshold: {result['threshold']:.2%}")
        print(f"Gate status: {'PASSED' if result['gate_passed'] else 'FAILED'}")
        print("="*60 + "\n")
        
        return 0

    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        return 1
    except SystemExit as e:
        # Re-raise SystemExit to halt pipeline
        raise
    except Exception as e:
        logger.error(f"Unexpected error during gate check: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == '__main__':
    sys.exit(main())
