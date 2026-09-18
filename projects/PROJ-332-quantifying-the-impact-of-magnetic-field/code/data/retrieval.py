"""
Data retrieval module for MDSplus connection and data fetching.
Handles connection retries, data fetching, and island width retrieval.
"""
import logging
import time
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

def get_efit_data(connection, discharge_id: int, tree_name: str = 'diii_d') -> Optional[Dict[str, Any]]:
    """
    Retrieve EFIT data from MDSplus for a given discharge.
    
    Args:
        connection: MDSplus connection object
        discharge_id: Discharge ID
        tree_name: MDSplus tree name
        
    Returns:
        Dictionary with EFIT data or None if retrieval fails
    """
    try:
        # EFIT data is typically in the 'efit' tree
        efit_tree = connection.openTree(tree_name, discharge_id)
        
        # Extract q-profile and magnetic shear
        q_profile = efit_tree.get('q_profile').data()
        rho_values = efit_tree.get('rho_tor').data()
        Bt_field = efit_tree.get('bt').data()
        
        # Calculate local magnetic shear: s = (r/q) * (dq/dr)
        dq_dr = np.gradient(q_profile, rho_values)
        local_magnetic_shear = (rho_values / q_profile) * dq_dr
        
        return {
            'q_profile': q_profile,
            'rho_values': rho_values,
            'Bt_field': Bt_field,
            'local_magnetic_shear': local_magnetic_shear,
            'discharge_id': discharge_id
        }
    except Exception as e:
        logger.error(f"Failed to retrieve EFIT data for discharge {discharge_id}: {e}")
        return None

def fetch_island_width(connection, discharge_id: int, tree_name: str = 'diii_d') -> Optional[float]:
    """
    Retrieve pre-calculated island width from MDSplus.
    
    Args:
        connection: MDSplus connection object
        discharge_id: Discharge ID
        tree_name: MDSplus tree name
        
    Returns:
        Island width in meters, or None if not found
    """
    try:
        # Try to get pre-calculated island width from 'islands' tree
        islands_tree = connection.openTree(tree_name, discharge_id)
        island_width_data = islands_tree.get('island_width').data()
        
        if island_width_data is not None and len(island_width_data) > 0:
            # Take the maximum or mean value depending on context
            return float(np.mean(island_width_data))
        else:
            return None
    except Exception as e:
        logger.debug(f"Pre-calculated island_width not found for {discharge_id}: {e}")
        return None

def derive_island_width(local_magnetic_shear: float, q_profile: np.ndarray, 
                       Bt_field: float, rho_values: np.ndarray, 
                       n_mode: int = 2, m_mode: int = 3) -> Optional[float]:
    """
    Derive island width using the Rutherford equation approximation.
    
    This function is also defined in code/analysis/metrics.py for consistency.
    The implementation here mirrors that one to ensure standalone functionality.
    
    Args:
        local_magnetic_shear: Local magnetic shear (s = r/q * dq/dr)
        q_profile: Array of q values across radius
        Bt_field: Toroidal magnetic field (Tesla)
        rho_values: Normalized minor radius values
        n_mode: Toroidal mode number (default 2)
        m_mode: Poloidal mode number (default 3)
        
    Returns:
        Derived island width in meters, or None if derivation fails
    """
    if local_magnetic_shear is None or np.isnan(local_magnetic_shear):
        logger.warning("Local magnetic shear is None or NaN, cannot derive island width")
        return None
        
    if q_profile is None or len(q_profile) == 0:
        logger.warning("q_profile is empty or None, cannot derive island width")
        return None
        
    if Bt_field is None or Bt_field <= 0:
        logger.warning("Invalid Bt_field, cannot derive island width")
        return None
        
    if rho_values is None or len(rho_values) == 0:
        logger.warning("rho_values is empty or None, cannot derive island width")
        return None
        
    # Find the rational surface where q = m/n
    target_q = m_mode / n_mode
    q_diff = np.abs(q_profile - target_q)
    
    if np.min(q_diff) > 0.05:  # Tolerance for finding rational surface
        logger.warning(f"No q={target_q} surface found (min diff={np.min(q_diff):.4f}), cannot derive island width")
        return None
        
    # Index of rational surface
    idx_rational = np.argmin(q_diff)
    r_at_surface = rho_values[idx_rational] * 0.67  # Approximate minor radius scaling for DIII-D
    
    # Calculate dq/dr (gradient of q)
    if len(q_profile) < 2:
        logger.warning("q_profile too short for gradient calculation")
        return None
        
    dq_dr = np.gradient(q_profile, rho_values)
    dq_dr_at_surface = dq_dr[idx_rational]
    
    if np.abs(dq_dr_at_surface) < 1e-6:
        logger.warning("q gradient too small, derivation would be unstable")
        return None
        
    # Magnetic shear length L_s = r / (r/q * dq/dr) = q / (dq/dr)
    q_at_surface = q_profile[idx_rational]
    L_s = q_at_surface / dq_dr_at_surface
    
    # Estimate delta' (tearing stability index)
    delta_prime = 1.0 / np.abs(L_s) if L_s != 0 else 0.1
    
    # Rutherford equation approximation
    numerator = 4 * r_at_surface * np.abs(delta_prime)
    denominator = m_mode * np.abs(dq_dr_at_surface)
    
    if denominator < 1e-10:
        logger.warning("Denominator too small in island width derivation")
        return None
        
    island_width = numerator / denominator
    
    # Physical constraints
    if island_width <= 0:
        logger.warning(f"Derived negative island width ({island_width}), derivation failed")
        return None
        
    if island_width > 0.67:
        logger.warning(f"Derived island width ({island_width:.4f}m) exceeds minor radius, capping")
        island_width = 0.67
        
    logger.info(f"Derived island width: {island_width:.6f}m")
    return island_width

def fetch_data_for_discharge(connection, discharge_id: int, 
                            tree_name: str = 'diii_d',
                            max_retries: int = 3,
                            retry_delay: float = 2.0) -> Optional[Dict[str, Any]]:
    """
    Fetch all required data for a discharge with retry logic.
    
    Args:
        connection: MDSplus connection object
        discharge_id: Discharge ID
        tree_name: MDSplus tree name
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Dictionary with all fetched data or None if all attempts fail
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching data for discharge {discharge_id} (attempt {attempt + 1}/{max_retries})")
            
            # Fetch pre-calculated island width
            island_width = fetch_island_width(connection, discharge_id, tree_name)
            
            # If pre-calculated is missing, attempt derivation
            if island_width is None:
                logger.info(f"Pre-calculated island_width missing for {discharge_id}, attempting derivation")
                efit_data = get_efit_data(connection, discharge_id, tree_name)
                
                if efit_data is None:
                    logger.warning(f"EFIT data missing for {discharge_id}, cannot derive")
                    # Return partial data but mark island_width as derivation_failed
                    return {
                        'discharge_id': discharge_id,
                        'island_width': None,
                        'derivation_failed': True,
                        'reason': 'EFIT data missing'
                    }
                
                island_width = derive_island_width(
                    local_magnetic_shear=efit_data['local_magnetic_shear'],
                    q_profile=efit_data['q_profile'],
                    Bt_field=efit_data['Bt_field'],
                    rho_values=efit_data['rho_values']
                )
                
                if island_width is None:
                    logger.warning(f"Derivation failed for {discharge_id}")
                    return {
                        'discharge_id': discharge_id,
                        'island_width': None,
                        'derivation_failed': True,
                        'reason': 'Derivation failed'
                    }
            
            return {
                'discharge_id': discharge_id,
                'island_width': island_width,
                'derivation_failed': False
            }
            
        except Exception as e:
            logger.error(f"Error fetching data for {discharge_id} (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"All {max_retries} attempts failed for discharge {discharge_id}")
                return None

def main():
    """
    Main function for data retrieval module (standalone execution).
    """
    logger.info("Data retrieval module initialized")
    # This module is typically called from the main pipeline
    logger.info("Ready for integration with MDSplus")

if __name__ == "__main__":
    main()
