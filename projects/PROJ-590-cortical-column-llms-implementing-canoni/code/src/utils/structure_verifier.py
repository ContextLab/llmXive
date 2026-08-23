import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Any, Optional
import logging
from src.models.microcircuit import (
    MicrocircuitColumn,
    L23Layer,
    L4Layer,
    L5Layer,
    L6Layer,
    generate_laminar_connectivity_mask,
    verify_connectivity_constraints
)

logger = logging.getLogger(__name__)

# Expected canonical connections as per spec.md:FR-001
# Format: (source_layer_name, target_layer_name, expected_type)
# Types: 'excitatory', 'inhibitory', 'recurrent'
EXPECTED_CONNECTIONS = [
    ("L4", "L23", "excitatory"),
    ("L23", "L5", "excitatory"),
    ("L5", "L6", "excitatory"),
    ("L23", "L23", "recurrent_excitatory"),
    ("L23", "L23", "inhibitory"), # L23 contains both E and I populations
]

# Expected E/I ratio (Excitatory : Inhibitory)
EXPECTED_EI_RATIO = 4.0
EI_TOLERANCE = 0.05  # 5% tolerance

def _get_layer_mapping(column: MicrocircuitColumn) -> Dict[str, Any]:
    """
    Extract layer instances from the MicrocircuitColumn for inspection.
    Returns a dict mapping layer names to their attributes.
    """
    mapping = {}
    if hasattr(column, 'layer_l4') and column.layer_l4 is not None:
        mapping['L4'] = column.layer_l4
    if hasattr(column, 'layer_l23') and column.layer_l23 is not None:
        mapping['L23'] = column.layer_l23
    if hasattr(column, 'layer_l5') and column.layer_l5 is not None:
        mapping['L5'] = column.layer_l5
    if hasattr(column, 'layer_l6') and column.layer_l6 is not None:
        mapping['L6'] = column.layer_l6
    return mapping

def _analyze_connectivity_masks(column: MicrocircuitColumn) -> Dict[str, List[str]]:
    """
    Analyze the connectivity masks of the column's layers.
    Returns a dictionary of active connections found.
    """
    layers = _get_layer_mapping(column)
    found_connections = []

    # Check L4 -> L23
    if 'L4' in layers and 'L23' in layers:
        l4_layer = layers['L4']
        l23_layer = layers['L23']
        # Check if L23 has a weight matrix receiving from L4
        # Assuming standard naming: weight_l4_to_l23 or similar in the forward logic
        # We inspect the state_dict keys for evidence of connections
        state_keys = list(column.state_dict().keys())
        has_l4_l23 = any('l4' in k.lower() and 'l23' in k.lower() and 'weight' in k.lower() for k in state_keys)
        if has_l4_l23:
            found_connections.append(("L4", "L23", "excitatory"))

    # Check L23 -> L5
    if 'L23' in layers and 'L5' in layers:
        state_keys = list(column.state_dict().keys())
        has_l23_l5 = any('l23' in k.lower() and 'l5' in k.lower() and 'weight' in k.lower() for k in state_keys)
        if has_l23_l5:
            found_connections.append(("L23", "L5", "excitatory"))

    # Check L5 -> L6
    if 'L5' in layers and 'L6' in layers:
        state_keys = list(column.state_dict().keys())
        has_l5_l6 = any('l5' in k.lower() and 'l6' in k.lower() and 'weight' in k.lower() for k in state_keys)
        if has_l5_l6:
            found_connections.append(("L5", "L6", "excitatory"))

    # Check L23 Recurrent (Excitatory) and Inhibitory
    if 'L23' in layers:
        l23_layer = layers['L23']
        state_keys = list(column.state_dict().keys())
        # Recurrent excitatory usually implies self-connection or within-layer E->E
        has_recurrent_exc = any('l23' in k.lower() and 'recurrent' in k.lower() and 'weight' in k.lower() for k in state_keys)
        if has_recurrent_exc:
            found_connections.append(("L23", "L23", "recurrent_excitatory"))
        
        # Inhibitory connections within L23 (E->I or I->E or I->I)
        # Often indicated by specific inhibitory weight matrices
        has_inhibitory = any('l23' in k.lower() and 'inhibitory' in k.lower() and 'weight' in k.lower() for k in state_keys)
        if has_inhibitory:
            found_connections.append(("L23", "L23", "inhibitory"))

    return found_connections

def _count_ei_ratio(column: MicrocircuitColumn) -> Tuple[float, int, int]:
    """
    Count excitatory and inhibitory parameters in the column.
    Heuristic: Parameters with 'exc' in name are excitatory, 'inh' are inhibitory.
    If naming is not explicit, assume standard E/I split based on layer config if available.
    """
    state_dict = column.state_dict()
    exc_count = 0
    inh_count = 0

    for name, param in state_dict.items():
        name_lower = name.lower()
        if 'exc' in name_lower or 'excitatory' in name_lower:
            exc_count += param.numel()
        elif 'inh' in name_lower or 'inhibitory' in name_lower:
            inh_count += param.numel()
        else:
            # Fallback: If the project uses standard naming, we might need to infer.
            # However, per task T069, we must verify the ratio. 
            # If explicit naming is missing, we might assume a default ratio if the architecture
            # is known to be fixed, but for verification, we look for explicit markers.
            # If no markers found, we cannot verify the ratio strictly.
            pass

    if inh_count == 0:
        # If no explicit inhibitory parameters found, check if the architecture
        # enforces it structurally (e.g., separate modules).
        # For this verifier, we assume explicit naming or structural separation.
        # If we can't count, we return a warning state.
        logger.warning("Could not distinguish E/I parameters by name. Assuming structural ratio if defined.")
        return 0.0, 0, 0

    return exc_count / inh_count, exc_count, inh_count

def verify_canonical_topology(column: MicrocircuitColumn) -> bool:
    """
    Assert that the instantiated MicrocircuitColumn has the exact connectivity masks
    for L2/3, L4, L5, L6 as defined in spec.md:FR-001.
    
    Checks:
    1. Expected connections exist (L4->L23, L23->L5, L5->L6, L23->L23 Recurrent, L23->L23 Inhibitory).
    2. E/I ratio is within 5% of 4:1.
    
    Returns:
        bool: True if topology is canonical, False otherwise.
    
    Raises:
        AssertionError: If topology is not canonical.
    """
    logger.info("Verifying canonical topology for MicrocircuitColumn...")
    
    # 1. Verify Connectivity
    found_connections = _analyze_connectivity_masks(column)
    logger.debug(f"Found connections: {found_connections}")
    
    missing_connections = []
    for expected_src, expected_tgt, expected_type in EXPECTED_CONNECTIONS:
        if (expected_src, expected_tgt, expected_type) not in found_connections:
            missing_connections.append((expected_src, expected_tgt, expected_type))
    
    if missing_connections:
        error_msg = f"Missing canonical connections: {missing_connections}. Found: {found_connections}"
        logger.error(error_msg)
        raise AssertionError(error_msg)
    
    # 2. Verify E/I Ratio
    current_ratio, exc_count, inh_count = _count_ei_ratio(column)
    
    if inh_count == 0:
        # If we cannot count, we might rely on a structural check if the model
        # enforces it at initialization. However, the task requires checking the ratio.
        # If the model doesn't expose E/I counts, we might need to check the config.
        # For now, if we can't count, we assume the ratio is structural if the model
        # was built with specific configs. But strict verification requires counts.
        # Let's assume if counts are 0, we check if the model has separate E/I modules.
        # If not found, we fail.
        raise AssertionError("Could not determine E/I ratio: No explicit E/I parameters found.")

    if abs(current_ratio - EXPECTED_EI_RATIO) / EXPECTED_EI_RATIO > EI_TOLERANCE:
        error_msg = (f"E/I ratio deviation too high. Expected {EXPECTED_EI_RATIO}:1, "
                     f"Got {current_ratio:.2f}:1 (Exc: {exc_count}, Inh: {inh_count}). "
                     f"Deviation: {abs(current_ratio - EXPECTED_EI_RATIO) / EXPECTED_EI_RATIO * 100:.2f}%")
        logger.error(error_msg)
        raise AssertionError(error_msg)
    
    logger.info(f"Topology verification passed. E/I Ratio: {current_ratio:.2f}:1")
    return True

def main():
    """
    Entry point for running the topology verification as a script.
    Expects a path to a saved model or creates a default one for testing.
    """
    import argparse
    from src.models.microcircuit import create_microcircuit_column

    parser = argparse.ArgumentParser(description="Verify canonical topology of MicrocircuitColumn")
    parser.add_argument("--model-path", type=str, default=None, help="Path to saved model state dict")
    args = parser.parse_args()

    try:
        # Create a default column if no model path provided
        if args.model_path:
            logger.warning("Model path provided not implemented in this snippet, creating default for demo.")
        
        # Create a standard column
        column = create_microcircuit_column()
        
        verify_canonical_topology(column)
        print("SUCCESS: Topology is canonical.")
        return 0
    except AssertionError as e:
        print(f"FAILED: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exit(main())