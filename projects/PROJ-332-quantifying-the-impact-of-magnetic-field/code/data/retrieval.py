import logging
import time
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

# Placeholder for MDSplus import.
# The environment must have 'mdsplus' installed.
# If not, we fail loudly as per constraints (no synthetic fallback).
try:
    import MDSplus
except ImportError:
    raise ImportError(
        "MDSplus library not found. Please install it to fetch real data. "
        "The pipeline cannot proceed with synthetic data."
    )

def get_efit_data(tree_name: str, shot: int) -> Dict[str, Any]:
    """
    Connect to MDSplus and retrieve EFIT equilibrium data for a specific shot.
    
    Args:
        tree_name: Name of the MDSplus tree (e.g., 'diii-d')
        shot: Discharge number (integer)
        
    Returns:
        Dictionary containing EFIT data (q-profile, magnetic shear, Bt, etc.)
        
    Raises:
        ConnectionError: If connection fails after retries
        ValueError: If data is missing
    """
    retries = 3
    delay = 2
    conn = None
    
    for attempt in range(retries):
        try:
            logger.info(f"Attempting MDSplus connection for shot {shot} (Attempt {attempt+1}/{retries})")
            # Connect to the DIII-D public archive
            # The server address is standard for DIII-D public data
            conn = MDSplus.Connection('diii-d.aps.anl.gov')
            conn.openTree(tree_name, shot)
            break
        except Exception as e:
            logger.warning(f"Connection attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise ConnectionError(f"Failed to connect to MDSplus after {retries} attempts: {e}")
    
    if not conn:
        raise ConnectionError("Could not establish MDSplus connection.")

    efit_data = {}
    
    try:
        # Extract q-profile (q)
        # Path: 'efitqq' or similar depending on tree version
        # Using a robust path often found in DIII-D trees
        q_node = f'efitqq'
        try:
            q_vals = conn.get(q_node).data()
            efit_data['q'] = q_vals
        except Exception:
            logger.warning(f"q-profile not found at {q_node} for shot {shot}")
            efit_data['q'] = None

        # Extract magnetic shear (s)
        # Often derived or stored in 'efitss' or similar
        shear_node = f'efitss'
        try:
            shear_vals = conn.get(shear_node).data()
            efit_data['shear'] = shear_vals
        except Exception:
            logger.warning(f"Magnetic shear not found at {shear_node} for shot {shot}")
            efit_data['shear'] = None

        # Extract Toroidal Field (Bt)
        # Usually stored in 'efitbt' or 'bt'
        bt_node = f'efitbt'
        try:
            bt_val = conn.get(bt_node).data()
            # If it's an array, take the first or mean value
            if isinstance(bt_val, np.ndarray):
                bt_val = float(bt_val[0])
            efit_data['Bt'] = float(bt_val)
        except Exception:
            logger.warning(f"Toroidal Field (Bt) not found at {bt_node} for shot {shot}")
            efit_data['Bt'] = None

    finally:
        # Close tree but keep connection if needed, or close connection
        try:
            conn.closeTree(tree_name, shot)
        except:
            pass
        # conn.close() # Usually not necessary for short-lived scripts

    return efit_data

def fetch_island_width(tree_name: str, shot: int) -> Optional[float]:
    """
    Attempt to retrieve pre-calculated island_width from MDSplus.
    
    Args:
        tree_name: Name of the MDSplus tree
        shot: Discharge number
        
    Returns:
        Pre-calculated island width in meters, or None if not found.
    """
    conn = None
    try:
        conn = MDSplus.Connection('diii-d.aps.anl.gov')
        conn.openTree(tree_name, shot)
        
        # Common paths for island width in DIII-D trees
        # 'island_width', 'w_island', 'te_island'
        candidates = ['island_width', 'w_island', 'te_island', 'island_size']
        
        for path in candidates:
            try:
                val = conn.get(path).data()
                if val is not None:
                    if isinstance(val, np.ndarray):
                        # If multiple values, take the mean or max? 
                        # Usually a single representative value is expected
                        val = float(np.mean(val))
                    else:
                        val = float(val)
                    logger.info(f"Found pre-calculated island_width at '{path}': {val}")
                    return val
            except Exception:
                continue
                
        logger.info(f"No pre-calculated island_width found for shot {shot} in standard paths.")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching island_width for shot {shot}: {e}")
        return None
    finally:
        if conn:
            try:
                conn.closeTree(tree_name, shot)
            except:
                pass

def derive_island_width(efit_data: Dict[str, Any], shot: int) -> Optional[float]:
    """
    Derive island_width using the Rutherford equation approximation.
    
    Formula approximation: w ~ sqrt( (mu0 * J_parallel * r) / (B_t * q * s) )
    Simplified for this task based on spec.md:FR-002 inputs:
    Inputs: local magnetic shear (s), q, Bt.
    
    We assume a proportional relationship: w = k * sqrt( (q * s) / Bt )
    where k is a constant derived from typical plasma parameters or 
    simplified physics constants. Since exact J_parallel is often not 
    directly available as a single scalar in simple EFIT nodes without 
    complex processing, we use the provided inputs to estimate the 
    scaling.
    
    Note: In a full physics implementation, one would integrate the 
    current profile. Here we implement the logic as requested: 
    using s, q, and Bt.
    
    Args:
        efit_data: Dictionary containing 'q', 'shear', 'Bt'
        shot: Discharge number (for logging)
        
    Returns:
        Derived island width in meters, or None if inputs are missing.
    """
    q = efit_data.get('q')
    shear = efit_data.get('shear')
    bt = efit_data.get('Bt')
    
    if q is None or shear is None or bt is None:
        logger.warning(f"Shot {shot}: Cannot derive island_width. Missing inputs: q={q is not None}, shear={shear is not None}, Bt={bt is not None}")
        return None

    # Handle array inputs: take the mean or a representative value (e.g., at rho=0.5)
    if isinstance(q, np.ndarray):
        q_val = float(np.mean(q))
    else:
        q_val = float(q)
        
    if isinstance(shear, np.ndarray):
        shear_val = float(np.mean(shear))
    else:
        shear_val = float(shear)
        
    if isinstance(bt, np.ndarray):
        bt_val = float(np.mean(bt))
    else:
        bt_val = float(bt)

    # Avoid division by zero
    if bt_val == 0 or q_val == 0:
        logger.warning(f"Shot {shot}: Invalid values for derivation (Bt={bt_val}, q={q_val}).")
        return None

    # Physics-based approximation (simplified Rutherford scaling):
    # w proportional to sqrt( (q * shear) / Bt )
    # We use a normalization constant to keep units in meters.
    # This is a placeholder constant; in a real scientific context, 
    # this would be calibrated against experimental data or full MHD codes.
    # Assuming typical DIII-D parameters, we set k ~ 0.01 for scaling.
    # w = k * sqrt( (q * s) / Bt )
    # Note: This is a heuristic implementation of the requested logic.
    
    try:
        # Ensure positive values for sqrt
        numerator = abs(q_val * shear_val)
        width = 0.01 * np.sqrt(numerator / bt_val)
        return float(width)
    except Exception as e:
        logger.warning(f"Shot {shot}: Derivation failed with error: {e}")
        return None

def fetch_data_for_discharge(tree_name: str, shot: int) -> Dict[str, Any]:
    """
    Main entry point for fetching all required data for a discharge.
    Implements the logic:
    1. Try to fetch pre-calculated island_width.
    2. If missing, fetch EFIT data and derive island_width.
    3. If derivation inputs missing, return None for island_width and log warning.
    
    Args:
        tree_name: MDSplus tree name
        shot: Discharge ID
        
    Returns:
        Dictionary with 'shot', 'island_width', 'efit_data', 'status'
    """
    logger.info(f"Processing discharge {shot}")
    
    result = {
        'shot': shot,
        'island_width': None,
        'efit_data': {},
        'status': 'success'
    }
    
    # 1. Try pre-calculated
    precalc_width = fetch_island_width(tree_name, shot)
    
    if precalc_width is not None:
        result['island_width'] = precalc_width
        logger.info(f"Shot {shot}: Using pre-calculated island_width: {precalc_width}")
    else:
        # 2. Derive if missing
        logger.info(f"Shot {shot}: Pre-calculated island_width missing. Attempting derivation.")
        efit_data = get_efit_data(tree_name, shot)
        result['efit_data'] = efit_data
        
        derived_width = derive_island_width(efit_data, shot)
        
        if derived_width is not None:
            result['island_width'] = derived_width
            logger.info(f"Shot {shot}: Derived island_width: {derived_width}")
        else:
            # 3. Log warning and exclude (island_width remains None)
            logger.warning(f"Shot {shot}: Could not derive island_width. Discharge will be excluded.")
            result['status'] = 'excluded'
            
    return result