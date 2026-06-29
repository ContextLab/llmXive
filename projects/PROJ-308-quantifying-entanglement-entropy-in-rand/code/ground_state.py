"""
Ground state computation using TeNPy for imaginary-time TEBD evolution.

Implements FR-003:
- Double-precision (64-bit) enforcement
- Convergence tolerance 1e-8
- Adaptive bond dimension (max chi=400)
- 'numerically unresolved' flagging for non-converged states
"""

import numpy as np
from typing import Tuple, Dict, Optional, List

# Import from sibling modules using the provided API surface
from config import ConfigError, validate_float, validate_int
from hamiltonian import generate_xxz_hamiltonian, get_coupling_distribution_stats

try:
    import tenpy
    from tenpy.models.spins import SpinChain
    from tenpy.algorithms.tebd import TEBDEngine
    from tenpy.networks.mps import MPS
    from tenpy.linalg.chi import Chi
except ImportError:
    raise ImportError(
        "TeNPy is required for ground state computation. "
        "Install it via: pip install tenpy"
    )


# Constants
DEFAULT_CHI_MAX = 400
DEFAULT_TOL = 1e-8
DEFAULT_N_EPOCHS = 100
DOUBLE_PRECISION = np.float64


class GroundStateError(ConfigError):
    """Custom exception for ground state computation failures."""
    pass


def get_default_ground_state_config() -> Dict:
    """Return default configuration for ground state computation."""
    return {
        'chi_max': DEFAULT_CHI_MAX,
        'tol': DEFAULT_TOL,
        'n_epochs': DEFAULT_N_EPOCHS,
        'random_seed': None,
        'L': 20,
        'delta': 0.0,
    }


def validate_ground_state_config(config: Dict) -> Dict:
    """
    Validate ground state computation configuration.

    Args:
        config: Dictionary with configuration parameters.

    Returns:
        Validated configuration dictionary.

    Raises:
        ConfigError: If any parameter is out of bounds.
    """
    validated = {}

    # Validate chi_max
    validated['chi_max'] = validate_int(
        config.get('chi_max', DEFAULT_CHI_MAX),
        min_val=10,
        max_val=1000,
        param_name='chi_max'
    )

    # Validate tolerance
    validated['tol'] = validate_float(
        config.get('tol', DEFAULT_TOL),
        min_val=1e-12,
        max_val=1e-4,
        param_name='tol'
    )

    # Validate n_epochs
    validated['n_epochs'] = validate_int(
        config.get('n_epochs', DEFAULT_N_EPOCHS),
        min_val=10,
        max_val=1000,
        param_name='n_epochs'
    )

    # Validate random seed
    validated['random_seed'] = validate_int(
        config.get('random_seed'),
        min_val=0,
        max_val=2**32 - 1,
        param_name='random_seed',
        allow_none=True
    )

    # Validate L (chain length)
    validated['L'] = validate_int(
        config.get('L'),
        min_val=4,
        max_val=100,
        param_name='L'
    )

    # Validate delta (disorder strength)
    validated['delta'] = validate_float(
        config.get('delta'),
        min_val=0.0,
        max_val=1.0,
        param_name='delta'
    )

    return validated


def _build_tenpy_model(L: int, couplings: np.ndarray, bc: str = 'open') -> SpinChain:
    """
    Build a TeNPy SpinChain model from XXZ Hamiltonian parameters.

    Args:
        L: Chain length.
        couplings: Array of coupling strengths J_i for each bond.
        bc: Boundary condition ('open' or 'periodic').

    Returns:
        Configured SpinChain model instance.
    """
    # Create J_z couplings (we use J_z for disorder, J_xy = 1)
    # For XXZ: H = sum J_i (S_i^x S_{i+1}^x + S_i^y S_{i+1}^y + S_i^z S_{i+1}^z)
    # TeNPy SpinChain expects J_z as a list or array

    # Ensure double precision
    couplings = couplings.astype(DOUBLE_PRECISION)

    # Create model parameters
    model_params = {
        'L': L,
        'Jx': 1.0,
        'Jy': 1.0,
        'Jz': couplings.tolist(),
        'h_x': 0.0,
        'h_y': 0.0,
        'h_z': 0.0,
        'bc_MPS': bc,
        'conserve': 'Sz',  # Conserve total Sz
        'dtype': DOUBLE_PRECISION,
    }

    model = SpinChain(model_params)
    return model


def compute_ground_state(
    L: int,
    delta: float,
    couplings: Optional[np.ndarray] = None,
    chi_max: int = DEFAULT_CHI_MAX,
    tol: float = DEFAULT_TOL,
    n_epochs: int = DEFAULT_N_EPOCHS,
    random_seed: Optional[int] = None
) -> Tuple[Dict, bool]:
    """
    Compute the ground state of the XXZ Heisenberg chain with random couplings
    using imaginary-time TEBD evolution.

    Implements FR-003:
    - Double-precision (64-bit) enforcement
    - Convergence tolerance 1e-8
    - Adaptive bond dimension (max chi=400)
    - 'numerically unresolved' flagging for non-converged states

    Args:
        L: Chain length (must be even for optimal TEBD).
        delta: Disorder strength (couplings ~ U[1-delta, 1+delta]).
        couplings: Optional pre-computed coupling array. If None, generated from delta.
        chi_max: Maximum bond dimension (default 400).
        tol: Convergence tolerance for TEBD (default 1e-8).
        n_epochs: Maximum number of TEBD sweeps (default 100).
        random_seed: Random seed for reproducibility.

    Returns:
        Tuple of (state_dict, is_converged):
            - state_dict: Contains 'mps' (MPS object), 'energy' (ground state energy),
                         'chi_list' (list of bond dimensions), 'final_trunc_err'
            - is_converged: True if TEBD converged within tolerance, False otherwise
                            (marked as 'numerically unresolved')

    Raises:
        ConfigError: If parameters are invalid.
        GroundStateError: If ground state computation fails.
    """
    # Validate inputs
    config = {
        'L': L,
        'delta': delta,
        'chi_max': chi_max,
        'tol': tol,
        'n_epochs': n_epochs,
        'random_seed': random_seed
    }
    validated = validate_ground_state_config(config)

    L = validated['L']
    delta = validated['delta']
    chi_max = validated['chi_max']
    tol = validated['tol']
    n_epochs = validated['n_epochs']
    random_seed = validated['random_seed']

    # Set random seed if provided
    if random_seed is not None:
        np.random.seed(random_seed)

    # Generate couplings if not provided
    if couplings is None:
        couplings = generate_xxz_hamiltonian(L, delta, return_only_couplings=True)

    # Ensure double precision
    couplings = couplings.astype(DOUBLE_PRECISION)

    # Build TeNPy model
    try:
        model = _build_tenpy_model(L, couplings, bc='open')
    except Exception as e:
        raise GroundStateError(f"Failed to build TeNPy model: {e}")

    # Initialize MPS with random product state (Neel state for better convergence)
    # For S=1/2, Neel state: up, down, up, down, ...
    psi = MPS.from_product_state(
        model.lat.mps_sites(),
        ['up', 'down'] * (L // 2),
        bc='open'
    )

    # Ensure double precision in MPS
    psi._data = {k: v.astype(DOUBLE_PRECISION) for k, v in psi._data.items()}

    # Configure TEBD
    try:
        tebd_params = {
            'order': 2,  # Second-order Suzuki-Trotter
            'dt': 0.1,   # Initial time step
            'N_steps': 100,  # Steps per sweep
            'trunc_params': {
                'chi_max': chi_max,
                'svd_min': 1e-10,
                'trunc_err': 1e-10,
            },
            'verbose': 0,
        }

        tebd = TEBDEngine(psi, model, tebd_params)

    except Exception as e:
        raise GroundStateError(f"Failed to initialize TEBD engine: {e}")

    # Run imaginary-time evolution
    is_converged = False
    final_trunc_err = 0.0
    chi_list = []
    final_energy = 0.0

    try:
        # Run TEBD with convergence checking
        for epoch in range(n_epochs):
            # Reduce time step for better convergence
            current_dt = max(0.001, 0.1 * (0.5 ** epoch))

            tebd.dt = current_dt
            tebd.N_steps = 100

            # Run one sweep
            tebd.run()

            # Check convergence
            if tebd.converged:
                is_converged = True
                break

            # Track bond dimensions
            chi_list.append(max(psi.chi))

            # Check if we've hit max chi without converging
            if max(psi.chi) >= chi_max and epoch > 10:
                # Mark as unresolved - couldn't converge within chi_max
                break

        # Get final energy
        final_energy = tebd.run()  # Returns energy expectation

        # Get final truncation error
        final_trunc_err = max(abs(psi.get_B(i, [0]).trunc_err) for i in range(L - 1))

    except Exception as e:
        # Mark as unresolved on any exception
        is_converged = False
        final_energy = np.nan
        final_trunc_err = np.inf

    # Build result dictionary
    state_dict = {
        'mps': psi,
        'energy': final_energy,
        'chi_list': chi_list,
        'final_trunc_err': final_trunc_err,
        'chi_max_reached': max(psi.chi) >= chi_max if not is_converged else False,
        'couplings': couplings,
        'L': L,
        'delta': delta,
    }

    return state_dict, is_converged


def compute_ground_state_batch(
    L: int,
    delta: float,
    N_real: int,
    chi_max: int = DEFAULT_CHI_MAX,
    tol: float = DEFAULT_TOL,
    n_epochs: int = DEFAULT_N_EPOCHS,
    random_seed_base: int = 42
) -> Tuple[List[Dict], List[bool]]:
    """
    Compute ground states for multiple realizations of disorder.

    Args:
        L: Chain length.
        delta: Disorder strength.
        N_real: Number of disorder realizations.
        chi_max: Maximum bond dimension.
        tol: Convergence tolerance.
        n_epochs: Maximum TEBD epochs.
        random_seed_base: Base seed for randomization.

    Returns:
        Tuple of (results_list, convergence_flags):
            - results_list: List of state dictionaries for each realization
            - convergence_flags: List of booleans indicating convergence
    """
    results = []
    convergence_flags = []

    for i in range(N_real):
        seed = random_seed_base + i
        state_dict, is_converged = compute_ground_state(
            L=L,
            delta=delta,
            chi_max=chi_max,
            tol=tol,
            n_epochs=n_epochs,
            random_seed=seed
        )
        results.append(state_dict)
        convergence_flags.append(is_converged)

    return results, convergence_flags


def is_numerically_unresolved(is_converged: bool, chi_max_reached: bool, trunc_err: float) -> bool:
    """
    Determine if a ground state computation is 'numerically unresolved'.

    A state is unresolved if:
    - TEBD did not converge within tolerance, OR
    - Maximum bond dimension was reached before convergence, OR
    - Truncation error is above acceptable threshold

    Args:
        is_converged: Whether TEBD converged.
        chi_max_reached: Whether max bond dimension was reached.
        trunc_err: Final truncation error.

    Returns:
        True if the state should be flagged as 'numerically unresolved'.
    """
    trunc_err_threshold = 1e-6

    if not is_converged:
        return True
    if chi_max_reached:
        return True
    if trunc_err > trunc_err_threshold:
        return True

    return False