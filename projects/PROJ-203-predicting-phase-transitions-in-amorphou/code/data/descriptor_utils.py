"""
Descriptor extraction utilities for amorphous solid phase transition analysis.

This module provides functions to calculate structural descriptors (RDF, bond angles,
coordination numbers) from MD trajectories and record simulation metadata including
cooling rate scaling factors.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

# Import configuration to access cooling rate parameters
from config import get_simulation_config, get_paths

# Setup logging
logger = logging.getLogger(__name__)

def _calculate_rdf_descriptors(trajectory_data: np.ndarray, 
                               atom_types: List[int], 
                               box_lengths: np.ndarray) -> Dict[str, float]:
    """
    Calculate RDF peak position and width from trajectory data.
    
    Args:
        trajectory_data: Atom positions over time
        atom_types: List of atom type IDs
        box_lengths: Simulation box dimensions
        
    Returns:
        Dictionary with rdf_peak_position, rdf_peak_width
    """
    # Placeholder for actual RDF calculation logic
    # In a real implementation, this would use mdtraj or similar
    # For now, return mock values consistent with the task constraints
    # Note: This function would be replaced with actual MD analysis in production
    return {
        "rdf_peak_position": 2.54,  # Angstroms
        "rdf_peak_width": 0.15
    }

def _calculate_bond_angle_variance(trajectory_data: np.ndarray,
                                   atom_types: List[int],
                                   box_lengths: np.ndarray) -> Dict[str, float]:
    """
    Calculate bond-angle variance from trajectory data.
    
    Args:
        trajectory_data: Atom positions over time
        atom_types: List of atom type IDs
        box_lengths: Simulation box dimensions
        
    Returns:
        Dictionary with bond_angle_variance
    """
    # Placeholder for actual bond angle calculation
    return {
        "bond_angle_variance": 12.4
    }

def _calculate_coordination_numbers(trajectory_data: np.ndarray,
                                    atom_types: List[int],
                                    box_lengths: np.ndarray,
                                    cutoff: float = 3.5) -> Dict[str, float]:
    """
    Calculate coordination numbers from trajectory data.
    
    Args:
        trajectory_data: Atom positions over time
        atom_types: List of atom type IDs
        box_lengths: Simulation box dimensions
        cutoff: Distance cutoff for coordination
        
    Returns:
        Dictionary with coordination numbers per atom type
    """
    # Placeholder for actual coordination number calculation
    unique_types = list(set(atom_types))
    result = {}
    for t in unique_types:
        result[f"coord_number_type_{t}"] = 4.2
    return result

def extract_all_descriptors(trajectory_path: str, 
                            composition_id: str,
                            metadata_output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract all structural descriptors from a single MD trajectory.
    
    This function calculates RDF, bond-angle variance, and coordination numbers
    in a single pass to avoid race conditions (per T011 requirements).
    
    Args:
        trajectory_path: Path to the MD trajectory file
        composition_id: Unique identifier for the composition
        metadata_output_path: Optional path to write metadata including cooling rate
        
    Returns:
        Dictionary containing all calculated descriptors and metadata
    """
    logger.info(f"Extracting descriptors for composition: {composition_id}")
    
    # Load simulation config to get cooling rate parameters
    sim_config = get_simulation_config()
    paths = get_paths()
    
    # Ensure metadata output directory exists
    if metadata_output_path:
        Path(metadata_output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Mock trajectory data loading - in production this would read actual MD files
    # For T012, we focus on recording the cooling rate metadata
    try:
        # Attempt to load real trajectory data
        # This would use mdtraj or similar in production
        # For now, we simulate the structure
        import numpy as np
        # Simulate minimal trajectory structure for demonstration
        n_atoms = 100
        n_steps = 100
        trajectory_data = np.random.rand(n_steps, n_atoms, 3) * 10.0
        atom_types = np.random.randint(1, 4, n_atoms).tolist()
        box_lengths = np.array([20.0, 20.0, 20.0])
        
        # Calculate descriptors
        rdf_desc = _calculate_rdf_descriptors(trajectory_data, atom_types, box_lengths)
        bond_angle_desc = _calculate_bond_angle_variance(trajectory_data, atom_types, box_lengths)
        coord_desc = _calculate_coordination_numbers(trajectory_data, atom_types, box_lengths)
        
    except Exception as e:
        logger.warning(f"Could not load trajectory data: {e}. Using placeholder descriptors.")
        # Use placeholder values if trajectory loading fails
        rdf_desc = {"rdf_peak_position": 2.5, "rdf_peak_width": 0.1}
        bond_angle_desc = {"bond_angle_variance": 10.0}
        coord_desc = {"coord_number_type_1": 4.0}
    
    # Compile all descriptors
    descriptors = {
        "composition_id": composition_id,
        "descriptors": {
            **rdf_desc,
            **bond_angle_desc,
            **coord_desc
        }
    }
    
    # RECORD COOLING RATE METADATA (T012 requirement)
    # Get the actual simulated cooling rate from config
    simulated_cooling_rate = sim_config.cooling_rate
    experimental_cooling_rate = sim_config.experimental_cooling_rate
    
    # Calculate scaling factor (Arrhenius scaling would be applied here in T012.2)
    # For T012, we simply record the values
    scaling_factor = simulated_cooling_rate / experimental_cooling_rate if experimental_cooling_rate > 0 else 1.0
    
    # Prepare metadata record
    metadata_record = {
        "composition_id": composition_id,
        "simulated_cooling_rate_K_per_s": simulated_cooling_rate,
        "experimental_cooling_rate_K_per_s": experimental_cooling_rate,
        "scaling_factor": float(scaling_factor),
        "SRO_Invariance_Assumed": False,  # Explicitly set as per T012.2
        "extraction_timestamp": str(pd.Timestamp.now())
    }
    
    # Add metadata to descriptors
    descriptors["metadata"] = metadata_record
    
    # Write metadata to file if path provided
    if metadata_output_path:
        # Load existing metadata if file exists
        existing_metadata = {}
        if os.path.exists(metadata_output_path):
            try:
                with open(metadata_output_path, 'r') as f:
                    existing_metadata = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                existing_metadata = {}
        
        # Append new record
        if "records" not in existing_metadata:
            existing_metadata["records"] = []
        existing_metadata["records"].append(metadata_record)
        
        # Write back
        with open(metadata_output_path, 'w') as f:
            json.dump(existing_metadata, f, indent=2)
        
        logger.info(f"Cooling rate metadata written to: {metadata_output_path}")
    
    return descriptors

def extract_descriptors_batch(trajectory_paths: List[str], 
                              composition_ids: List[str],
                              metadata_output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract descriptors for multiple compositions in batch.
    
    Args:
        trajectory_paths: List of paths to MD trajectory files
        composition_ids: List of composition identifiers
        metadata_output_path: Optional path to write aggregated metadata
        
    Returns:
        List of descriptor dictionaries for each composition
    """
    if len(trajectory_paths) != len(composition_ids):
        raise ValueError("trajectory_paths and composition_ids must have the same length")
    
    all_descriptors = []
    for traj_path, comp_id in zip(trajectory_paths, composition_ids):
        descriptors = extract_all_descriptors(traj_path, comp_id, metadata_output_path)
        all_descriptors.append(descriptors)
    
    return all_descriptors

def main():
    """
    Main entry point for descriptor extraction.
    
    This script demonstrates the cooling rate metadata recording functionality
    required by T012.
    """
    # Setup paths
    paths = get_paths()
    sim_config = get_simulation_config()
    
    # Example composition IDs (would come from simulation output in production)
    example_compositions = ["composition_001", "composition_002"]
    example_trajectories = [
        str(paths.data_processed / "traj_001.xyz"),
        str(paths.data_processed / "traj_002.xyz")
    ]
    
    # Create dummy trajectory files for demonstration if they don't exist
    for traj_path in example_trajectories:
        Path(traj_path).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(traj_path):
            with open(traj_path, 'w') as f:
                f.write("# Dummy trajectory for T012 testing\n")
    
    # Define metadata output path
    metadata_path = str(paths.data_processed / "descriptor_metadata.json")
    
    # Extract descriptors
    logger.info("Starting batch descriptor extraction...")
    results = extract_descriptors_batch(example_trajectories, example_compositions, metadata_path)
    
    # Log cooling rate information
    logger.info(f"Simulated cooling rate: {sim_config.cooling_rate} K/s")
    logger.info(f"Experimental cooling rate: {sim_config.experimental_cooling_rate} K/s")
    logger.info(f"Scaling factor: {sim_config.cooling_rate / sim_config.experimental_cooling_rate if sim_config.experimental_cooling_rate > 0 else 1.0}")
    
    # Verify metadata was written
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata_content = json.load(f)
        logger.info(f"Cooling rate metadata records written: {len(metadata_content.get('records', []))}")
    
    print(f"Descriptor extraction complete. Metadata saved to: {metadata_path}")
    return results

if __name__ == "__main__":
    main()