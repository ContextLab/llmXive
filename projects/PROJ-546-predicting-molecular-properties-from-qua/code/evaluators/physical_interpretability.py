"""
Physical Interpretability Evaluator for Molecular Property Prediction.

This module traces top feature importance scores from Random Forest models back
to specific physical mechanisms (Feynman/Pauling review), ensuring that the
"top 5" descriptors correspond to known chemical invariants (e.g., resonance energy,
bond length, electronegativity) rather than statistical noise.

It implements a mapping from computational descriptors to their underlying
physical interpretations, validating that the model's decision logic aligns
with established chemical theory.
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import from project utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logging_utils import setup_logger

# Known chemical invariants and their physical interpretations
# Mapping from descriptor names to physical mechanisms
CHEMICAL_INVARIANTS = {
    # Electronic structure descriptors
    'homo_energy': {
        'mechanism': 'Ionization Potential / Electron Donating Ability',
        'theory': 'Frontier Molecular Orbital Theory (Fukui)',
        'description': 'Energy of the Highest Occupied Molecular Orbital; relates to the energy required to remove an electron.',
        'physical_constant': True,
        'units': 'eV'
    },
    'lumo_energy': {
        'mechanism': 'Electron Affinity / Electron Accepting Ability',
        'theory': 'Frontier Molecular Orbital Theory (Fukui)',
        'description': 'Energy of the Lowest Unoccupied Molecular Orbital; relates to the energy released when an electron is added.',
        'physical_constant': True,
        'units': 'eV'
    },
    'homo_lumo_gap': {
        'mechanism': 'Chemical Hardness / Reactivity',
        'theory': 'Conceptual DFT (Pearson)',
        'description': 'Energy difference between HOMO and LUMO; measures resistance to charge transfer and chemical stability.',
        'physical_constant': True,
        'units': 'eV'
    },
    'mulliken_charges': {
        'mechanism': 'Electrostatic Potential / Charge Distribution',
        'theory': 'Mulliken Population Analysis',
        'description': 'Atomic partial charges derived from electron density partitioning; indicates sites for nucleophilic/electrophilic attack.',
        'physical_constant': False,
        'units': 'e'
    },
    'dipole_moment': {
        'mechanism': 'Molecular Polarity',
        'theory': 'Classical Electrodynamics / Quantum Chemistry',
        'description': 'Vector sum of bond dipoles; measures charge separation and solvent interaction potential.',
        'physical_constant': True,
        'units': 'Debye'
    },
    # Geometric descriptors
    'bond_length_mean': {
        'mechanism': 'Bond Strength / Equilibrium Geometry',
        'theory': 'Morse Potential / Harmonic Oscillator',
        'description': 'Average bond length; inversely related to bond strength and force constants.',
        'physical_constant': True,
        'units': 'Angstrom'
    },
    'bond_angle_variance': {
        'mechanism': 'Molecular Rigidity / Steric Strain',
        'theory': 'Valence Shell Electron Pair Repulsion (VSEPR)',
        'description': 'Variation in bond angles; indicates steric strain and conformational flexibility.',
        'physical_constant': False,
        'units': 'degrees^2'
    },
    'molecular_volume': {
        'mechanism': 'Steric Bulk / Solvation Shell',
        'theory': 'Scaled Particle Theory',
        'description': 'Total molecular volume; affects packing, solvation, and steric hindrance.',
        'physical_constant': True,
        'units': 'Angstrom^3'
    },
    # Quantum chemical descriptors
    'total_energy': {
        'mechanism': 'Thermodynamic Stability',
        'theory': 'Born-Oppenheimer Approximation',
        'description': 'Total electronic energy; relates to the stability of the molecular configuration.',
        'physical_constant': True,
        'units': 'Hartree'
    },
    'zero_point_energy': {
        'mechanism': 'Quantum Zero-Point Motion',
        'theory': 'Heisenberg Uncertainty Principle',
        'description': 'Vibrational ground state energy; prevents molecular collapse at absolute zero.',
        'physical_constant': True,
        'units': 'Hartree'
    },
    'mayer_bond_order': {
        'mechanism': 'Bond Order / Covalency',
        'theory': 'Mayer Bond Order Analysis',
        'description': 'Quantitative measure of bond multiplicity; relates to bond strength and length.',
        'physical_constant': False,
        'units': 'dimensionless'
    },
    'electronegativity': {
        'mechanism': 'Electron Attraction Power',
        'theory': 'Mulliken Electronegativity / Conceptual DFT',
        'description': 'Average of HOMO and LUMO energies; measures tendency to attract electrons.',
        'physical_constant': True,
        'units': 'eV'
    },
    'chemical_hardness': {
        'mechanism': 'Resistance to Charge Transfer',
        'theory': 'Conceptual DFT (Pearson)',
        'description': 'Half the HOMO-LUMO gap; measures resistance to polarization and charge transfer.',
        'physical_constant': True,
        'units': 'eV'
    },
    'chemical_potential': {
        'mechanism': 'Electron Flow Driving Force',
        'theory': 'Conceptual DFT (Parr)',
        'description': 'Negative of electronegativity; drives electron flow from high to low potential.',
        'physical_constant': True,
        'units': 'eV'
    },
    'electrophilicity_index': {
        'mechanism': 'Electrophilic Power',
        'theory': 'Conceptual DFT (Parr)',
        'description': 'Measures the energy lowering due to maximal electron flow from reservoir to system.',
        'physical_constant': True,
        'units': 'eV'
    },
    # Topological descriptors
    'molecular_weight': {
        'mechanism': 'Mass / Inertia',
        'theory': 'Classical Mechanics',
        'description': 'Sum of atomic masses; affects diffusion, vibration frequencies, and kinetic isotope effects.',
        'physical_constant': True,
        'units': 'g/mol'
    },
    'rotatable_bonds': {
        'mechanism': 'Conformational Entropy',
        'theory': 'Statistical Mechanics',
        'description': 'Number of freely rotatable bonds; relates to conformational freedom and entropy.',
        'physical_constant': False,
        'units': 'count'
    },
    'aromatic_rings': {
        'mechanism': 'Resonance Energy / Delocalization',
        'theory': 'Huckel Molecular Orbital Theory',
        'description': 'Number of aromatic rings; indicates stabilization due to electron delocalization.',
        'physical_constant': True,
        'units': 'count'
    },
}

# Statistical noise threshold for feature importance
NOISE_THRESHOLD = 0.01  # Importance below this is considered statistical noise

logger = logging.getLogger(__name__)


def load_feature_importance(input_path: str) -> List[Dict[str, Any]]:
    """
    Load feature importance scores from a CSV file.

    Args:
        input_path: Path to the sensitivity analysis CSV file (e.g., reports/sensitivity.csv)

    Returns:
        List of dictionaries with 'rank', 'descriptor', 'importance' keys
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Feature importance file not found: {input_path}")

    results = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'rank': int(row['rank']),
                'descriptor': row['descriptor'],
                'importance': float(row['importance'])
            })
    return results


def map_descriptor_to_physics(descriptor_name: str) -> Dict[str, Any]:
    """
    Map a descriptor name to its physical interpretation.

    Args:
        descriptor_name: Name of the descriptor (e.g., 'homo_energy')

    Returns:
        Dictionary with physical mechanism, theory, and description
    """
    # Handle variations in naming (e.g., 'homo_energy' vs 'homo')
    normalized_name = descriptor_name.lower().strip()

    # Direct match
    if normalized_name in CHEMICAL_INVARIANTS:
        return {
            'descriptor': descriptor_name,
            'interpretation': CHEMICAL_INVARIANTS[normalized_name],
            'is_known_invariant': True,
            'confidence': 'high'
        }

    # Partial match (e.g., 'homo' matches 'homo_energy')
    for invariant_name, invariant_data in CHEMICAL_INVARIANTS.items():
        if invariant_name.startswith(normalized_name) or normalized_name.startswith(invariant_name):
            return {
                'descriptor': descriptor_name,
                'interpretation': invariant_data,
                'is_known_invariant': True,
                'confidence': 'medium'
            }

    # No match found - likely statistical noise or novel descriptor
    return {
        'descriptor': descriptor_name,
        'interpretation': {
            'mechanism': 'Unknown / Statistical Artifact',
            'theory': 'No established physical theory',
            'description': 'This descriptor does not correspond to a known chemical invariant.',
            'physical_constant': False,
            'units': 'unknown'
        },
        'is_known_invariant': False,
        'confidence': 'low'
    }


def validate_physical_significance(importance_scores: List[Dict[str, Any]], top_n: int = 5) -> Dict[str, Any]:
    """
    Validate that top N features correspond to known chemical invariants.

    Args:
        importance_scores: List of feature importance dictionaries
        top_n: Number of top features to validate

    Returns:
        Validation report dictionary
    """
    top_features = importance_scores[:top_n]
    validation_results = []
    known_count = 0
    noise_count = 0

    for feature in top_features:
        descriptor = feature['descriptor']
        importance = feature['importance']

        # Check if importance is above noise threshold
        is_significant = importance > NOISE_THRESHOLD

        # Map to physical interpretation
        physical_map = map_descriptor_to_physics(descriptor)

        validation_entry = {
            'rank': feature['rank'],
            'descriptor': descriptor,
            'importance': importance,
            'is_significant': is_significant,
            'is_known_invariant': physical_map['is_known_invariant'],
            'physical_mechanism': physical_map['interpretation']['mechanism'],
            'theoretical_basis': physical_map['interpretation']['theory'],
            'description': physical_map['interpretation']['description'],
            'confidence': physical_map['confidence'],
            'units': physical_map['interpretation']['units'],
            'assessment': 'VALID' if (is_significant and physical_map['is_known_invariant']) else 'SUSPECT'
        }

        if is_significant and physical_map['is_known_invariant']:
            known_count += 1
        elif not is_significant:
            noise_count += 1
        else:
            # Significant but not a known invariant
            pass

        validation_results.append(validation_entry)

    # Summary statistics
    total_valid = sum(1 for r in validation_results if r['assessment'] == 'VALID')
    total_suspect = sum(1 for r in validation_results if r['assessment'] == 'SUSPECT')

    return {
        'top_n': top_n,
        'total_features_analyzed': len(top_features),
        'known_invariants_found': known_count,
        'noise_features': noise_count,
        'valid_count': total_valid,
        'suspect_count': total_suspect,
        'validation_pass': total_valid >= 3,  # At least 3/5 must be valid
        'details': validation_results
    }


def generate_physical_interpretation_report(
    validation_results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Generate a detailed physical interpretability report.

    Args:
        validation_results: Results from validate_physical_significance
        output_path: Path to write the JSON report
    """
    report = {
        'report_type': 'Physical Interpretability Analysis',
        'review_basis': 'Feynman/Pauling Review - Chemical Invariants vs Statistical Noise',
        'summary': {
            'total_top_features': validation_results['top_n'],
            'valid_physical_mechanisms': validation_results['known_invariants_found'],
            'statistical_noise_features': validation_results['noise_features'],
            'overall_assessment': 'PASS' if validation_results['validation_pass'] else 'FAIL',
            'confidence_statement': (
                f"The top {validation_results['known_invariants_found']} of {validation_results['top_n']} "
                f"features correspond to established chemical invariants with known physical mechanisms."
            ) if validation_results['validation_pass'] else (
                f"Warning: Only {validation_results['known_invariants_found']} of {validation_results['top_n']} "
                f"features map to known physical mechanisms. Some top features may be statistical artifacts."
            )
        },
        'feature_analysis': validation_results['details'],
        'physical_principles_cited': list(set(
            r['theoretical_basis'] for r in validation_results['details']
            if r['is_known_invariant']
        )),
        'recommendations': []
    }

    # Generate recommendations
    if validation_results['suspect_count'] > 0:
        report['recommendations'].append(
            "Review top features marked as 'SUSPECT'. Consider: "
            "1) Increasing dataset size to reduce statistical noise, "
            "2) Removing correlated descriptors, "
            "3) Verifying descriptor calculation accuracy."
        )

    if validation_results['known_invariants_found'] < 3:
        report['recommendations'].append(
            "The model may be overfitting to statistical artifacts. "
            "Recommend retraining with stronger regularization or feature selection."
        )

    # Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Physical interpretability report written to: {output_path}")


def trace_feynman_pathway(descriptor_name: str) -> str:
    """
    Trace the physical pathway from descriptor to observable (Feynman sum-over-paths analogy).

    This function provides a narrative explanation of how a descriptor relates
    to measurable physical quantities, following the Feynman principle of
    understanding which "paths" contribute to the amplitude.

    Args:
        descriptor_name: Name of the descriptor

    Returns:
        Narrative string explaining the physical pathway
    """
    physical_map = map_descriptor_to_physics(descriptor_name)

    if not physical_map['is_known_invariant']:
        return (
            f"The descriptor '{descriptor_name}' does not correspond to a known "
            f"chemical invariant. It may represent statistical noise or a novel "
            f"correlation without established physical basis."
        )

    interpretation = physical_map['interpretation']
    pathway = (
        f"Descriptor: {descriptor_name}\n"
        f"Physical Mechanism: {interpretation['mechanism']}\n"
        f"Theoretical Foundation: {interpretation['theory']}\n"
        f"Observable Connection: This descriptor maps to {interpretation['description'].lower()}\n"
        f"Units: {interpretation['units']}\n"
        f"Significance: {'This is a fundamental physical constant.' if interpretation['physical_constant'] else 'This is a derived quantity subject to calculation method.'}"
    )

    return pathway


def run_physical_interpretability_analysis(
    input_path: str,
    output_path: str,
    top_n: int = 5
) -> Dict[str, Any]:
    """
    Main entry point for physical interpretability analysis.

    Args:
        input_path: Path to sensitivity analysis CSV (reports/sensitivity.csv)
        output_path: Path to write the JSON report (reports/physical_interpretability.json)
        top_n: Number of top features to analyze

    Returns:
        Validation results dictionary
    """
    logger.info(f"Starting physical interpretability analysis for top {top_n} features")
    logger.info(f"Input: {input_path}, Output: {output_path}")

    # Load feature importance
    importance_scores = load_feature_importance(input_path)
    logger.info(f"Loaded {len(importance_scores)} features from {input_path}")

    # Validate physical significance
    validation_results = validate_physical_significance(importance_scores, top_n)
    logger.info(f"Validation complete: {validation_results['valid_count']} valid, {validation_results['suspect_count']} suspect")

    # Generate report
    generate_physical_interpretation_report(validation_results, output_path)

    # Log Feynman pathway traces for top features
    logger.info("Tracing physical pathways for top features:")
    for feature in importance_scores[:top_n]:
        pathway = trace_feynman_pathway(feature['descriptor'])
        logger.debug(pathway)

    return validation_results


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description='Trace feature importance to physical mechanisms (Feynman/Pauling review)'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='reports/sensitivity.csv',
        help='Path to sensitivity analysis CSV with feature importance'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='reports/physical_interpretability.json',
        help='Path to write the physical interpretability report'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=5,
        help='Number of top features to analyze (default: 5)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default='logs/physical_interpretability.log',
        help='Path to log file'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logger('physical_interpretability', args.log_file)

    try:
        results = run_physical_interpretability_analysis(
            args.input,
            args.output,
            args.top_n
        )

        # Exit with error if validation fails
        if not results['validation_pass']:
            logger.warning(f"Physical interpretability check FAILED: {results['suspect_count']} suspect features")
            sys.exit(1)
        else:
            logger.info(f"Physical interpretability check PASSED: {results['valid_count']}/{results['top_n']} valid")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(3)


if __name__ == '__main__':
    main()