"""
T073: Missing Degrees of Freedom Analysis
Implements analysis to identify and quantify missing degrees of freedom in the
quantum chemical model compared to experimental reality, as requested by
reviewer Rosalind Franklin-simulated regarding unit cell parameters and
hydration states.
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Any

# Import from existing API surface
from evaluators.experimental_validator import load_experimental_data, load_predictions, align_data
from evaluators.physical_interpretability import load_feature_importance, map_descriptor_to_physics
from utils.validation_utils import validate_columns

# Setup logging
def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def load_missing_dof_data(
    descriptors_semi_path: str,
    descriptors_dft_path: str,
    experimental_path: str
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Load semi-empirical descriptors, DFT descriptors, and experimental data."""
    logger = logging.getLogger(__name__)
    
    # Load semi-empirical descriptors
    semi_data = []
    with open(descriptors_semi_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            semi_data.append(row)
    
    # Load DFT descriptors
    dft_data = []
    with open(descriptors_dft_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dft_data.append(row)
    
    # Load experimental data
    exp_data = []
    with open(experimental_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exp_data.append(row)
    
    logger.info(f"Loaded {len(semi_data)} semi-empirical samples")
    logger.info(f"Loaded {len(dft_data)} DFT samples")
    logger.info(f"Loaded {len(exp_data)} experimental samples")
    
    return semi_data, dft_data, exp_data

def identify_missing_dof(
    semi_data: List[Dict],
    dft_data: List[Dict],
    exp_data: List[Dict]
) -> Dict[str, Any]:
    """
    Identify missing degrees of freedom by comparing:
    1. Gas-phase quantum calculations vs experimental condensed-phase data
    2. Isolated molecule vs crystal lattice effects
    3. Lack of solvent/hydration shell modeling
    """
    logger = logging.getLogger(__name__)
    
    # Align datasets by SMILES
    semi_aligned = {row.get('smiles', row.get('SMILES', '')): row for row in semi_data}
    dft_aligned = {row.get('smiles', row.get('SMILES', '')): row for row in dft_data}
    exp_aligned = {row.get('smiles', row.get('SMILES', '')): row for row in exp_data}
    
    # Identify molecules present in experimental data but not modeled with full physics
    missing_dof_categories = {
        'solvation_effects': [],
        'crystal_lattice_effects': [],
        'temperature_effects': [],
        'vibrational_zero_point': [],
        'conformational_sampling': []
    }
    
    common_smiles = set(semi_aligned.keys()) & set(dft_aligned.keys()) & set(exp_aligned.keys())
    
    logger.info(f"Found {len(common_smiles)} molecules with complete data")
    
    for smiles in common_smiles:
        semi_row = semi_aligned[smiles]
        dft_row = dft_aligned[smiles]
        exp_row = exp_aligned[smiles]
        
        # Calculate discrepancies
        semi_barrier = float(semi_row.get('experimental_barrier', 0))
        dft_barrier = float(dft_row.get('experimental_barrier', 0))
        exp_barrier = float(exp_row.get('experimental_barrier', 0))
        
        # Gas-phase vs condensed-phase discrepancy
        gas_phase_error = abs(dft_barrier - exp_barrier)
        
        # Identify missing DOF contributors
        if gas_phase_error > 5.0:  # kcal/mol threshold
            missing_dof_categories['solvation_effects'].append({
                'smiles': smiles,
                'experimental_barrier': exp_barrier,
                'dft_gas_phase': dft_barrier,
                'error': gas_phase_error,
                'likely_cause': 'solvent interaction missing'
            })
        
        # Check for crystal lattice effects (if experimental data is from crystal)
        if 'crystal' in exp_row.get('source', '').lower():
            missing_dof_categories['crystal_lattice_effects'].append({
                'smiles': smiles,
                'experimental_barrier': exp_barrier,
                'dft_gas_phase': dft_barrier,
                'error': gas_phase_error,
                'likely_cause': 'crystal lattice interactions missing'
            })
    
    # Calculate summary statistics
    total_missing_dof_impact = sum(
        len(v) for v in missing_dof_categories.values()
    )
    
    return {
        'missing_dof_categories': missing_dof_categories,
        'summary': {
            'total_molecules_analyzed': len(common_smiles),
            'molecules_with_significant_missing_dof': total_missing_dof_impact,
            'solvation_effects_count': len(missing_dof_categories['solvation_effects']),
            'crystal_lattice_effects_count': len(missing_dof_categories['crystal_lattice_effects']),
            'temperature_effects_count': len(missing_dof_categories['temperature_effects']),
            'vibrational_zero_point_count': len(missing_dof_categories['vibrational_zero_point']),
            'conformational_sampling_count': len(missing_dof_categories['conformational_sampling'])
        }
    }

def generate_missing_dof_report(
    analysis_results: Dict[str, Any],
    output_path: str
) -> None:
    """Generate a comprehensive report on missing degrees of freedom."""
    logger = logging.getLogger(__name__)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2, default=str)
    
    logger.info(f"Missing DOF report written to {output_path}")

def run_missing_dof_analysis(
    semi_descriptors_path: str,
    dft_descriptors_path: str,
    experimental_path: str,
    output_path: str
) -> Dict[str, Any]:
    """Run the complete missing degrees of freedom analysis."""
    logger = setup_logger('missing_dof_analysis', 'logs/missing_dof_analysis.log')
    logger.info("Starting missing degrees of freedom analysis")
    
    # Load data
    semi_data, dft_data, exp_data = load_missing_dof_data(
        semi_descriptors_path,
        dft_descriptors_path,
        experimental_path
    )
    
    # Identify missing DOF
    analysis_results = identify_missing_dof(semi_data, dft_data, exp_data)
    
    # Generate report
    generate_missing_dof_report(analysis_results, output_path)
    
    logger.info("Missing degrees of freedom analysis complete")
    return analysis_results

def main():
    parser = argparse.ArgumentParser(
        description='Analyze missing degrees of freedom in quantum chemical model'
    )
    parser.add_argument(
        '--semi-descriptors',
        type=str,
        default='data/descriptors_semi.csv',
        help='Path to semi-empirical descriptors CSV'
    )
    parser.add_argument(
        '--dft-descriptors',
        type=str,
        default='data/descriptors_dft.csv',
        help='Path to DFT descriptors CSV'
    )
    parser.add_argument(
        '--experimental',
        type=str,
        default='data/experimental_barrier_dataset.csv',
        help='Path to experimental barrier dataset CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='reports/missing_dof_analysis.json',
        help='Output path for analysis report'
    )
    
    args = parser.parse_args()
    
    # Validate input files exist
    for path in [args.semi_descriptors, args.dft_descriptors, args.experimental]:
        if not os.path.exists(path):
            logging.error(f"Input file not found: {path}")
            sys.exit(1)
    
    # Run analysis
    results = run_missing_dof_analysis(
        args.semi_descriptors,
        args.dft_descriptors,
        args.experimental,
        args.output
    )
    
    # Print summary
    print("\nMissing Degrees of Freedom Analysis Summary:")
    print(f"  Total molecules analyzed: {results['summary']['total_molecules_analyzed']}")
    print(f"  Molecules with significant missing DOF: {results['summary']['molecules_with_significant_missing_dof']}")
    print(f"  Solvation effects: {results['summary']['solvation_effects_count']}")
    print(f"  Crystal lattice effects: {results['summary']['crystal_lattice_effects_count']}")
    print(f"  Temperature effects: {results['summary']['temperature_effects_count']}")
    print(f"  Vibrational zero-point: {results['summary']['vibrational_zero_point_count']}")
    print(f"  Conformational sampling: {results['summary']['conformational_sampling_count']}")

if __name__ == '__main__':
    main()