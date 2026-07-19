"""
code/ground_state.py

Implements ground state computation for the XXZ Heisenberg spin chain with
random nearest-neighbour couplings using imaginary-time TEBD evolution via TeNPy.

Features:
- Double-precision (float64) enforcement.
- Adaptive bond dimension (max chi=400).
- Convergence tolerance 1e-8.
- 'Numerically unresolved' flagging for non-converged states.
"""

import numpy as np
from typing import Tuple, Dict, Optional, List, Any
from config import ConfigError, validate_float, validate_int
from hamiltonian import generate_xxz_hamiltonian, get_coupling_distribution_stats

# Import TeNPy components
try:
    from tenpy.networks.mps import MPS
    from tenpy.models.spins import SpinChain
    from tenpy.algorithms.tebd import TEBDEngine
    from tenpy.linalg.np_conserved import array
    import tenpy
except ImportError:
    raise ImportError(
        "TeNPy library is required for ground state computation. "
        "Please install it via: pip install tenpy"
    )

class GroundStateError(Exception):
    """Custom exception for ground state computation failures."""
    pass


def get_default_ground_state_config() -> Dict[str, Any]:
    """
    Returns the default configuration for ground state computation.

    Returns:
        Dict: Default configuration parameters.
    """
    return {
        'convergence_tol': 1e-8,
        'max_bond_dim': 400,
        'dt_list': [0.1, 0.05, 0.01, 0.005, 0.001],
        'trunc_cut': 1e-10,
        'verbose': False
    }


def validate_ground_state_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the ground state configuration parameters.

    Args:
        config: Configuration dictionary.

    Returns:
        Dict: Validated configuration.

    Raises:
        ConfigError: If any parameter is out of bounds or invalid.
    """
    validated = get_default_ground_state_config()
    validated.update(config)

    # Validate convergence tolerance
    validated['convergence_tol'] = validate_float(
        validated['convergence_tol'],
        min_val=1e-12,
        max_val=1e-4,
        param_name='convergence_tol'
    )

    # Validate max bond dimension
    validated['max_bond_dim'] = validate_int(
        validated['max_bond_dim'],
        min_val=10,
        max_val=1000,
        param_name='max_bond_dim'
    )

    # Validate truncation cut
    validated['trunc_cut'] = validate_float(
        validated['trunc_cut'],
        min_val=1e-15,
        max_val=1e-6,
        param_name='trunc_cut'
    )

    return validated


def _build_tenpy_model(L: int, couplings: np.ndarray, delta: float) -> SpinChain:
    """
    Builds a TeNPy SpinChain model with custom couplings.

    Args:
        L: Chain length.
        couplings: Array of coupling strengths J_i for nearest neighbors.
        delta: Disorder strength parameter (used for model identification).

    Returns:
        SpinChain: Configured TeNPy model.
    """
    # Ensure double precision for couplings
    couplings = np.asarray(couplings, dtype=np.float64)

    # Prepare parameters for TeNPy model
    # The XXZ model in TeNPy uses J_x, J_y, J_z and h_z parameters.
    # For isotropic XXZ (Heisenberg), J_x = J_y = J_z = J.
    # We need to inject random couplings J_i between sites.
    # TeNPy's SpinChain allows site-dependent couplings via 'J' parameter.

    params = {
        'L': L,
        'S': 0.5,
        'conserve': 'Sz',
        'bc_MPS': 'finite',
        'J': couplings,  # Site-dependent couplings
        'Jz': couplings,  # ZZ coupling (isotropic)
        'hz': 0.0,       # No external field
        'bc': 'open',
        'dtype': np.float64  # Explicit double precision
    }

    try:
        model = SpinChain(params)
    except Exception as e:
        raise GroundStateError(f"Failed to build TeNPy model: {e}")

    return model


def _compute_ground_state_tebd(
    model: SpinChain,
    config: Dict[str, Any]
) -> Tuple[MPS, Dict[str, Any]]:
    """
    Computes the ground state using imaginary-time TEBD evolution.

    Args:
        model: TeNPy SpinChain model.
        config: Ground state configuration.

    Returns:
        Tuple[MPS, Dict]: Ground state MPS and metadata (convergence status, bond dims, etc.)
    """
    # Initialize MPS as product state (all spins up)
    L = model.L
    psi = MPS.from_product_state(
        model.lat.mps_sites(),
        ['up'] * L,
        bc=model.bc
    )

    # Configure TEBD
    tebd_params = {
        'dt': config['dt_list'][0],
        'order': 2,
        'trunc_cut': config['trunc_cut'],
        'max_bond_dim': config['max_bond_dim'],
        'chi_list': None,  # Adaptive
        'verbose': config['verbose'],
        'combine': True
    }

    try:
        engine = TEBDEngine(psi, model, tebd_params)
    except Exception as e:
        raise GroundStateError(f"Failed to initialize TEBD engine: {e}")

    # Run imaginary time evolution with adaptive dt and bond dimension
    converged = False
    best_psi = psi
    metadata = {
        'converged': False,
        'final_dt': None,
        'max_chi_reached': 0,
        'energy': None,
        'num_steps': 0,
        'reason': None
    }

    total_steps = 0
    max_total_steps = 10000  # Safety limit

    for dt in config['dt_list']:
        engine.params['dt'] = dt
        engine.options['max_bond_dim'] = config['max_bond_dim']

        # Evolve until convergence or max steps for this dt
        steps_this_dt = 0
        while steps_this_dt < 1000:  # Limit per dt
            try:
                engine.run_one_step()
            except Exception as e:
                metadata['reason'] = f"TEBD step failed: {e}"
                break

            total_steps += 1
            steps_this_dt += 1
            metadata['num_steps'] = total_steps

            # Check bond dimension
            current_max_chi = max([max(b) for b in psi.chi])
            if current_max_chi > metadata['max_chi_reached']:
                metadata['max_chi_reached'] = current_max_chi

            # Check convergence by energy change
            E = psi.expectation_value(model.H_mpo)
            if metadata['energy'] is not None:
                dE = abs(E[0] - metadata['energy'])
                if dE < config['convergence_tol']:
                    converged = True
                    metadata['converged'] = True
                    metadata['final_dt'] = dt
                    metadata['energy'] = E[0]
                    best_psi = psi.copy()
                    break
            metadata['energy'] = E[0]

            # Safety break if max bond dimension hit and not converging
            if current_max_chi >= config['max_bond_dim'] and dE > config['convergence_tol']:
                # Continue with smaller dt
                break

        if converged:
            break

        # If we hit max bond dimension, try smaller dt
        if metadata['max_chi_reached'] >= config['max_bond_dim']:
            continue

    if not converged:
        if metadata['max_chi_reached'] >= config['max_bond_dim']:
            metadata['reason'] = "Max bond dimension reached without convergence"
        elif total_steps >= max_total_steps:
            metadata['reason'] = "Maximum evolution steps exceeded"
        else:
            metadata['reason'] = "Convergence tolerance not met within limits"

    return best_psi, metadata


def compute_ground_state(
    L: int,
    delta: float,
    couplings: Optional[np.ndarray] = None,
    seed: Optional[int] = None,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[MPS, Dict[str, Any]]:
    """
    Computes the ground state of the XXZ Heisenberg spin chain with random couplings.

    Args:
        L: Chain length (20-40).
        delta: Disorder strength (0-1).
        couptions: Optional pre-generated coupling array. If None, generated from delta.
        seed: Random seed for coupling generation.
        config: Ground state configuration (optional, uses defaults if None).

    Returns:
        Tuple[MPS, Dict]: Ground state MPS and metadata including convergence status.

    Raises:
        GroundStateError: If computation fails or parameters are invalid.
    """
    # Validate inputs
    L = validate_int(L, min_val=20, max_val=40, param_name='L')
    delta = validate_float(delta, min_val=0.0, max_val=1.0, param_name='delta')

    if config is None:
        config = get_default_ground_state_config()
    config = validate_ground_state_config(config)

    # Generate couplings if not provided
    if couplings is None:
        if seed is not None:
            np.random.seed(seed)
        couplings = get_coupling_distribution_stats(L, delta, seed=None)[0]
        # Actually, we need the array, not just stats. Let's regenerate properly.
        from hamiltonian import generate_xxz_hamiltonian
        H, J_array = generate_xxz_hamiltonian(L, delta, seed)
        couplings = J_array

    # Ensure double precision
    couplings = np.asarray(couplings, dtype=np.float64)

    # Build model
    model = _build_tenpy_model(L, couplings, delta)

    # Compute ground state via TEBD
    psi, metadata = _compute_ground_state_tebd(model, config)

    return psi, metadata


def compute_ground_state_batch(
    L: int,
    delta: float,
    N_realizations: int,
    seed_base: int,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[List[MPS], List[Dict[str, Any]]]:
    """
    Computes ground states for multiple realizations of random couplings.

    Args:
        L: Chain length.
        delta: Disorder strength.
        N_realizations: Number of disorder realizations.
        seed_base: Base seed for random number generation.
        config: Ground state configuration.

    Returns:
        Tuple[List[MPS], List[Dict]]: List of MPS and metadata for each realization.
    """
    L = validate_int(L, min_val=20, max_val=40, param_name='L')
    delta = validate_float(delta, min_val=0.0, max_val=1.0, param_name='delta')
    N_realizations = validate_int(N_realizations, min_val=1, max_val=200, param_name='N_realizations')
    seed_base = validate_int(seed_base, min_val=0, max_val=2**31-1, param_name='seed_base')

    if config is None:
        config = get_default_ground_state_config()

    ground_states = []
    metadata_list = []

    for i in range(N_realizations):
        seed = seed_base + i
        psi, meta = compute_ground_state(L, delta, seed=seed, config=config)
        ground_states.append(psi)
        metadata_list.append(meta)

    return ground_states, metadata_list


def is_numerically_unresolved(metadata: Dict[str, Any]) -> bool:
    """
    Checks if a ground state computation is numerically unresolved.

    Args:
        metadata: Metadata dictionary from compute_ground_state.

    Returns:
        bool: True if the state is unresolved (non-converged), False otherwise.
    """
    return not metadata.get('converged', False)


def get_ground_state_statistics(
    metadata_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes statistics over a batch of ground state computations.

    Args:
        metadata_list: List of metadata dictionaries.

    Returns:
        Dict: Statistics including convergence rate, max bond dimensions, etc.
    """
    if not metadata_list:
        return {
            'total_realizations': 0,
            'converged_count': 0,
            'unresolved_count': 0,
            'convergence_rate': 0.0,
            'avg_max_chi': 0.0,
            'max_chi_overall': 0
        }

    total = len(metadata_list)
    converged = sum(1 for m in metadata_list if m.get('converged', False))
    unresolved = total - converged
    max_chis = [m.get('max_chi_reached', 0) for m in metadata_list]

    return {
        'total_realizations': total,
        'converged_count': converged,
        'unresolved_count': unresolved,
        'convergence_rate': converged / total if total > 0 else 0.0,
        'avg_max_chi': float(np.mean(max_chis)),
        'max_chi_overall': int(np.max(max_chis))
    }
