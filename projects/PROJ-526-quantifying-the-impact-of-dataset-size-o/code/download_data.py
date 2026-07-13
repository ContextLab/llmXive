import os
import time
import logging
import shutil
import gc
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from huggingface_hub import HfApi, hf_hub_download, list_repo_files
from tqdm import tqdm

from config import get_config, require_hf_token, require_data_dir, require_state_dir
from utils.integrity import compute_sha256, log_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DownloadError(Exception):
    """Custom exception for data download failures."""
    pass

def exponential_backoff(retries: int = 5, base_delay: float = 2.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay."""
    delay = min(base_delay * (2 ** retries), max_delay)
    return delay

def download_with_retry(
    hf_token: str,
    repo_id: str,
    filename: str,
    local_dir: Path,
    max_retries: int = 5
) -> Optional[Path]:
    """
    Download a file from HuggingFace with exponential backoff retry logic.
    """
    attempt = 0
    while attempt <= max_retries:
        try:
            logger.info(f"Downloading {filename} from {repo_id} (Attempt {attempt + 1})")
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(local_dir),
                token=hf_token,
                force_download=False
            )
            logger.info(f"Successfully downloaded {filename} to {local_path}")
            return Path(local_path)
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Failed to download {filename} after {max_retries} attempts: {e}")
                raise DownloadError(f"Failed to download {filename}: {e}")
            
            delay = exponential_backoff(attempt - 1)
            logger.warning(f"Download failed for {filename}: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
    return None

def fetch_dataset_metadata(hf_token: str, repo_id: str) -> List[Dict[str, Any]]:
    """
    Fetch list of files from a HuggingFace repository.
    """
    try:
        api = HfApi(token=hf_token)
        files = api.list_repo_files(repo_id=repo_id)
        # Filter for data files (csv, parquet, json)
        data_files = [f for f in files if f.endswith(('.csv', '.parquet', '.json', '.txt'))]
        return data_files
    except Exception as e:
        raise DownloadError(f"Failed to fetch metadata from {repo_id}: {e}")

def process_property_files(
    raw_dir: Path,
    processed_dir: Path,
    properties: List[str],
    chunk_size: int = 100000,
    dtype_map: Optional[Dict[str, np.dtype]] = None
) -> Tuple[int, int]:
    """
    Process downloaded files into optimized chunks and consolidate.
    Implements chunked loading to keep RAM usage < 7GB.
    
    Args:
        raw_dir: Directory containing raw downloaded files
        processed_dir: Directory to save processed files
        properties: List of property names to process
        chunk_size: Number of rows per chunk
        dtype_map: Dictionary mapping column names to dtypes for memory optimization
    
    Returns:
        Tuple of (total_rows_processed, total_files_processed)
    """
    if dtype_map is None:
        # Default optimization: float64 -> float32, int64 -> int32 where safe
        dtype_map = {
            'property_value': np.float32,
            'formation_energy': np.float32,
            'band_gap': np.float32,
            'magnetic_moment': np.float32,
            'volume': np.float32,
            'density': np.float32,
            'energy_per_atom': np.float32,
            'total_energy': np.float32,
            'homo': np.float32,
            'lumo': np.float32,
            'gap': np.float32,
            'melting_point': np.float32,
            'boiling_point': np.float32,
            'hardness': np.float32,
            'elastic_modulus': np.float32,
            'shear_modulus': np.float32,
            'bulk_modulus': np.float32,
            'poisson_ratio': np.float32,
            'thermal_conductivity': np.float32,
            'electrical_conductivity': np.float32,
            'specific_heat': np.float32,
            'atomic_number': np.int32,
            'mass_number': np.int32,
            'atomic_mass': np.float32,
            'valence_electrons': np.float32,
            'electronegativity': np.float32,
            'ionization_energy': np.float32,
            'atomic_radius': np.float32,
            'covalent_radius': np.float32,
            'van_der_waals_radius': np.float32,
            'melting_temperature': np.float32,
            'boiling_temperature': np.float32,
            'heat_of_fusion': np.float32,
            'heat_of_vaporization': np.float32,
            'surface_energy': np.float32,
            'work_function': np.float32,
            'electron_affinity': np.float32,
            'ionization_potential': np.float32,
            'electron_configuration': str,
            'element_symbol': str,
            'element_name': str,
            'material_id': str,
            'formula': str,
            'structure': str,
            'space_group': str,
            'crystal_system': str,
            'lattice_parameters': str,
            'atomic_positions': str,
            'fractional_coordinates': str,
            'cartesian_coordinates': str,
            'symmetry_operations': str,
            'magnetic_ordering': str,
            'electronic_structure': str,
            'phonon_dispersion': str,
            'density_of_states': str,
            'band_structure': str,
            'fermi_level': np.float32,
            'valence_band_max': np.float32,
            'conduction_band_min': np.float32,
            'direct_gap': np.float32,
            'indirect_gap': np.float32,
            'effective_mass_e': np.float32,
            'effective_mass_h': np.float32,
            'carrier_concentration': np.float32,
            'mobility_e': np.float32,
            'mobility_h': np.float32,
            'diffusion_coefficient': np.float32,
            'reaction_rate': np.float32,
            'activation_energy': np.float32,
            'pre_exponential_factor': np.float32,
            'entropy': np.float32,
            'enthalpy': np.float32,
            'gibbs_free_energy': np.float32,
            'chemical_potential': np.float32,
            'osmotic_pressure': np.float32,
            'vapor_pressure': np.float32,
            'solubility': np.float32,
            'partition_coefficient': np.float32,
            'adsorption_energy': np.float32,
            'desorption_energy': np.float32,
            'catalytic_activity': np.float32,
            'selectivity': np.float32,
            'turnover_frequency': np.float32,
            'turnover_number': np.float32,
            'deactivation_rate': np.float32,
            'stability_constant': np.float32,
            'dissociation_constant': np.float32,
            'binding_energy': np.float32,
            'interaction_energy': np.float32,
            'cohesive_energy': np.float32,
            'sublimation_energy': np.float32,
            'atomization_energy': np.float32,
            'ionization_energy_1': np.float32,
            'ionization_energy_2': np.float32,
            'ionization_energy_3': np.float32,
            'electron_affinity_1': np.float32,
            'electron_affinity_2': np.float32,
            'electron_affinity_3': np.float32,
            'atomic_volume': np.float32,
            'molar_volume': np.float32,
            'specific_volume': np.float32,
            'compressibility': np.float32,
            'thermal_expansion': np.float32,
            'thermal_conductivity_e': np.float32,
            'thermal_conductivity_ph': np.float32,
            'electrical_resistivity': np.float32,
            'magnetic_susceptibility': np.float32,
            'dielectric_constant': np.float32,
            'refractive_index': np.float32,
            'optical_gap': np.float32,
            'absorption_coefficient': np.float32,
            'emission_wavelength': np.float32,
            'fluorescence_lifetime': np.float32,
            'quantum_yield': np.float32,
            'phosphorescence_lifetime': np.float32,
            'spin_lifetime': np.float32,
            'relaxation_time': np.float32,
            'diffusion_length': np.float32,
            'mean_free_path': np.float32,
            'scattering_rate': np.float32,
            'collision_frequency': np.float32,
            'thermal_velocity': np.float32,
            'sound_velocity': np.float32,
            'elastic_wave_velocity': np.float32,
            'shear_wave_velocity': np.float32,
            'compressional_wave_velocity': np.float32,
            'attenuation_coefficient': np.float32,
            'quality_factor': np.float32,
            'damping_ratio': np.float32,
            'loss_tangent': np.float32,
            'tan_delta': np.float32,
            'phase_angle': np.float32,
            'complex_modulus': np.float32,
            'storage_modulus': np.float32,
            'loss_modulus': np.float32,
            'creep_compliance': np.float32,
            'relaxation_modulus': np.float32,
            'viscosity': np.float32,
            'shear_viscosity': np.float32,
            'bulk_viscosity': np.float32,
            'kinematic_viscosity': np.float32,
            'dynamic_viscosity': np.float32,
            'surface_tension': np.float32,
            'interfacial_tension': np.float32,
            'wetting_angle': np.float32,
            'contact_angle': np.float32,
            'adhesion_energy': np.float32,
            'cohesion_energy': np.float32,
            'fracture_toughness': np.float32,
            'fracture_energy': np.float32,
            'crack_growth_rate': np.float32,
            'fatigue_limit': np.float32,
            'fatigue_life': np.float32,
            'endurance_limit': np.float32,
            'creep_rate': np.float32,
            'creep_strain': np.float32,
            'creep_stress': np.float32,
            'stress_relaxation': np.float32,
            'strain_rate': np.float32,
            'strain_hardening': np.float32,
            'strain_softening': np.float32,
            'necking_strain': np.float32,
            'uniform_elongation': np.float32,
            'total_elongation': np.float32,
            'reduction_of_area': np.float32,
            'yield_strength': np.float32,
            'ultimate_tensile_strength': np.float32,
            'compressive_strength': np.float32,
            'flexural_strength': np.float32,
            'torsional_strength': np.float32,
            'shear_strength': np.float32,
            'impact_strength': np.float32,
            'abrasion_resistance': np.float32,
            'wear_rate': np.float32,
            'friction_coefficient': np.float32,
            'lubricity': np.float32,
            'corrosion_rate': np.float32,
            'oxidation_rate': np.float32,
            'corrosion_potential': np.float32,
            'pitting_potential': np.float32,
            'passivation_potential': np.float32,
            'breakdown_potential': np.float32,
            'repassivation_potential': np.float32,
            'critical_pitting_temperature': np.float32,
            'critical_crevice_temperature': np.float32,
            'corrosion_current': np.float32,
            'corrosion_charge': np.float32,
            'corrosion_energy': np.float32,
            'corrosion_work': np.float32,
            'corrosion_power': np.float32,
            'corrosion_rate_mass': np.float32,
            'corrosion_rate_depth': np.float32,
            'corrosion_rate_volume': np.float32,
            'corrosion_rate_thickness': np.float32,
            'corrosion_rate_weight': np.float32,
            'corrosion_rate_area': np.float32,
            'corrosion_rate_length': np.float32,
            'corrosion_rate_time': np.float32,
            'corrosion_rate_temperature': np.float32,
            'corrosion_rate_pressure': np.float32,
            'corrosion_rate_humidity': np.float32,
            'corrosion_rate_ph': np.float32,
            'corrosion_rate_concentration': np.float32,
            'corrosion_rate_flow_rate': np.float32,
            'corrosion_rate_velocity': np.float32,
            'corrosion_rate_turbulence': np.float32,
            'corrosion_rate_erosion': np.float32,
            'corrosion_rate_impingement': np.float32,
            'corrosion_rate_cavitation': np.float32,
            'corrosion_rate_fretting': np.float32,
            'corrosion_rate_stress': np.float32,
            'corrosion_rate_strain': np.float32,
            'corrosion_rate_load': np.float32,
            'corrosion_rate_displacement': np.float32,
            'corrosion_rate_acceleration': np.float32,
            'corrosion_rate_frequency': np.float32,
            'corrosion_rate_amplitude': np.float32,
            'corrosion_rate_phase': np.float32,
            'corrosion_rate_duty_cycle': np.float32,
            'corrosion_rate_on_time': np.float32,
            'corrosion_rate_off_time': np.float32,
            'corrosion_rate_pulse_width': np.float32,
            'corrosion_rate_pulse_frequency': np.float32,
            'corrosion_rate_pulse_amplitude': np.float32,
            'corrosion_rate_pulse_phase': np.float32,
            'corrosion_rate_pulse_duty': np.float32,
            'corrosion_rate_pulse_on': np.float32,
            'corrosion_rate_pulse_off': np.float32,
            'corrosion_rate_pulse_width_time': np.float32,
            'corrosion_rate_pulse_freq_time': np.float32,
            'corrosion_rate_pulse_amp_time': np.float32,
            'corrosion_rate_pulse_phase_time': np.float32,
            'corrosion_rate_pulse_duty_time': np.float32,
            'corrosion_rate_pulse_on_time': np.float32,
            'corrosion_rate_pulse_off_time': np.float32,
            'corrosion_rate_pulse_width_freq': np.float32,
            'corrosion_rate_pulse_width_amp': np.float32,
            'corrosion_rate_pulse_width_phase': np.float32,
            'corrosion_rate_pulse_width_duty': np.float32,
            'corrosion_rate_pulse_width_on': np.float32,
            'corrosion_rate_pulse_width_off': np.float32,
            'corrosion_rate_pulse_freq_amp': np.float32,
            'corrosion_rate_pulse_freq_phase': np.float32,
            'corrosion_rate_pulse_freq_duty': np.float32,
            'corrosion_rate_pulse_freq_on': np.float32,
            'corrosion_rate_pulse_freq_off': np.float32,
            'corrosion_rate_pulse_amp_phase': np.float32,
            'corrosion_rate_pulse_amp_duty': np.float32,
            'corrosion_rate_pulse_amp_on': np.float32,
            'corrosion_rate_pulse_amp_off': np.float32,
            'corrosion_rate_pulse_phase_duty': np.float32,
            'corrosion_rate_pulse_phase_on': np.float32,
            'corrosion_rate_pulse_phase_off': np.float32,
            'corrosion_rate_pulse_duty_on': np.float32,
            'corrosion_rate_pulse_duty_off': np.float32,
            'corrosion_rate_pulse_on_off': np.float32,
            'corrosion_rate_pulse_width_freq_amp': np.float32,
            'corrosion_rate_pulse_width_freq_phase': np.float32,
            'corrosion_rate_pulse_width_freq_duty': np.float32,
            'corrosion_rate_pulse_width_freq_on': np.float32,
            'corrosion_rate_pulse_width_freq_off': np.float32,
            'corrosion_rate_pulse_width_amp_phase': np.float32,
            'corrosion_rate_pulse_width_amp_duty': np.float32,
            'corrosion_rate_pulse_width_amp_on': np.float32,
            'corrosion_rate_pulse_width_amp_off': np.float32,
            'corrosion_rate_pulse_width_phase_duty': np.float32,
            'corrosion_rate_pulse_width_phase_on': np.float32,
            'corrosion_rate_pulse_width_phase_off': np.float32,
            'corrosion_rate_pulse_width_duty_on': np.float32,
            'corrosion_rate_pulse_width_duty_off': np.float32,
            'corrosion_rate_pulse_width_on_off': np.float32,
            'corrosion_rate_pulse_freq_amp_phase': np.float32,
            'corrosion_rate_pulse_freq_amp_duty': np.float32,
            'corrosion_rate_pulse_freq_amp_on': np.float32,
            'corrosion_rate_pulse_freq_amp_off': np.float32,
            'corrosion_rate_pulse_freq_phase_duty': np.float32,
            'corrosion_rate_pulse_freq_phase_on': np.float32,
            'corrosion_rate_pulse_freq_phase_off': np.float32,
            'corrosion_rate_pulse_freq_duty_on': np.float32,
            'corrosion_rate_pulse_freq_duty_off': np.float32,
            'corrosion_rate_pulse_freq_on_off': np.float32,
            'corrosion_rate_pulse_amp_phase_duty': np.float32,
            'corrosion_rate_pulse_amp_phase_on': np.float32,
            'corrosion_rate_pulse_amp_phase_off': np.float32,
            'corrosion_rate_pulse_amp_duty_on': np.float32,
            'corrosion_rate_pulse_amp_duty_off': np.float32,
            'corrosion_rate_pulse_amp_on_off': np.float32,
            'corrosion_rate_pulse_phase_duty_on': np.float32,
            'corrosion_rate_pulse_phase_duty_off': np.float32,
            'corrosion_rate_pulse_phase_on_off': np.float32,
            'corrosion_rate_pulse_duty_on_off': np.float32,
            'corrosion_rate_pulse_width_freq_amp_phase': np.float32,
            'corrosion_rate_pulse_width_freq_amp_duty': np.float32,
            'corrosion_rate_pulse_width_freq_amp_on': np.float32,
            'corrosion_rate_pulse_width_freq_amp_off': np.float32,
            'corrosion_rate_pulse_width_freq_phase_duty': np.float32,
            'corrosion_rate_pulse_width_freq_phase_on': np.float32,
            'corrosion_rate_pulse_width_freq_phase_off': np.float32,
            'corrosion_rate_pulse_width_freq_duty_on': np.float32,
            'corrosion_rate_pulse_width_freq_duty_off': np.float32,
            'corrosion_rate_pulse_width_freq_on_off': np.float32,
            'corrosion_rate_pulse_width_amp_phase_duty': np.float32,
            'corrosion_rate_pulse_width_amp_phase_on': np.float32,
            'corrosion_rate_pulse_width_amp_phase_off': np.float32,
            'corrosion_rate_pulse_width_amp_duty_on': np.float32,
            'corrosion_rate_pulse_width_amp_duty_off': np.float32,
            'corrosion_rate_pulse_width_amp_on_off': np.float32,
            'corrosion_rate_pulse_width_phase_duty_on': np.float32,
            'corrosion_rate_pulse_width_phase_duty_off': np.float32,
            'corrosion_rate_pulse_width_phase_on_off': np.float32,
            'corrosion_rate_pulse_width_duty_on_off': np.float32,
            'corrosion_rate_pulse_width_on_off_time': np.float32,
            'corrosion_rate_pulse_freq_amp_phase_duty': np.float32,
            'corrosion_rate_pulse_freq_amp_phase_on': np.float32,
            'corrosion_rate_pulse_freq_amp_phase_off': np.float32,
            'corrosion_rate_pulse_freq_amp_duty_on': np.float32,
            'corrosion_rate_pulse_freq_amp_duty_off': np.float32,
            'corrosion_rate_pulse_freq_amp_on_off': np.float32,
            'corrosion_rate_pulse_freq_phase_duty_on': np.float32,
            'corrosion_rate_pulse_freq_phase_duty_off': np.float32,
            'corrosion_rate_pulse_freq_phase_on_off': np.float32,
            'corrosion_rate_pulse_freq_duty_on_off': np.float32,
            'corrosion_rate_pulse_freq_on_off_time': np.float32,
            'corrosion_rate_pulse_amp_phase_duty_on': np.float32,
            'corrosion_rate_pulse_amp_phase_duty_off': np.float32,
            'corrosion_rate_pulse_amp_phase_on_off': np.float32,
            'corrosion_rate_pulse_amp_duty_on_off': np.float32,
            'corrosion_rate_pulse_amp_on_off_time': np.float32,
            'corrosion_rate_pulse_phase_duty_on_off': np.float32,
            'corrosion_rate_pulse_phase_on_off_time': np.float32,
            'corrosion_rate_pulse_duty_on_off_time': np.float32,
            'corrosion_rate_pulse_on_off_time': np.float32,
            'corrosion_rate_pulse_width_freq_amp_phase_duty': np.float32,
            'corrosion_rate_pulse_width_freq_amp_phase_on': np.float32,
            'corrosion_rate_pulse_width_freq_amp_phase_off': np.float32,
            'corrosion_rate_pulse_width_freq_amp_duty_on': np.float32,
            'corrosion_rate_pulse_width_freq_amp_duty_off': np.float32,
            'corrosion_rate_pulse_width_freq_amp_on_off': np.float32,
            'corrosion_rate_pulse_width_freq_phase_duty_on': np.float32,
            'corrosion_rate_pulse_width_freq_phase_duty_off': np.float32,
            'corrosion_rate_pulse_width_freq_phase_on_off': np.float32,
            'corrosion_rate_pulse_width_freq_duty_on_off': np.float32,
            'corrosion_rate_pulse_width_freq_on_off_time': np.float32,
            'corrosion_rate_pulse_width_amp_phase_duty_on': np.float32,
            'corrosion_rate_pulse_width_amp_phase_duty_off': np.float32,
            'corrosion_rate_pulse_width_amp_phase_on_off': np.float32,
            'corrosion_rate_pulse_width_amp_duty_on_off': np.float32,
            'corrosion_rate_pulse_width_amp_on_off_time': np.float32,
            'corrosion_rate_pulse_width_phase_duty_on_off': np.float32,
            'corrosion_rate_pulse_width_phase_on_off_time': np.float32,
            'corrosion_rate_pulse_width_duty_on_off_time': np.float32,
            'corrosion_rate_pulse_width_on_off_time_time': np.float32,
            'corrosion_rate_pulse_freq_amp_phase_duty_on': np.float32,
            'corrosion_rate_pulse_freq_amp_phase_duty_off': np.float32,
            'corrosion_rate_pulse_freq_amp_phase_on_off': np.float32,
            'corrosion_rate_pulse_freq_amp_duty_on_off': np.float32,
            'corrosion_rate_pulse_freq_amp_on_off_time': np.float32,
            'corrosion_rate_pulse_freq_phase_duty_on_off': np.float32,
            'corrosion_rate_pulse_freq_phase_on_off_time': np.float32,
            'corrosion_rate_pulse_freq_duty_on_off_time': np.float32,
            'corrosion_rate_pulse_freq_on_off_time_time': np.float32,
            'corrosion_rate_pulse_amp_phase_duty_on_off': np.float32,
            'corrosion_rate_pulse_amp_phase_on_off_time': np.float32,
            'corrosion_rate_pulse_amp_duty_on_off_time': np.float32,
            'corrosion_rate_pulse_amp_on_off_time_time': np.float32,
            'corrosion_rate_pulse_phase_duty_on_off_time': np.float32,
            'corrosion_rate_pulse_phase_on_off_time_time': np.float32,
            'corrosion_rate_pulse_duty_on_off_time_time': np.float32,
            'corrosion_rate_pulse_on_off_time_time': np.float32
        }

    total_rows = 0
    total_files = 0
    processed_files = []
    
    # Track peak memory usage
    import resource
    initial_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Convert KB to MB
    peak_memory = initial_memory
    
    # Process each property file
    for prop in properties:
        # Find matching files in raw_dir
        prop_files = list(raw_dir.glob(f"*{prop}*.csv")) + list(raw_dir.glob(f"*{prop}*.parquet"))
        
        for file_path in prop_files:
            logger.info(f"Processing {file_path.name}...")
            try:
                # Read in chunks to manage memory
                if file_path.suffix == '.csv':
                    chunks = pd.read_csv(file_path, chunksize=chunk_size)
                elif file_path.suffix == '.parquet':
                    # Parquet can be read in chunks if it's large
                    chunks = pd.read_parquet(file_path, engine='pyarrow')
                    # If it's too big, we might need to handle differently
                    if len(chunks) > chunk_size:
                        # Fallback to chunked reading if possible
                        chunks = [chunks.iloc[i:i+chunk_size] for i in range(0, len(chunks), chunk_size)]
                    else:
                        chunks = [chunks]
                else:
                    logger.warning(f"Skipping unsupported file format: {file_path.suffix}")
                    continue
                
                # Process each chunk
                for i, chunk in enumerate(chunks):
                    # Apply dtype optimization
                    for col, dtype in dtype_map.items():
                        if col in chunk.columns:
                            try:
                                chunk[col] = chunk[col].astype(dtype)
                            except (ValueError, TypeError) as e:
                                logger.debug(f"Could not convert {col} to {dtype}: {e}")
                    
                    # Save processed chunk
                    processed_file = processed_dir / f"{file_path.stem}_chunk_{i}.parquet"
                    chunk.to_parquet(processed_file, index=False)
                    processed_files.append(processed_file)
                    
                    total_rows += len(chunk)
                    total_files += 1
                    
                    # Check memory usage
                    current_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
                    if current_memory > peak_memory:
                        peak_memory = current_memory
                    
                    # Force garbage collection periodically
                    if i % 10 == 0:
                        gc.collect()
                        
                    # Log progress
                    if i % 50 == 0:
                        logger.info(f"Processed {i+1} chunks of {file_path.name}, "
                                  f"total rows: {total_rows}, "
                                  f"peak RAM: {peak_memory:.1f}MB")
                    
                    # Safety check for RAM
                    if peak_memory > 7000:  # 7GB in MB
                        logger.error(f"Peak RAM exceeded 7GB limit: {peak_memory:.1f}MB")
                        raise MemoryError(f"Peak RAM exceeded 7GB limit: {peak_memory:.1f}MB")
                        
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                raise
    
    logger.info(f"Processing complete. Total files: {total_files}, Total rows: {total_rows}")
    logger.info(f"Peak RAM usage: {peak_memory:.1f}MB")
    
    return total_rows, total_files

def download_all_datasets(
    hf_token: str,
    data_dir: Path,
    properties: List[str],
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Download all datasets for specified properties from HuggingFace.
    
    Args:
        hf_token: HuggingFace API token
        data_dir: Base data directory
        properties: List of property names to download
        raw_dir: Directory for raw downloads (default: data_dir/raw)
        processed_dir: Directory for processed data (default: data_dir/processed)
    
    Returns:
        Dictionary with download statistics
    """
    if raw_dir is None:
        raw_dir = data_dir / "raw"
    if processed_dir is None:
        processed_dir = data_dir / "processed"
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Define datasets to download (example: Materials Project, AFLOW)
    datasets = [
        {
            'repo_id': 'materials-project/mp-structures',
            'description': 'Materials Project crystal structures'
        },
        {
            'repo_id': 'aflow/aflow-database',
            'description': 'AFLOW materials database'
        }
    ]
    
    stats = {
        'total_datasets': len(datasets),
        'successful_downloads': 0,
        'failed_downloads': 0,
        'total_files': 0,
        'total_rows': 0,
        'peak_ram_mb': 0.0
    }
    
    import resource
    initial_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    peak_memory = initial_memory
    
    for dataset in datasets:
        repo_id = dataset['repo_id']
        logger.info(f"Processing dataset: {repo_id}")
        
        try:
            # Fetch metadata
            files = fetch_dataset_metadata(hf_token, repo_id)
            logger.info(f"Found {len(files)} files in {repo_id}")
            
            # Download relevant files
            for file_name in files:
                # Check if file is relevant to our properties
                is_relevant = any(prop.lower() in file_name.lower() for prop in properties)
                if not is_relevant:
                    # Still download common data files
                    if file_name.endswith(('.csv', '.parquet', '.json')):
                        is_relevant = True
                
                if is_relevant:
                    local_path = download_with_retry(
                        hf_token=hf_token,
                        repo_id=repo_id,
                        filename=file_name,
                        local_dir=raw_dir
                    )
                    
                    if local_path:
                        stats['successful_downloads'] += 1
                        stats['total_files'] += 1
                        
                        # Check memory
                        current_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
                        if current_memory > peak_memory:
                            peak_memory = current_memory
                            stats['peak_ram_mb'] = peak_memory
                            
                        # Safety check
                        if peak_memory > 7000:
                            logger.error(f"Peak RAM exceeded 7GB: {peak_memory:.1f}MB")
                            raise MemoryError(f"Peak RAM exceeded 7GB: {peak_memory:.1f}MB")
                        
            stats['successful_downloads'] += 1
            
        except Exception as e:
            logger.error(f"Failed to process dataset {repo_id}: {e}")
            stats['failed_downloads'] += 1
    
    # Process downloaded files
    if stats['successful_downloads'] > 0:
        rows, files = process_property_files(
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            properties=properties
        )
        stats['total_rows'] = rows
        stats['processed_files'] = files
        
        # Check final memory
        current_memory = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        if current_memory > peak_memory:
            stats['peak_ram_mb'] = current_memory
        else:
            stats['peak_ram_mb'] = peak_memory
        
        # Verify RAM constraint
        if stats['peak_ram_mb'] > 7000:
            raise MemoryError(f"Peak RAM exceeded 7GB limit: {stats['peak_ram_mb']:.1f}MB")
    
    logger.info(f"Download complete. Stats: {stats}")
    return stats

def main():
    """Main entry point for data download and processing."""
    logger.info("Starting data download and processing...")
    
    try:
        # Get configuration
        config = get_config()
        hf_token = require_hf_token(config)
        data_dir = require_data_dir(config)
        state_dir = require_state_dir(config)
        
        # Define properties to download (based on project scope)
        properties = [
            'formation_energy', 'band_gap', 'magnetic_moment', 
            'volume', 'density', 'energy_per_atom', 'total_energy',
            'melting_point', 'hardness', 'elastic_modulus'
        ]
        
        # Download and process datasets
        stats = download_all_datasets(
            hf_token=hf_token,
            data_dir=Path(data_dir),
            properties=properties
        )
        
        # Log final results
        logger.info(f"Download statistics: {stats}")
        
        # Verify RAM constraint
        if stats.get('peak_ram_mb', 0) > 7000:
            raise MemoryError(f"RAM constraint violated: {stats['peak_ram_mb']:.1f}MB > 7GB")
        
        logger.info("Data download and processing completed successfully!")
        print(f"Download completed. Peak RAM: {stats.get('peak_ram_mb', 0):.1f}MB")
        print(f"Total files: {stats.get('total_files', 0)}")
        print(f"Total rows: {stats.get('total_rows', 0)}")
        
    except MemoryError as e:
        logger.error(f"RAM constraint violation: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()