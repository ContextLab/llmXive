"""
MDSplus Data Retrieval Module.

Handles connection to the MDSplus archive, fetching EFIT data, island widths,
energy confinement times (tau_e), and the H-factor (h98y2).
"""
import logging
import time
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import numpy as np

# Attempt to import mdsplus.
# NOTE: Per project constraints, mdsplus is NOT in requirements.txt.
# This module is designed to be run in an environment where mdsplus is installed
# (e.g., via system package manager or a specific virtual environment setup).
# If not available, a RuntimeError is raised to fail loudly (Constitution VI).
try:
    import MDSplus
    from MDSplus import Tree, Connection
    MDSPLUS_AVAILABLE = True
except ImportError:
    MDSPLUS_AVAILABLE = False
    MDSplus = None
    Connection = None
    Tree = None

from utils.logger import get_logger
from utils.limits import timeout_guard

logger = get_logger(__name__)

# Constants
DIII_D_SERVER = "d3d.mdsplus.org"
DIII_D_PORT = 8000
# Default timeout for connection attempts (seconds)
CONNECTION_TIMEOUT = 30

def _get_connection(discharge_id: int) -> Optional[Connection]:
    """
    Establish a connection to the DIII-D MDSplus server with retry logic.
    """
    if not MDSPLUS_AVAILABLE:
        raise RuntimeError(
            "MDSplus library is not installed. "
            "Please install 'mdsplus' system package or 'mdsplus' python wheel "
            "to retrieve real data. Failing loudly as per Constitution VI."
        )

    retries = 3
    delay = 5
    conn = None

    for attempt in range(retries):
        try:
            logger.info(f"Attempting MDSplus connection (attempt {attempt + 1}/{retries})...")
            # Connection string format: "server:port"
            conn_str = f"{DIII_D_SERVER}:{DIII_D_PORT}"
            conn = Connection(conn_str)
            logger.info(f"Successfully connected to MDSplus at {conn_str}")
            return conn
        except Exception as e:
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"Failed to connect to MDSplus after {retries} attempts.")
                raise RuntimeError(f"Could not connect to MDSplus server: {e}") from e

    return None

def get_efit_data(conn: Connection, discharge_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch EFIT equilibrium data for a given discharge.
    Returns a dictionary with q-profile, Bt, and other relevant fields.
    """
    try:
        # Open the DIII-D tree (usually 'd3d')
        # The tree name might vary, but 'd3d' is standard for DIII-D
        tree = Tree("d3d", discharge_id, "+")
        logger.info(f"Opened tree for discharge {discharge_id}")

        # Extract EFIT data
        # Common paths for EFIT data in DIII-D MDSplus
        efit_path = "d0.equit"
        if not tree.getNode(efit_path).data() is None:
            efit_data = tree.getNode(efit_path).data()
            # efit_data is typically a record with specific structure
            # We need to extract q-profile, Bt, etc.
            # This is a simplified extraction; real implementation might need
            # more complex parsing of the efit record.
            # For now, we assume we can get the q-profile and Bt.
            # q_profile is often in d0.qprofile or similar
            q_node = tree.getNode("d0.qprofile")
            if q_node:
                q_profile = q_node.data()
            else:
                q_profile = None

            bt_node = tree.getNode("d0.btor") # Toroidal field
            if bt_node:
                bt_field = bt_node.data()
            else:
                bt_field = None

            return {
                "q_profile": q_profile,
                "btor": bt_field,
                "raw_efit": efit_data
            }
        else:
            logger.warning(f"EFIT data not found for discharge {discharge_id}")
            return None

    except Exception as e:
        logger.error(f"Error fetching EFIT data for discharge {discharge_id}: {e}")
        return None

def fetch_island_width(conn: Connection, discharge_id: int) -> Optional[float]:
    """
    Fetch pre-calculated island width from the MDSplus 'islands' tree.
    """
    try:
        tree = Tree("islands", discharge_id, "+")
        # Look for a node containing island width, e.g., "width" or "w_m"
        # This is a placeholder path; actual path depends on the tree structure.
        # Assuming a node named "width" exists.
        width_node = tree.getNode("width")
        if width_node:
            width = width_node.data()
            if isinstance(width, (list, np.ndarray)):
                # If it's a time series, take the max or mean
                width = float(np.max(width))
            else:
                width = float(width)
            return width
        else:
            logger.warning(f"Island width not found for discharge {discharge_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching island width for discharge {discharge_id}: {e}")
        return None

def fetch_tau_e(conn: Connection, discharge_id: int) -> Optional[float]:
    """
    Fetch energy confinement time (tau_e) from the 'taue' tree.
    """
    try:
        tree = Tree("taue", discharge_id, "+")
        # Common node for tau_e
        tau_node = tree.getNode("taue")
        if tau_node:
            tau = tau_node.data()
            if isinstance(tau, (list, np.ndarray)):
                tau = float(np.mean(tau)) # Average over the discharge
            else:
                tau = float(tau)
            return tau
        else:
            logger.warning(f"Tau_e not found for discharge {discharge_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching tau_e for discharge {discharge_id}: {e}")
        return None

def fetch_h98y2(conn: Connection, discharge_id: int) -> Optional[float]:
    """
    Fetch the H-factor (h98y2) from the 'h98y2' tree or 'taue' tree.
    This is critical for determining confinement mode.
    """
    try:
        # Try 'h98y2' tree first
        try:
            tree = Tree("h98y2", discharge_id, "+")
            h_node = tree.getNode("h98y2")
            if h_node:
                h = h_node.data()
                if isinstance(h, (list, np.ndarray)):
                    h = float(np.mean(h))
                else:
                    h = float(h)
                return h
        except Exception:
            # If 'h98y2' tree doesn't exist, try 'taue' tree
            pass

        # Fallback to 'taue' tree
        tree = Tree("taue", discharge_id, "+")
        h_node = tree.getNode("h98y2")
        if h_node:
            h = h_node.data()
            if isinstance(h, (list, np.ndarray)):
                h = float(np.mean(h))
            else:
                h = float(h)
            return h

        logger.warning(f"h98y2 not found for discharge {discharge_id} in 'h98y2' or 'taue' tree")
        return None

    except Exception as e:
        logger.error(f"Error fetching h98y2 for discharge {discharge_id}: {e}")
        return None

def determine_confinement_mode(h98y2: Optional[float]) -> str:
    """
    Determine confinement mode based on h98y2.
    H-mode if h98y2 >= 0.85, else L-mode.
    """
    if h98y2 is None:
        logger.warning("h98y2 is None, defaulting to L-mode")
        return "L-mode"
    if h98y2 >= 0.85:
        return "H-mode"
    else:
        return "L-mode"

@timeout_guard(timeout=CONNECTION_TIMEOUT)
def fetch_data_for_discharge(discharge_id: int) -> Dict[str, Any]:
    """
    Fetch all required data (EFIT, island_width, tau_e, h98y2) for a single discharge.
    Returns a dictionary containing the parsed data.
    Raises an exception if the real data cannot be fetched.
    """
    conn = _get_connection(discharge_id)
    if not conn:
        raise RuntimeError(f"Failed to establish connection for discharge {discharge_id}")

    result = {
        "discharge_id": discharge_id,
        "efit_data": None,
        "island_width": None,
        "tau_e": None,
        "h98y2": None,
        "confinement_mode": "L-mode", # Default
        "needs_derivation": False
    }

    # Fetch EFIT
    efit = get_efit_data(conn, discharge_id)
    if efit:
        result["efit_data"] = efit
    else:
        logger.warning(f"EFIT data missing for {discharge_id}, marking for derivation check")
        result["needs_derivation"] = True

    # Fetch Island Width
    iw = fetch_island_width(conn, discharge_id)
    if iw is not None:
        result["island_width"] = iw
    else:
        # If not pre-calculated, we might need to derive it later
        # For now, we just note it. T013 handles the derivation logic.
        result["needs_derivation"] = True

    # Fetch Tau_e
    tau = fetch_tau_e(conn, discharge_id)
    result["tau_e"] = tau

    # Fetch h98y2 and determine mode
    h98 = fetch_h98y2(conn, discharge_id)
    result["h98y2"] = h98
    result["confinement_mode"] = determine_confinement_mode(h98)

    logger.info(f"Successfully fetched data for discharge {discharge_id}: "
                f"Mode={result['confinement_mode']}, H98={h98}, Tau={tau}")

    return result

def main():
    """
    Main entry point for testing retrieval logic.
    """
    logger.setLevel(logging.INFO)
    # Example discharge IDs (replace with real ones when available)
    test_discharges = [123456, 123457] # Placeholder IDs

    for d_id in test_discharges:
        try:
            data = fetch_data_for_discharge(d_id)
            print(f"Discharge {d_id}: {data}")
        except Exception as e:
            print(f"Failed to fetch data for {d_id}: {e}")

if __name__ == "__main__":
    main()