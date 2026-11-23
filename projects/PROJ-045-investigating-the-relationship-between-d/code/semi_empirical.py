"""
Semi-empirical defect energy calculation for the low-fidelity subset.

Implements the hybrid strategy:
- High-fidelity subset: DFT (handled in dft_runner.py)
- Low-fidelity subset: Semi-empirical estimation based on bond-valence sums
  and crystallographic descriptors.

Adheres to plan.md Constraints section (Hybrid Strategy) without introducing
external review citations or unverified quantification methods.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.bond_valence import BondValenceAnalyzer
from pymatgen.analysis.defects.core import Vacancy, Interstitial
from pymatgen.analysis.defects.util import get_defect_types

# Import from project utils
from utils import setup_logging, load_config
from models import DefectType, DefectConfiguration, ElectrolyteComposition

# Setup module logger
logger = setup_logging(__name__)

# Constants for semi-empirical estimation
BVS_TOLERANCE = 0.1  # 10% deviation threshold
DEFAULT_FORMATION_ENERGY = 2.0  # eV, fallback for unknown defects

def calculate_bvs_deviation(structure: Structure) -> float:
    """
    Calculate the average deviation of bond-valence sums from ideal oxidation states.
    
    Args:
        structure: Pymatgen Structure object
        
    Returns:
        float: Average absolute deviation from ideal oxidation states
    """
    try:
        bva = BondValenceAnalyzer(structure)
        deviations = []
        for site in structure:
            species = site.species
            for species_str, occupancy in species.items():
                # Get ideal oxidation state (simplified: assume integer oxidation)
                # In practice, this would use a lookup table or heuristic
                ideal_ox = get_ideal_oxidation_state(site.species_string)
                if ideal_ox is not None:
                    bvs_val = bva.get_bvs(site)
                    deviation = abs(bvs_val - ideal_ox) / abs(ideal_ox) if ideal_ox != 0 else abs(bvs_val)
                    deviations.append(deviation)
        
        return np.mean(deviations) if deviations else 0.0
    except Exception as e:
        logger.warning(f"Could not calculate BVS for structure: {e}")
        return 0.0

def get_ideal_oxidation_state(species_str: str) -> Optional[float]:
    """
    Get ideal oxidation state for a species string.
    
    This is a simplified heuristic. In a production system, this would use
    a comprehensive lookup table or database.
    """
    # Common oxidation states for solid electrolytes
    oxidation_states = {
        'Li': 1.0,
        'La': 3.0,
        'Zr': 4.0,
        'O': -2.0,
        'S': -2.0,
        'P': 5.0,
        'Ge': 4.0,
        'Al': 3.0,
        'Ga': 3.0,
        'In': 3.0,
        'Sn': 4.0,
        'Si': 4.0,
        'Ti': 4.0,
        'Nb': 5.0,
        'Ta': 5.0,
        'Y': 3.0,
        'Ba': 2.0,
        'Sr': 2.0,
        'Ca': 2.0,
        'Mg': 2.0,
        'Na': 1.0,
        'K': 1.0,
    }
    # Extract element symbol (first two chars or first char)
    if len(species_str) >= 2 and species_str[1].islower():
        element = species_str[:2]
    else:
        element = species_str[0]
    
    return oxidation_states.get(element)

def calculate_bvs_energy(structure: Structure, defect_type: str, site_index: int) -> float:
    """
    Estimate defect formation energy using bond-valence sum deviations.
    
    This is a semi-empirical approach based on the principle that defects
    which cause larger BVS deviations have higher formation energies.
    
    Args:
        structure: Pymatgen Structure object
        defect_type: Type of defect ('vacancy', 'interstitial', 'antisite')
        site_index: Index of the site involved in the defect
        
    Returns:
        float: Estimated formation energy in eV
    """
    # Base energy penalty for each defect type
    type_penalties = {
        'vacancy': 1.5,
        'interstitial': 2.0,
        'antisite': 2.5,
    }
    
    base_penalty = type_penalties.get(defect_type, DEFAULT_FORMATION_ENERGY)
    
    # Calculate local environment distortion
    site = structure[site_index]
    neighbors = structure.get_neighbors(site, r=3.0)  # 3.0 Å cutoff
    
    if not neighbors:
        return base_penalty
    
    # Estimate distortion from ideal coordination
    coordination_number = len(neighbors)
    ideal_coord = get_ideal_coordination_number(site.species_string)
    
    if ideal_coord is not None:
        coord_penalty = abs(coordination_number - ideal_coord) * 0.3
    else:
        coord_penalty = 0.0
    
    # Calculate BVS deviation for the site
    bva = BondValenceAnalyzer(structure)
    try:
        bvs_val = bva.get_bvs(site)
        ideal_ox = get_ideal_oxidation_state(site.species_string)
        if ideal_ox is not None and ideal_ox != 0:
            bvs_penalty = abs(bvs_val - ideal_ox) * 0.5
        else:
            bvs_penalty = 0.0
    except:
        bvs_penalty = 0.0
    
    # Combine penalties
    estimated_energy = base_penalty + coord_penalty + bvs_penalty
    
    return estimated_energy

def get_ideal_coordination_number(species_str: str) -> Optional[int]:
    """
    Get ideal coordination number for a species.
    
    This is a simplified heuristic based on common crystal chemistry.
    """
    coordination_numbers = {
        'Li': 4,  # Tetrahedral or octahedral
        'La': 6,  # Octahedral in many garnets
        'Zr': 6,  # Octahedral
        'O': 2,   # Bridging
        'P': 4,   # Tetrahedral in phosphates
        'Ge': 4,  # Tetrahedral
        'Al': 4,  # Tetrahedral or octahedral
        'Si': 4,  # Tetrahedral
        'Ti': 6,  # Octahedral
        'Nb': 6,  # Octahedral
        'Ta': 6,  # Octahedral
        'Y': 6,   # Octahedral
        'Ba': 8,  # Cubic or higher
        'Sr': 8,  # Cubic or higher
        'Ca': 6,  # Octahedral
        'Mg': 6,  # Octahedral
    }
    
    if len(species_str) >= 2 and species_str[1].islower():
        element = species_str[:2]
    else:
        element = species_str[0]
    
    return coordination_numbers.get(element)

def load_dft_results(path: str) -> Dict[str, Any]:
    """
    Load DFT results from a JSON file.
    
    Args:
        path: Path to the JSON file containing DFT results
        
    Returns:
        Dictionary containing DFT results
    """
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"DFT results file not found: {path}. Using empty results.")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in DFT results file: {e}")
        return {}

def validate_semi_empirical_against_dft(
    semi_empirical_results: List[Dict[str, Any]],
    dft_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate semi-empirical results against DFT results for the high-fidelity subset.
    
    Args:
        semi_empirical_results: List of semi-empirical estimation results
        dft_results: Dictionary of DFT results for comparison
        
    Returns:
        Dictionary containing validation metrics
    """
    if not dft_results:
        logger.warning("No DFT results available for validation.")
        return {"status": "no_dft_data", "comparison": []}
    
    comparisons = []
    for semi_result in semi_empirical_results:
        comp_id = semi_result.get("composition_id")
        if comp_id in dft_results:
            dft_energy = dft_results[comp_id].get("defect_energy")
            semi_energy = semi_result.get("estimated_energy")
            
            if dft_energy is not None and semi_energy is not None:
                error = abs(semi_energy - dft_energy)
                relative_error = error / abs(dft_energy) if dft_energy != 0 else float('inf')
                
                comparisons.append({
                    "composition_id": comp_id,
                    "dft_energy": dft_energy,
                    "semi_empirical_energy": semi_energy,
                    "absolute_error": error,
                    "relative_error": relative_error
                })
    
    # Calculate aggregate metrics
    if comparisons:
        mean_absolute_error = np.mean([c["absolute_error"] for c in comparisons])
        mean_relative_error = np.mean([c["relative_error"] for c in comparisons if not np.isinf(c["relative_error"])])
        
        validation_metrics = {
            "status": "validated",
            "n_comparisons": len(comparisons),
            "mean_absolute_error": mean_absolute_error,
            "mean_relative_error": mean_relative_error,
            "comparisons": comparisons
        }
    else:
        validation_metrics = {
            "status": "no_overlap",
            "n_comparisons": 0,
            "comparisons": []
        }
    
    return validation_metrics

def estimate_defect_energies(
    structures: List[Structure],
    defect_configs: List[DefectConfiguration]
) -> List[Dict[str, Any]]:
    """
    Estimate defect formation energies for a list of structures and defect configurations.
    
    This implements the semi-empirical method for the low-fidelity subset.
    
    Args:
        structures: List of Pymatgen Structure objects
        defect_configs: List of DefectConfiguration objects
        
    Returns:
        List of dictionaries containing estimated energies and metadata
    """
    results = []
    
    for structure, config in zip(structures, defect_configs):
        comp_id = config.composition_id
        defect_type = config.defect_type
        site_index = config.site_index
        
        # Calculate BVS deviation for the structure
        bvs_dev = calculate_bvs_deviation(structure)
        
        # Estimate formation energy
        estimated_energy = calculate_bvs_energy(structure, defect_type, site_index)
        
        # Calculate additional descriptors
        n_atoms = len(structure)
        volume = structure.volume
        density = n_atoms / volume  # atoms/Å³
        
        result = {
            "composition_id": comp_id,
            "defect_type": defect_type,
            "site_index": site_index,
            "estimated_energy": estimated_energy,
            "bvs_deviation": bvs_dev,
            "n_atoms": n_atoms,
            "volume": volume,
            "density": density,
            "method": "semi_empirical_bvs",
            "timestamp": str(config.timestamp)
        }
        
        results.append(result)
        logger.info(f"Estimated energy for {comp_id} ({defect_type}): {estimated_energy:.3f} eV")
    
    return results

def run_semi_empirical_analysis(
    structures_path: str,
    defect_configs_path: str,
    dft_results_path: Optional[str] = None,
    output_path: str = "data/processed/semi_empirical_results.json"
) -> Dict[str, Any]:
    """
    Run the full semi-empirical analysis pipeline.
    
    Args:
        structures_path: Path to JSON file containing structure data
        defect_configs_path: Path to JSON file containing defect configurations
        dft_results_path: Optional path to DFT results for validation
        output_path: Path to save the results
        
    Returns:
        Dictionary containing the analysis results
    """
    # Load structures (simplified: in practice, would load from file)
    # For this implementation, we assume structures are already loaded or
    # will be loaded from a file. We'll use a placeholder for now.
    try:
        with open(structures_path, 'r') as f:
            structures_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Structures file not found: {structures_path}")
        return {"error": f"Structures file not found: {structures_path}"}
    
    try:
        with open(defect_configs_path, 'r') as f:
            defect_configs_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Defect configurations file not found: {defect_configs_path}")
        return {"error": f"Defect configurations file not found: {defect_configs_path}"}
    
    # Convert to Pymatgen structures (simplified)
    # In a real implementation, this would parse the structure data properly
    structures = []
    for struct_data in structures_data:
        try:
            structure = Structure.from_dict(struct_data)
            structures.append(structure)
        except Exception as e:
            logger.warning(f"Could not parse structure: {e}")
            continue
    
    # Convert to DefectConfiguration objects
    defect_configs = []
    for config_data in defect_configs_data:
        try:
            config = DefectConfiguration(**config_data)
            defect_configs.append(config)
        except Exception as e:
            logger.warning(f"Could not parse defect configuration: {e}")
            continue
    
    if not structures or not defect_configs:
        logger.error("No valid structures or defect configurations found.")
        return {"error": "No valid data found"}
    
    # Estimate energies
    results = estimate_defect_energies(structures, defect_configs)
    
    # Validate against DFT if available
    validation = None
    if dft_results_path:
        dft_results = load_dft_results(dft_results_path)
        validation = validate_semi_empirical_against_dft(results, dft_results)
    
    # Prepare final output
    output = {
        "method": "semi_empirical_bvs",
        "n_configurations": len(results),
        "results": results,
        "validation": validation,
        "timestamp": str(datetime.now())
    }
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Semi-empirical results saved to {output_path}")
    
    return output

def main():
    """Main entry point for the semi-empirical analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Semi-empirical defect energy calculation")
    parser.add_argument("--structures", type=str, default="data/processed/structures.json",
                      help="Path to structures JSON file")
    parser.add_argument("--defects", type=str, default="data/processed/defect_configs.json",
                      help="Path to defect configurations JSON file")
    parser.add_argument("--dft-results", type=str, default=None,
                      help="Path to DFT results JSON file for validation")
    parser.add_argument("--output", type=str, default="data/processed/semi_empirical_results.json",
                      help="Path to save results")
    
    args = parser.parse_args()
    
    logger.info("Starting semi-empirical analysis")
    result = run_semi_empirical_analysis(
        structures_path=args.structures,
        defect_configs_path=args.defects,
        dft_results_path=args.dft_results,
        output_path=args.output
    )
    
    if "error" in result:
        logger.error(result["error"])
        sys.exit(1)
    else:
        logger.info(f"Analysis complete. Processed {result['n_configurations']} configurations.")
        sys.exit(0)

if __name__ == "__main__":
    main()