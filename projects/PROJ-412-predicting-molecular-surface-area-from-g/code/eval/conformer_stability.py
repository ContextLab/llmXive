import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats

# Import from project API surface
from utils.logging import get_logger, setup_logging
from utils.config import get_project_root, get_data_dir, get_results_dir
from utils.seed import set_seed
from data.preprocess import generate_conformers, calculate_sasa
import rdkit
from rdkit import Chem
from rdkit.Chem import AllChem

def load_subset_for_pilot(
    input_path: str,
    subset_size: int = 50
) -> pd.DataFrame:
    """
    Load a small random subset of molecules from the processed parquet file.
    This is used for the pilot stability check.
    """
    logger = get_logger()
    logger.info(f"Loading subset of {subset_size} molecules from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    
    if len(df) < subset_size:
        logger.warning(f"Dataset size ({len(df)}) is smaller than requested subset size ({subset_size}). Using full dataset.")
        subset_size = len(df)
    
    # Random sample with fixed seed for reproducibility
    set_seed(42)
    subset = df.sample(n=subset_size, random_state=42)
    
    logger.info(f"Loaded {len(subset)} molecules for pilot check")
    return subset

def generate_multiple_conformers_and_sasa(
    smiles: str,
    num_conformers: int = 10,
    max_attempts: int = 100
) -> Tuple[Optional[float], float, bool]:
    """
    Generate multiple conformers for a single molecule and calculate SASA variance.
    
    Returns:
        Tuple of (mean_sasa, variance_sasa, success_flag)
        If generation fails, returns (None, None, False)
    """
    logger = get_logger()
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        logger.warning(f"Could not parse SMILES: {smiles}")
        return None, None, False
    
    # Add hydrogens
    mol = Chem.AddHs(mol)
    
    # Generate conformers
    try:
        params = AllChem.ETKDGv3()
        params.maxAttempts = max_attempts
        params.numThreads = 0
        
        conformer_ids = AllChem.EmbedMultipleConfs(mol, numConfs=num_conformers, params=params)
        
        if len(conformer_ids) == 0:
            logger.warning(f"Failed to generate any conformers for: {smiles}")
            return None, None, False
        
        sasa_values = []
        
        for conf_id in conformer_ids:
            # Minimize energy
            try:
                AllChem.MMFFOptimizeMolecule(mol, confId=conf_id, maxIters=200)
            except Exception as e:
                logger.debug(f"MMFF optimization failed for conf {conf_id}: {e}")
                continue
            
            # Calculate SASA
            try:
                sasa = calculate_sasa(mol, conf_id=conf_id)
                if sasa is not None and sasa > 0:
                    sasa_values.append(sasa)
            except Exception as e:
                logger.debug(f"SASA calculation failed for conf {conf_id}: {e}")
                continue
        
        if len(sasa_values) < 2:
            logger.warning(f"Not enough valid SASA values for {smiles}: {len(sasa_values)}")
            return None, None, False
        
        mean_sasa = np.mean(sasa_values)
        variance_sasa = np.var(sasa_values)
        std_sasa = np.std(sasa_values)
        
        logger.debug(f"Molecule {smiles[:20]}...: mean_sasa={mean_sasa:.2f}, std={std_sasa:.2f}, var={variance_sasa:.2f}")
        
        return mean_sasa, variance_sasa, True
        
    except Exception as e:
        logger.error(f"Conformer generation failed for {smiles}: {e}")
        return None, None, False

def run_stability_check(
    input_path: str,
    output_path: str,
    num_conformers: int = 10,
    variance_threshold: float = 5.0,
    subset_size: int = 50
) -> Dict[str, Any]:
    """
    Run the conformer stability check on a pilot subset.
    
    Args:
        input_path: Path to the processed parquet file
        output_path: Path to write the markdown report
        num_conformers: Number of conformers to generate per molecule
        variance_threshold: SASA variance threshold above which a molecule is flagged
        subset_size: Number of molecules to sample for the pilot check
    
    Returns:
        Dictionary containing stability analysis results
    """
    logger = get_logger()
    logger.info(f"Starting conformer stability pilot check")
    logger.info(f"Parameters: num_conformers={num_conformers}, variance_threshold={variance_threshold}, subset_size={subset_size}")
    
    # Load subset
    subset_df = load_subset_for_pilot(input_path, subset_size)
    
    results = []
    failed_molecules = []
    successful_molecules = []
    
    total_sasa_variance = []
    
    for idx, row in subset_df.iterrows():
        smiles = row['smiles']
        
        mean_sasa, variance_sasa, success = generate_multiple_conformers_and_sasa(
            smiles, 
            num_conformers=num_conformers
        )
        
        if success:
            is_stable = variance_sasa <= variance_threshold
            status = "STABLE" if is_stable else "UNSTABLE"
            
            result = {
                'smiles': smiles,
                'mean_sasa': mean_sasa,
                'variance_sasa': variance_sasa,
                'std_sasa': np.sqrt(variance_sasa),
                'num_conformers_generated': num_conformers,
                'status': status,
                'threshold': variance_threshold
            }
            results.append(result)
            successful_molecules.append(smiles)
            total_sasa_variance.append(variance_sasa)
        else:
            failed_molecules.append(smiles)
    
    # Calculate statistics
    total_molecules = len(subset_df)
    success_count = len(successful_molecules)
    failure_count = len(failed_molecules)
    stability_count = sum(1 for r in results if r['status'] == 'STABLE')
    instability_count = sum(1 for r in results if r['status'] == 'UNSTABLE')
    
    success_rate = success_count / total_molecules if total_molecules > 0 else 0
    stability_rate = stability_count / success_count if success_count > 0 else 0
    
    mean_variance = np.mean(total_sasa_variance) if total_sasa_variance else 0
    std_variance = np.std(total_sasa_variance) if total_sasa_variance else 0
    
    # Determine if pipeline should be flagged
    pipeline_flagged = instability_count > (success_count * 0.1)  # More than 10% unstable
    
    analysis_summary = {
        'total_molecules_tested': total_molecules,
        'conformer_generation_success_rate': success_rate,
        'conformer_stability_rate': stability_rate,
        'mean_sasa_variance': mean_variance,
        'std_sasa_variance': std_variance,
        'variance_threshold': variance_threshold,
        'pipeline_flagged': pipeline_flagged,
        'num_conformers_per_molecule': num_conformers
    }
    
    # Generate markdown report
    report_lines = [
        "# Conformer Stability Pilot Check Report",
        "",
        "## Summary",
        "",
        f"- **Total Molecules Tested**: {total_molecules}",
        f"- **Conformer Generation Success Rate**: {success_rate:.2%}",
        f"- **Conformer Stability Rate**: {stability_rate:.2%}",
        f"- **Mean SASA Variance**: {mean_variance:.4f} Å²",
        f"- **Std SASA Variance**: {std_variance:.4f} Å²",
        f"- **Variance Threshold**: {variance_threshold} Å²",
        f"- **Pipeline Flagged**: {'⚠️ YES' if pipeline_flagged else '✅ NO'}",
        "",
        "## Methodology",
        "",
        f"This check generates {num_conformers} conformers per molecule and measures the variance in SASA values.",
        f"A variance exceeding {variance_threshold} Å² indicates conformer instability.",
        f"The pipeline is flagged if more than 10% of successfully generated conformers are unstable.",
        "",
        "## Results Breakdown",
        "",
        f"- **Stable Molecules**: {stability_count}",
        f"- **Unstable Molecules**: {instability_count}",
        f"- **Failed Conformer Generation**: {failure_count}",
        "",
    ]
    
    if instability_count > 0:
        report_lines.extend([
            "### Unstable Molecules",
            "",
            "The following molecules showed high SASA variance (>{} Å²):".format(variance_threshold),
            ""
        ])
        for r in results:
            if r['status'] == 'UNSTABLE':
                report_lines.append(f"- `{r['smiles'][:50]}...`: variance={r['variance_sasa']:.4f} Å²")
        report_lines.append("")
    
    if failure_count > 0:
        report_lines.extend([
            "### Conformer Generation Failures",
            "",
            "The following molecules failed conformer generation:",
            ""
        ])
        for smiles in failed_molecules[:20]:  # Limit to first 20
            report_lines.append(f"- `{smiles[:50]}...`")
        if failure_count > 20:
            report_lines.append(f"... and {failure_count - 20} more")
        report_lines.append("")
    
    report_lines.extend([
        "## Conclusion",
        "",
        f"The conformer generation pipeline shows {'acceptable' if not pipeline_flagged else 'concerning'} stability.",
        f"{'No action required.' if not pipeline_flagged else 'Recommendation: Review conformer generation parameters or increase threshold.'}",
        "",
        f"Report generated on: {pd.Timestamp.now().isoformat()}",
    ])
    
    # Write report
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Report written to {output_path}")
    
    # Save detailed results as JSON for programmatic access
    json_output_path = output_path.replace('.md', '.json')
    with open(json_output_path, 'w') as f:
        json.dump({
            'summary': analysis_summary,
            'detailed_results': results,
            'failed_molecules': failed_molecules
        }, f, indent=2)
    
    logger.info(f"Detailed results written to {json_output_path}")
    
    return analysis_summary

def main():
    """Main entry point for the conformer stability pilot check."""
    parser = argparse.ArgumentParser(description='Conformer Stability Pilot Check')
    parser.add_argument('--input', type=str, default=None,
                      help='Path to processed parquet file (default: auto-detect)')
    parser.add_argument('--output', type=str, default=None,
                      help='Path to output markdown report (default: auto-detect)')
    parser.add_argument('--num-conformers', type=int, default=10,
                      help='Number of conformers per molecule (default: 10)')
    parser.add_argument('--variance-threshold', type=float, default=5.0,
                      help='SASA variance threshold for stability (default: 5.0)')
    parser.add_argument('--subset-size', type=int, default=50,
                      help='Number of molecules for pilot check (default: 50)')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level)
    logger = get_logger()
    
    # Determine paths
    project_root = get_project_root()
    data_dir = get_data_dir()
    results_dir = get_results_dir()
    
    # Default input path
    if args.input is None:
        input_path = data_dir / 'processed' / 'graphs_with_sasa.parquet'
        if not input_path.exists():
            # Try alternative name from T015
            input_path = data_dir / 'processed' / 'processed_data.parquet'
        if not input_path.exists():
            logger.error("Could not find processed data file. Please specify --input")
            sys.exit(1)
    else:
        input_path = Path(args.input)
    
    # Default output path
    if args.output is None:
        output_path = results_dir / 'reports' / 'pilot_conformer_check.md'
    else:
        output_path = Path(args.output)
    
    logger.info(f"Input file: {input_path}")
    logger.info(f"Output file: {output_path}")
    
    # Run stability check
    try:
        results = run_stability_check(
            input_path=str(input_path),
            output_path=str(output_path),
            num_conformers=args.num_conformers,
            variance_threshold=args.variance_threshold,
            subset_size=args.subset_size
        )
        
        logger.info("Pilot check completed successfully")
        logger.info(f"Pipeline flagged: {results['pipeline_flagged']}")
        
        if results['pipeline_flagged']:
            logger.warning("⚠️ Pipeline flagged due to conformer instability!")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Pilot check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
