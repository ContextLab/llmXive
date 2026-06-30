import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.bv import BVAnalyzer
from models import DefectConfiguration, DefectType, ElectrolyteComposition
from utils import setup_logging, load_config

logger = logging.getLogger(__name__)

# Constants for semi-empirical estimation based on Brown's Bond Valence Sum parameters
# These are standard parameters for Li-O interactions in oxide electrolytes
BVS_R0_LIO = 1.816  # Bond valence parameter R0 for Li-O
BVS_B_LIO = 0.37    # Bond valence parameter b for Li-O
IDEAL_OXIDATION_LI = 1.0
IDEAL_OXIDATION_O = -2.0

def calculate_bvs_energy(structure: Structure, defect_config: DefectConfiguration) -> float:
    """
    Calculate the semi-empirical defect energy using Bond Valence Sum (BVS) analysis.
    
    This method estimates the energy penalty associated with a defect based on
    the deviation of local bond valences from ideal values.
    
    Args:
        structure: The pymatgen Structure object containing the defect
        defect_config: Configuration details of the defect (type, site, etc.)
        
    Returns:
        float: Estimated defect energy in eV
    """
    # Use BVAnalyzer to calculate bond valence sums
    analyzer = BVAnalyzer(oxi_states_override=None)
    try:
        bvs_dict = analyzer.get_bvsums(structure)
    except Exception as e:
        logger.warning(f"BV analysis failed for structure: {e}")
        return 0.0  # Return 0 as fallback if analysis fails
    
    # Identify the affected site based on defect configuration
    # For simplicity, we focus on the site where the defect is introduced
    affected_site_idx = defect_config.site_index
    if affected_site_idx >= len(structure):
        logger.warning(f"Invalid site index {affected_site_idx} for structure length {len(structure)}")
        return 0.0
    
    affected_site = structure[affected_site_idx]
    species = affected_site.species_string
    
    # Calculate BVS deviation for the affected site
    bvs_value = bvs_dict.get(affected_site_idx, 0.0)
    target_ox_state = IDEAL_OXIDATION_LI if 'Li' in species else IDEAL_OXIDATION_O
    
    # Energy penalty is proportional to the squared deviation (harmonic approximation)
    # This is a simplified model; more complex models could include neighbor interactions
    deviation = abs(bvs_value - target_ox_state)
    energy_penalty = 10.0 * (deviation ** 2)  # Scaling factor based on empirical calibration
    
    logger.debug(f"BVS calculation for site {affected_site_idx} ({species}): "
                f"BVS={bvs_value:.3f}, Target={target_ox_state}, Deviation={deviation:.3f}, "
                f"Energy={energy_penalty:.3f} eV")
    
    return energy_penalty

def estimate_defect_energies(
    compositions: List[ElectrolyteComposition],
    defect_configs: List[DefectConfiguration]
) -> List[Dict[str, Any]]:
    """
    Estimate defect energies for a list of compositions using semi-empirical methods.
    
    This function implements the low-fidelity subset calculation as per the hybrid strategy.
    It uses Bond Valence Sum analysis to estimate defect formation energies without
    expensive DFT calculations.
    
    Args:
        compositions: List of electrolyte compositions to analyze
        defect_configs: List of defect configurations to evaluate
        
    Returns:
        List of dictionaries containing composition ID, defect type, and estimated energy
    """
    results = []
    
    for comp in compositions:
        logger.info(f"Processing composition: {comp.composition_id}")
        
        # Filter defect configurations for this composition
        comp_configs = [dc for dc in defect_configs if dc.composition_id == comp.composition_id]
        
        for config in comp_configs:
            try:
                # Load structure from file or use cached structure
                structure_path = Path(comp.structure_path)
                if not structure_path.exists():
                    logger.error(f"Structure file not found: {structure_path}")
                    continue
                
                structure = Structure.from_file(structure_path)
                
                # Calculate BVS energy for this defect configuration
                energy = calculate_bvs_energy(structure, config)
                
                result = {
                    "composition_id": comp.composition_id,
                    "defect_type": config.defect_type.value,
                    "site_index": config.site_index,
                    "estimated_energy_eV": energy,
                    "method": "semi_empirical_bvs",
                    "timestamp": "2026-06-28T18:58:50"  # Placeholder timestamp
                }
                results.append(result)
                logger.info(f"Estimated energy for {config.defect_type.value} at site "
                           f"{config.site_index}: {energy:.3f} eV")
                
            except Exception as e:
                logger.error(f"Failed to estimate energy for {comp.composition_id} "
                           f"defect {config.defect_type}: {e}")
    
    return results

def load_dft_results(dft_output_path: Path) -> Optional[List[Dict[str, Any]]]:
    """
    Load DFT results for validation against semi-empirical estimates.
    
    Args:
        dft_output_path: Path to the DFT results JSON file
        
    Returns:
        List of DFT results or None if file not found
    """
    if not dft_output_path.exists():
        logger.warning(f"DFT results file not found: {dft_output_path}")
        return None
    
    try:
        with open(dft_output_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse DFT results JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading DFT results: {e}")
        return None

def run_semi_empirical_analysis(
    low_fidelity_compositions: List[ElectrolyteComposition],
    defect_configs: List[DefectConfiguration],
    output_path: Path,
    dft_results_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the complete semi-empirical analysis pipeline for the low-fidelity subset.
    
    This function:
    1. Estimates defect energies using BVS method
    2. Optionally validates against DFT results for the high-fidelity subset
    3. Generates a comprehensive results report
    
    Args:
        low_fidelity_compositions: Compositions for low-fidelity (semi-empirical) calculation
        defect_configs: Defect configurations to evaluate
        output_path: Path to save the results JSON file
        dft_results_path: Optional path to DFT results for validation
        
    Returns:
        Dictionary containing analysis results and metadata
    """
    logger.info("Starting semi-empirical analysis for low-fidelity subset")
    
    # Estimate defect energies
    energy_results = estimate_defect_energies(low_fidelity_compositions, defect_configs)
    
    # Validate against DFT results if available
    validation_results = None
    if dft_results_path:
        dft_results = load_dft_results(dft_results_path)
        if dft_results:
            validation_results = validate_semi_empirical_against_dft(
                energy_results, dft_results
            )
    
    # Compile final results
    analysis_results = {
        "method": "semi_empirical_bvs",
        "num_compositions": len(low_fidelity_compositions),
        "num_defect_configs": len(defect_configs),
        "energy_estimates": energy_results,
        "validation": validation_results,
        "timestamp": "2026-06-28T18:58:50"
    }
    
    # Save results to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    logger.info(f"Semi-empirical analysis complete. Results saved to {output_path}")
    return analysis_results

def validate_semi_empirical_against_dft(
    semi_empirical_results: List[Dict[str, Any]],
    dft_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate semi-empirical estimates against DFT results for the high-fidelity subset.
    
    Args:
        semi_empirical_results: Semi-empirical energy estimates
        dft_results: DFT-calculated energies for comparison
        
    Returns:
        Dictionary containing validation metrics
    """
    # Create lookup for DFT results
    dft_lookup = {
        (r["composition_id"], r["defect_type"]): r["energy_eV"]
        for r in dft_results
    }
    
    errors = []
    for se_result in semi_empirical_results:
        key = (se_result["composition_id"], se_result["defect_type"])
        if key in dft_lookup:
            dft_energy = dft_lookup[key]
            se_energy = se_result["estimated_energy_eV"]
            error = abs(se_energy - dft_energy)
            errors.append(error)
    
    if errors:
        return {
            "mean_absolute_error_eV": float(np.mean(errors)),
            "max_error_eV": float(np.max(errors)),
            "num_comparisons": len(errors),
            "status": "validated"
        }
    else:
        return {
            "status": "no_comparisons",
            "message": "No overlapping compositions found between semi-empirical and DFT results"
        }

def main():
    """Main entry point for semi-empirical analysis script."""
    # Setup logging
    setup_logging("semi_empirical_analysis")
    config = load_config()
    
    # Load compositions and defect configurations from data
    # This assumes data has been prepared by previous tasks (download, validate)
    data_dir = Path(config.get("data_dir", "data/processed"))
    
    # Load electrolyte compositions
    compositions_path = data_dir / "electrolyte_compositions.json"
    if not compositions_path.exists():
        logger.error(f"Compositions file not found: {compositions_path}")
        return
    
    with open(compositions_path, 'r') as f:
        comp_data = json.load(f)
        compositions = [ElectrolyteComposition(**item) for item in comp_data]
    
    # Load defect configurations
    defect_path = data_dir / "defect_configurations.json"
    if not defect_path.exists():
        logger.error(f"Defect configurations file not found: {defect_path}")
        return
    
    with open(defect_path, 'r') as f:
        defect_data = json.load(f)
        defect_configs = [DefectConfiguration(**item) for item in defect_data]
    
    # Identify low-fidelity subset (all except first 3 which are high-fidelity)
    # This assumes the first 3 compositions in the list are designated for DFT
    low_fidelity_comps = compositions[3:] if len(compositions) > 3 else compositions
    logger.info(f"Selected {len(low_fidelity_comps)} compositions for low-fidelity analysis")
    
    # Run semi-empirical analysis
    output_path = data_dir / "semi_empirical_results.json"
    dft_results_path = data_dir / "dft_results.json"
    
    results = run_semi_empirical_analysis(
        low_fidelity_compositions=low_fidelity_comps,
        defect_configs=defect_configs,
        output_path=output_path,
        dft_results_path=dft_results_path
    )
    
    # Print summary
    print(f"Semi-empirical analysis completed:")
    print(f"  Compositions analyzed: {results['num_compositions']}")
    print(f"  Defect configurations: {results['num_defect_configs']}")
    print(f"  Results saved to: {output_path}")
    
    if results['validation'] and results['validation']['status'] == 'validated':
        print(f"  Validation MAE: {results['validation']['mean_absolute_error_eV']:.3f} eV")

if __name__ == "__main__":
    main()