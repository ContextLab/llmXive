import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_power_analysis_with_literature(
    current_analysis: Dict[str, Any],
    literature_estimates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update the current power analysis with refined values from literature estimates.
    
    Args:
        current_analysis: The existing power analysis dictionary.
        literature_estimates: The parsed literature estimates dictionary.
        
    Returns:
        The updated power analysis dictionary.
    """
    updated_analysis = current_analysis.copy()
    
    # Update variance if available in literature estimates
    if 'variance' in literature_estimates:
        logger.info(f"Updating variance from {current_analysis.get('expected_variance')} "
                   f"to {literature_estimates['variance']} based on literature.")
        updated_analysis['expected_variance'] = literature_estimates['variance']
        updated_analysis['variance_source'] = 'empirical_literature'
    
    # Update effect size if available in literature estimates
    if 'effect_size' in literature_estimates:
        logger.info(f"Updating effect size from {current_analysis.get('effect_size')} "
                   f"to {literature_estimates['effect_size']} based on literature.")
        updated_analysis['effect_size'] = literature_estimates['effect_size']
    
    # Recalculate recommended sample size if variance or effect_size changed
    if 'variance' in literature_estimates or 'effect_size' in literature_estimates:
        # Simple power analysis formula for sample size estimation:
        # n = 2 * (Z_alpha + Z_beta)^2 * variance / effect_size^2
        # Using standard values: Z_alpha (95% CI) = 1.96, Z_beta (80% power) = 0.84
        import math
        
        variance = updated_analysis.get('expected_variance', 1.0)
        effect_size = updated_analysis.get('effect_size', 0.5)
        
        if effect_size > 0:
            z_alpha = 1.96  # 95% confidence level
            z_beta = 0.84   # 80% power
            numerator = 2 * ((z_alpha + z_beta) ** 2) * variance
            denominator = effect_size ** 2
            new_sample_size = int(math.ceil(numerator / denominator))
            
            logger.info(f"Recalculated recommended sample size: {new_sample_size}")
            updated_analysis['recommended_sample_size'] = new_sample_size
            updated_analysis['recalculation_reason'] = 'updated_with_literature'
        else:
            logger.warning("Effect size is zero or negative, skipping sample size recalculation.")
    
    # Add metadata about the update
    updated_analysis['last_updated'] = 'literature_update'
    updated_analysis['literature_source'] = literature_estimates.get('source', 'unknown')
    
    return updated_analysis

def save_power_analysis(data: Dict[str, Any], file_path: Path) -> None:
    """Save the power analysis dictionary to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved updated power analysis to {file_path}")

def main():
    """Main entry point for updating power analysis with literature estimates."""
    parser = argparse.ArgumentParser(
        description='Update power analysis with literature estimates.'
    )
    parser.add_argument(
        '--current-analysis',
        type=str,
        default='data/metrics/power_analysis_initial.json',
        help='Path to the current power analysis JSON file.'
    )
    parser.add_argument(
        '--literature-estimates',
        type=str,
        default='data/metrics/literature_estimates.json',
        help='Path to the literature estimates JSON file.'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/metrics/power_analysis_initial.json',
        help='Path to save the updated power analysis JSON file.'
    )
    
    args = parser.parse_args()
    
    current_analysis_path = Path(args.current_analysis)
    literature_estimates_path = Path(args.literature_estimates)
    output_path = Path(args.output)
    
    # Check if required files exist
    if not current_analysis_path.exists():
        logger.error(f"Current power analysis file not found: {current_analysis_path}")
        sys.exit(1)
    
    if not literature_estimates_path.exists():
        logger.error(f"Literature estimates file not found: {literature_estimates_path}")
        sys.exit(1)
    
    try:
        # Load the current power analysis
        logger.info(f"Loading current power analysis from {current_analysis_path}")
        current_analysis = load_json_file(current_analysis_path)
        
        # Load the literature estimates
        logger.info(f"Loading literature estimates from {literature_estimates_path}")
        literature_estimates = load_json_file(literature_estimates_path)
        
        # Update the power analysis
        logger.info("Updating power analysis with literature estimates...")
        updated_analysis = update_power_analysis_with_literature(
            current_analysis, 
            literature_estimates
        )
        
        # Save the updated analysis
        save_power_analysis(updated_analysis, output_path)
        
        logger.info("Power analysis update completed successfully.")
        
    except Exception as e:
        logger.error(f"Error updating power analysis: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
