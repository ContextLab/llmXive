"""
Numerical Yukawa Potential Solver for Validation (Plan 0.2).

This module implements a numerical solver for the Schrödinger equation
with a Yukawa potential V(r) = - (alpha * exp(-m_phi * r)) / r.
It uses the Numerov algorithm for high-precision integration to extract
the Sommerfeld enhancement factor and binding energies.
"""
import numpy as np
from scipy.optimize import brentq
from typing import Tuple, Optional, Callable

def yukawa_potential(r: np.ndarray, alpha: float, m_phi: float) -> np.ndarray:
    """
    Calculate the Yukawa potential V(r) = - (alpha * exp(-m_phi * r)) / r.
    
    Handles r=0 singularity by returning the limit value: -alpha * m_phi.
    
    Args:
        r: Array of radial distances.
        alpha: Coupling strength (alpha = g^2 / 4pi).
        m_phi: Mediator mass.
        
    Returns:
        Array of potential values.
    """
    # Avoid division by zero at r=0
    # Limit as r->0 of -alpha * exp(-m_phi * r) / r is -infinity, 
    # but for numerical stability in Schrödinger eq, we handle the first point.
    # However, the Numerov method usually starts from r=eps.
    # We'll use a small epsilon for the calculation if 0 is present.
    eps = 1e-12
    r_safe = np.where(r == 0, eps, r)
    
    return - (alpha * np.exp(-m_phi * r_safe)) / r_safe

def numerov_schrodinger(
    r: np.ndarray, 
    E: float, 
    potential_func: Callable[[np.ndarray], np.ndarray],
    l: int = 0
) -> np.ndarray:
    """
    Solve the radial Schrödinger equation using the Numerov method.
    
    Equation: u''(r) + k(r)^2 u(r) = 0
    where k(r)^2 = 2 * mu * (E - V(r)) - l(l+1)/r^2
    
    We assume reduced mass mu = 1 for the solver (scaling applied later) 
    or passed via the potential/E scaling. Here we assume standard form:
    u''(r) = 2 * (V(r) - E) * u(r) (assuming mu=1/2 for convenience in units)
    Actually, standard radial eq: -1/(2mu) u'' + (V + l(l+1)/(2mu r^2)) u = E u
    => u'' = 2mu (V - E + l(l+1)/(2mu r^2)) u
    
    For Sommerfeld, we usually look at scattering states (E > 0) or bound states (E < 0).
    Here we implement the integration for a given E.
    
    Args:
        r: Radial grid.
        E: Energy eigenvalue.
        potential_func: Function V(r).
        l: Angular momentum quantum number (default 0 for s-wave).
        
    Returns:
        Array of wavefunction values u(r).
    """
    N = len(r)
    u = np.zeros(N)
    
    # Constants
    # Assuming units where 2*mu = 1 for simplicity in the numerical step, 
    # or we incorporate mu into the potential/E scaling.
    # Let's assume the equation is u'' = k^2 * u where k^2 = 2*mu*(E - V) - l(l+1)/r^2
    # For Sommerfeld enhancement, we are interested in the asymptotic behavior.
    # We'll assume mu is absorbed or set to 1.
    mu = 1.0 
    
    # Precompute k^2 array
    # k2(r) = 2*mu * (E - V(r)) - l*(l+1)/r^2
    # Handle r=0 carefully
    r_safe = np.where(r == 0, 1e-12, r)
    centrifugal = l * (l + 1) / (r_safe ** 2)
    V = potential_func(r)
    k2 = 2 * mu * (E - V) - centrifugal
    
    # Numerov coefficients
    # u_{n+1} = ( (2 + 10/12 * h^2 * k2_n) * u_n - (1 - 1/12 * h^2 * k2_{n-1}) * u_{n-1} ) 
    #           / (1 - 1/12 * h^2 * k2_{n+1})
    h = r[1] - r[0]
    h2 = h * h
    
    # Initialize boundary conditions
    # For scattering (E>0): u(0)=0, u'(0) ~ 1 (small r behavior)
    # u(r) ~ r^{l+1}
    if l == 0:
        u[0] = 0.0
        u[1] = r[1] # Approximate slope
    else:
        u[0] = 0.0
        u[1] = (r[1] ** (l + 1))
    
    # Numerov integration forward
    for i in range(1, N - 1):
        g_n = k2[i]
        g_n1 = k2[i+1]
        g_n_1 = k2[i-1]
        
        term_n = 2 + (h2 / 6.0) * g_n
        term_n1 = 1 - (h2 / 12.0) * g_n1
        term_n_1 = 1 - (h2 / 12.0) * g_n_1
        
        u[i+1] = (term_n * u[i] - term_n_1 * u[i-1]) / term_n1
        
    return u

def extract_sommerfeld_factor(
    u: np.ndarray, 
    r: np.ndarray, 
    k: float,
    mass: float = 1.0
) -> float:
    """
    Extract the Sommerfeld enhancement factor S from the wavefunction.
    
    S = |psi(0)|^2 / |psi_free(0)|^2
    For s-wave, S = |u'(0)|^2 / k^2 (normalized appropriately)
    Or more commonly: S = (u(r_max) * k / sin(k*r_max + delta))^2 ...
    
    A robust method: Compare the amplitude of the oscillating tail to the free case.
    Free solution: u_free(r) ~ sin(kr)
    Interacting: u(r) ~ A sin(kr + delta)
    S = A^2
    
    We fit the tail of u(r) to A * sin(kr + delta).
    
    Args:
        u: Wavefunction array.
        r: Radial grid.
        k: Momentum (sqrt(2*mu*E)).
        mass: Reduced mass.
        
    Returns:
        Sommerfeld enhancement factor S.
    """
    # Select the tail region for fitting
    tail_start = int(len(r) * 0.7)
    r_tail = r[tail_start:]
    u_tail = u[tail_start:]
    
    if k <= 0:
        # Bound state or zero energy, different handling needed
        # For E=0, S = |u'(0)|^2 / (const)
        # Approximate derivative at origin
        if len(u) > 1:
            return (u[1] / r[1]) ** 2 # Very rough
        return 1.0
    
    # Fit u(r) = A * sin(k*r + delta)
    # We can use a simple least squares or just amplitude extraction
    # Amplitude A = max(u) if phase is right, but fitting is better.
    # Let's use a simple approach:
    # u(r) = C1 * sin(kr) + C2 * cos(kr)
    # Matrix form: [sin(kr) cos(kr)] [C1; C2] = u
    
    M = np.column_stack([np.sin(k * r_tail), np.cos(k * r_tail)])
    # Solve least squares
    coeffs, _, _, _ = np.linalg.lstsq(M, u_tail, rcond=None)
    C1, C2 = coeffs
    
    A = np.sqrt(C1**2 + C2**2)
    
    # For free particle, amplitude is 1 (normalized to incoming flux 1)
    # S = A^2
    return A**2

def solve_yukawa_binding_energy(
    alpha: float, 
    m_phi: float, 
    mass: float = 1.0,
    r_max: float = 100.0,
    N_points: int = 10000
) -> Optional[float]:
    """
    Find the binding energy of the ground state (E < 0) for the Yukawa potential.
    Uses the Numerov method and a root finder to match boundary conditions at infinity.
    
    Args:
        alpha: Coupling strength.
        m_phi: Mediator mass.
        mass: Reduced mass of the system.
        r_max: Maximum radial distance.
        N_points: Number of grid points.
        
    Returns:
        Binding energy E (negative value), or None if no bound state found.
    """
    r = np.linspace(1e-6, r_max, N_points)
    h = r[1] - r[0]
    
    def potential_func(r_arr):
        return yukawa_potential(r_arr, alpha, m_phi)
    
    # We look for E such that u(r_max) -> 0 (bound state condition)
    # For E < 0, k = i * kappa. u(r) ~ exp(-kappa * r)
    # We search for E in range [-alpha^2 * mass / 2, 0] (approx hydrogenic)
    # Or simply scan for sign change in u(r_max)
    
    E_min = - (alpha**2 * mass) / 2.0 - 0.1 # Below ground state estimate
    E_max = -1e-6 # Just below zero
    
    # Function to evaluate u(r_max) for a given E
    def get_u_max(E):
        # k2 = 2*mu*(E - V)
        # For bound states, we expect exponential decay.
        # We integrate from 0 to r_max.
        # If E is too low, u blows up one way, if too high, it blows up the other.
        # Actually, for E < 0, V < 0, E-V is negative?
        # k2 = 2*mu*(E - V). V is negative. E is negative.
        # If |E| > |V|, k2 < 0 -> exponential.
        # We need the solution that decays at infinity.
        # Numerov from 0 will generally blow up unless E is an eigenvalue.
        # We look for the zero crossing of u(r_max).
        
        u = numerov_schrodinger(r, E, potential_func, l=0)
        return u[-1]
    
    try:
        # Check if sign changes
        val_min = get_u_max(E_min)
        val_max = get_u_max(E_max)
        
        if val_min * val_max > 0:
            # No root found in this range, or need better search
            return None
        
        E_bound = brentq(get_u_max, E_min, E_max, xtol=1e-8)
        return E_bound
    except ValueError:
        return None

def main():
    """
    Main entry point to demonstrate the Yukawa solver.
    Calculates the Sommerfeld factor for a benchmark point.
    """
    # Benchmark parameters (example)
    alpha = 0.01
    m_phi = 1.0 # Mediator mass
    mass = 100.0 # DM mass (reduced mass approx m/2 for equal mass)
    v = 1e-3 # Velocity
    
    # Energy E = 0.5 * mass * v^2
    E = 0.5 * mass * v**2
    k = np.sqrt(2 * mass * E)
    
    # Grid
    r_max = 50.0 / m_phi # Scale with mediator range
    N = 20000
    r = np.linspace(1e-6, r_max, N)
    
    # Define potential
    def pot(r_arr):
        return yukawa_potential(r_arr, alpha, m_phi)
    
    # Solve
    u = numerov_schrodinger(r, E, pot, l=0)
    
    # Extract S
    S = extract_sommerfeld_factor(u, r, k, mass)
    
    print(f"Yukawa Solver Benchmark:")
    print(f"  Alpha: {alpha}")
    print(f"  Mediator Mass: {m_phi}")
    print(f"  DM Mass: {mass}")
    print(f"  Velocity: {v}")
    print(f"  Calculated Sommerfeld Factor (S): {S:.4f}")
    
    # Check for bound state
    E_bound = solve_yukawa_binding_energy(alpha, m_phi, mass, r_max=r_max, N_points=N)
    if E_bound:
        print(f"  Ground State Binding Energy: {E_bound:.6f}")
    else:
        print("  No bound state found in the searched range.")

if __name__ == "__main__":
    main()
