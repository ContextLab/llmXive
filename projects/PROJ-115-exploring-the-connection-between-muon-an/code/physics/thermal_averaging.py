"""
Thermal averaging of the Sommerfeld-enhanced annihilation cross-section.

Implements the calculation of <σv> over a Maxwell-Boltzmann distribution
as required for relic density calculations in the presence of Sommerfeld enhancement.

References:
- FR-002: Sommerfeld enhancement implementation
- User Story 4: Relic Density Validation
"""
import numpy as np
from scipy.integrate import quad
from typing import Callable, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Physical constants (natural units where c = hbar = k_B = 1)
# These are consistent with the rest of the physics module
PI = np.pi

def maxwell_boltzmann_distribution(v: np.ndarray, T: float, m_chi: float) -> np.ndarray:
    """
    Calculate the Maxwell-Boltzmann velocity distribution function.
    
    f(v) dv = 4 * pi * (m / (2 * pi * T))^(3/2) * v^2 * exp(-m * v^2 / (2 * T))
    
    Args:
        v: Velocity array (dimensionless, v/c)
        T: Temperature in natural units (same as mass units)
        m_chi: Dark matter particle mass
        
    Returns:
        Probability density values for each velocity
    """
    if T <= 0:
        raise ValueError(f"Temperature must be positive, got {T}")
    
    prefactor = 4.0 * PI * (m_chi / (2.0 * PI * T))**1.5
    exponent = -m_chi * v**2 / (2.0 * T)
    
    # Handle potential overflow in exponent for large v
    # For very negative exponents, the term approaches 0
    result = np.zeros_like(v, dtype=np.float64)
    mask = exponent > -700  # Avoid underflow
    result[mask] = prefactor * v[mask]**2 * np.exp(exponent[mask])
    
    return result

def sommerfeld_enhanced_cross_section(
    v: float, 
    m_chi: float, 
    m_V: float, 
    alpha: float,
    sommerfeld_func: Optional[Callable[[float, float, float, float], float]] = None
) -> float:
    """
    Calculate the Sommerfeld-enhanced annihilation cross-section.
    
    σv = S(v) * (σv)_0
    
    where S(v) is the Sommerfeld enhancement factor and (σv)_0 is the
    perturbative cross-section.
    
    Args:
        v: Relative velocity (dimensionless)
        m_chi: Dark matter mass
        m_V: Mediator mass
        alpha: Coupling constant
        sommerfeld_func: Optional callable for custom Sommerfeld calculation.
                        If None, uses Hulthen potential approximation.
                        
    Returns:
        Enhanced cross-section times velocity
    """
    if v <= 0:
        # At zero velocity, we need to handle the limit carefully
        # For s-wave annihilation, σv is finite at v=0
        v = 1e-12  # Small but non-zero to avoid division issues
    
    # Perturbative cross-section (s-wave approximation)
    # (σv)_0 ≈ (πα²) / m_chi² for simple models
    sigma_v_0 = (PI * alpha**2) / (m_chi**2)
    
    # Calculate Sommerfeld enhancement factor
    if sommerfeld_func is not None:
        S = sommerfeld_func(v, m_chi, m_V, alpha)
    else:
        # Use Hulthen potential approximation for Sommerfeld factor
        # S = (π α / v) / (1 - exp(-π α / v)) * (sinh(π α m_chi / (m_V * v)) / 
    #      (cosh(π α m_chi / (m_V * v)) - cos(π sqrt(2 m_chi α / m_V - (π α m_chi / (m_V * v))²))))
    # Simplified Hulthen approximation:
        S = sommerfeld_factor_hulthen_approx(v, m_chi, m_V, alpha)
    
    return S * sigma_v_0

def sommerfeld_factor_hulthen_approx(v: float, m_chi: float, m_V: float, alpha: float) -> float:
    """
    Approximate Sommerfeld enhancement factor using Hulthen potential.
    
    This is a simplified version of the Hulthen potential calculation.
    For more precise calculations, use the full numerical solution from yukawa_solver.py.
    
    Args:
        v: Relative velocity
        m_chi: Dark matter mass
        m_V: Mediator mass
        alpha: Coupling constant
        
    Returns:
        Sommerfeld enhancement factor S
    """
    if v <= 0:
        v = 1e-12
    
    # Dimensionless parameters
    epsilon_v = v / (alpha * np.pi)
    epsilon_phi = m_V / (alpha * m_chi)
    
    # Avoid division by zero
    if epsilon_v < 1e-10:
        epsilon_v = 1e-10
    
    # Hulthen potential approximation
    # S = (π/epsilon_v) * sinh(2π*epsilon_v/epsilon_phi) / (cosh(2π*epsilon_v/epsilon_phi) - cos(2π*sqrt(1/epsilon_phi - epsilon_v²/epsilon_phi²)))
    
    # Simplified for small epsilon_v (low velocity):
    # S ≈ (π α / v) / (1 - exp(-π α / v)) when m_V << m_chi
    
    if epsilon_phi < 1e-3:
        # Deep bound state regime
        S = (PI * alpha / v) / (1 - np.exp(-PI * alpha / v))
    else:
        # General Hulthen approximation
        arg = 2 * PI * epsilon_v / epsilon_phi
        S = (PI / epsilon_v) * np.sinh(arg) / (np.cosh(arg) - np.cos(2 * PI * np.sqrt(max(0, 1/epsilon_phi - (epsilon_v/epsilon_phi)**2))))
    
    # Clamp to reasonable values to avoid numerical issues
    S = max(1.0, min(S, 1e10))
    
    return S

def thermal_average_cross_section(
    m_chi: float,
    m_V: float,
    alpha: float,
    x: float,
    sommerfeld_func: Optional[Callable[[float, float, float, float], float]] = None,
    rel_tol: float = 1e-6,
    abs_tol: float = 1e-12
) -> float:
    """
    Calculate the thermally averaged Sommerfeld-enhanced cross-section <σv>.
    
    <σv> = ∫ σv(v) * f(v) * 4πv² dv
    
    where f(v) is the Maxwell-Boltzmann distribution at temperature T = m_chi/x.
    
    Args:
        m_chi: Dark matter particle mass
        m_V: Mediator mass
        alpha: Coupling constant
        x: m_chi / T (freeze-out parameter, typically 20-30)
        sommerfeld_func: Optional custom Sommerfeld factor function
        rel_tol: Relative tolerance for integration
        abs_tol: Absolute tolerance for integration
        
    Returns:
        Thermally averaged cross-section <σv>
    """
    if x <= 0:
        raise ValueError(f"x must be positive, got {x}")
    
    # Temperature in natural units
    T = m_chi / x
    
    # Define the integrand: σv(v) * v² * exp(-m_chi * v² / (2T))
    def integrand(v: float) -> float:
        if v <= 0:
            return 0.0
        sigma_v = sommerfeld_enhanced_cross_section(v, m_chi, m_V, alpha, sommerfeld_func)
        # Maxwell-Boltzmann factor (excluding normalization, which we'll handle separately)
        mb_factor = v**2 * np.exp(-m_chi * v**2 / (2.0 * T))
        return sigma_v * mb_factor
    
    # Integration range: v from 0 to ~10 (relativistic limit, but DM is non-relativistic)
    # For non-relativistic DM, most contribution comes from v << 1
    v_max = 1.0  # v/c = 1 is relativistic, but we integrate to capture the tail
    
    try:
        result, error = quad(
            integrand, 
            0, 
            v_max,
            epsrel=rel_tol,
            epsabs=abs_tol,
            limit=100
        )
    except Exception as e:
        logger.warning(f"Integration failed with error: {e}. Using fallback integration.")
        # Fallback: use a simpler integration method
        v_values = np.linspace(0, v_max, 1000)[1:]  # Skip v=0
        sigma_v_values = np.array([sommerfeld_enhanced_cross_section(v, m_chi, m_V, alpha, sommerfeld_func) for v in v_values])
        mb_values = v_values**2 * np.exp(-m_chi * v_values**2 / (2.0 * T))
        result = np.trapz(sigma_v_values * mb_values, v_values)
        error = 0.0
    
    # Normalization factor for Maxwell-Boltzmann distribution
    normalization = 4 * PI * (m_chi / (2 * PI * T))**1.5
    
    return result * normalization

def calculate_sommerfeld_averaged_cross_section_grid(
    m_chi_values: np.ndarray,
    m_V_values: np.ndarray,
    x_values: np.ndarray,
    alpha: float = 0.01,
    sommerfeld_func: Optional[Callable[[float, float, float, float], float]] = None
) -> np.ndarray:
    """
    Calculate <σv> over a grid of parameters for efficiency.
    
    Args:
        m_chi_values: Array of dark matter masses
        m_V_values: Array of mediator masses
        x_values: Array of m_chi/T values
        alpha: Coupling constant
        sommerfeld_func: Optional custom Sommerfeld factor function
        
    Returns:
        3D array of <σv> values with shape (len(m_chi), len(m_V), len(x))
    """
    results = np.zeros((len(m_chi_values), len(m_V_values), len(x_values)))
    
    for i, m_chi in enumerate(m_chi_values):
        for j, m_V in enumerate(m_V_values):
            for k, x in enumerate(x_values):
                results[i, j, k] = thermal_average_cross_section(
                    m_chi, m_V, alpha, x, sommerfeld_func
                )
    
    return results

def main():
    """
    Demonstration of thermal averaging calculation.
    """
    # Example parameters
    m_chi = 10.0  # GeV
    m_V = 0.1    # GeV
    alpha = 0.01
    x = 25.0     # Typical freeze-out value
    
    print(f"Calculating thermally averaged cross-section for:")
    print(f"  m_chi = {m_chi} GeV")
    print(f"  m_V = {m_V} GeV")
    print(f"  alpha = {alpha}")
    print(f"  x = {x}")
    
    sigma_v_avg = thermal_average_cross_section(m_chi, m_V, alpha, x)
    
    print(f"  <σv> = {sigma_v_avg:.6e} GeV^-2")
    
    # Compare with perturbative value (no Sommerfeld)
    sigma_v_pert = sommerfeld_enhanced_cross_section(0.1, m_chi, m_V, alpha, lambda v, mc, mV, a: 1.0)
    print(f"  Perturbative σv (at v=0.1) = {sigma_v_pert:.6e} GeV^-2")
    
    # Calculate Sommerfeld enhancement at typical velocity
    v_typical = np.sqrt(6.0 * x)  # Typical thermal velocity
    S_typical = sommerfeld_factor_hulthen_approx(v_typical, m_chi, m_V, alpha)
    print(f"  Typical velocity v = {v_typical:.4f}")
    print(f"  Sommerfeld factor S(v) = {S_typical:.4f}")

if __name__ == "__main__":
    main()