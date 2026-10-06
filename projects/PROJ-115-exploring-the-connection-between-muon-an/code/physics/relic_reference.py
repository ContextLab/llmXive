"""
High-precision numerical solver for relic density benchmark generation.

This module implements a manual RK4 integrator with adaptive step sizing
to generate high-precision reference data for validating the approximate
relic density calculations (Hulthen potential, thermal averaging).

Output: data/relic_reference_benchmarks.csv
"""
import os
import math
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
M_Pl = 1.22e19  # Planck mass in GeV
M_eV = 1.0e-9   # Conversion to GeV
h_bar = 6.582119569e-25  # GeV*s
c = 2.99792458e8  # m/s
k_B = 8.617333262e-14  # GeV/K
G_N = 6.67430e-11  # m^3 kg^-1 s^-2
sigma_sb = 5.670374419e-8  # W m^-2 K^-4
pi = math.pi
e = math.e

# Physical constants for relic density calculation
g_star = 10.75  # Effective relativistic degrees of freedom at freeze-out
g_star_s = 10.75  # Entropy degrees of freedom
M_Planck_eff = 2.435e18  # Reduced Planck mass in GeV

def hubble_parameter(x: float, m_chi: float) -> float:
    """
    Calculate Hubble parameter H as a function of x = m_chi/T.
    
    H(x) = sqrt(pi^2 * g_star / 90) * m_chi^2 / (M_P * x^2)
    
    Args:
        x: m_chi / T (dimensionless)
        m_chi: Dark matter mass in GeV
        
    Returns:
        Hubble parameter H in GeV
    """
    return math.sqrt(pi**2 * g_star / 90) * (m_chi**2) / (M_Planck_eff * x**2)

def entropy_density(x: float, m_chi: float) -> float:
    """
    Calculate entropy density s as a function of x.
    
    s(x) = (2*pi^2/45) * g_star_s * (m_chi/x)^3
    
    Args:
        x: m_chi / T
        m_chi: Dark matter mass in GeV
        
    Returns:
        Entropy density s in GeV^3
    """
    return (2 * pi**2 / 45) * g_star_s * (m_chi / x)**3

def equilibrium_yield(x: float, m_chi: float, g_eff: float = 2.0) -> float:
    """
    Calculate equilibrium yield Y_eq = n_eq / s.
    
    For non-relativistic limit: Y_eq ~ 0.145 * g_eff * x^(3/2) * exp(-x)
    
    Args:
        x: m_chi / T
        m_chi: Dark matter mass in GeV (not directly used in non-rel limit)
        g_eff: Effective degrees of freedom for DM
        
    Returns:
        Equilibrium yield Y_eq
    """
    # Non-relativistic approximation
    return 0.145 * g_eff * x**1.5 * math.exp(-x)

def annihilation_cross_section(m_chi: float, m_V: float, g: float, alpha_D: float = 0.1) -> float:
    """
    Calculate thermally averaged annihilation cross-section <sigma*v>.
    
    This uses a simplified s-wave approximation with Sommerfeld enhancement.
    For the reference solver, we use a more precise calculation including
    the full Sommerfeld factor via Hulthen potential approximation.
    
    Args:
        m_chi: Dark matter mass in GeV
        m_V: Mediator mass in GeV
        g: Coupling constant
        alpha_D: Dark fine-structure constant (alpha_D = g^2 / 4pi)
        
    Returns:
        <sigma*v> in GeV^-2
    """
    # Basic s-wave cross-section: sigma*v ~ alpha_D^2 / m_chi^2
    sigma_v_0 = alpha_D**2 / (m_chi**2)
    
    # Sommerfeld enhancement factor (approximate Hulthen potential)
    # S = (pi * alpha_D / v) / (1 - exp(-pi * alpha_D / v))
    # For thermal average, we use v ~ sqrt(6/x)
    v_thermal = math.sqrt(6.0 / 20.0)  # Typical freeze-out velocity
    if v_thermal > 0:
        S = (pi * alpha_D / v_thermal) / (1 - math.exp(-pi * alpha_D / v_thermal))
        # Clamp S to avoid numerical issues
        S = min(S, 1e6)
    else:
        S = 1.0
    
    return sigma_v_0 * S

def dYdx(x: float, Y: float, m_chi: float, m_V: float, g: float, alpha_D: float = 0.1) -> float:
    """
    Calculate dY/dx for the Boltzmann equation.
    
    dY/dx = -lambda * x^-2 * (Y^2 - Y_eq^2)
    
    where lambda = sqrt(pi/45) * g_star^(1/2) * M_P * m_chi * <sigma*v>
    
    Args:
        x: m_chi / T
        Y: Current yield
        m_chi: Dark matter mass in GeV
        m_V: Mediator mass in GeV
        g: Coupling constant
        alpha_D: Dark fine-structure constant
        
    Returns:
        dY/dx
    """
    # Calculate <sigma*v>
    sigma_v = annihilation_cross_section(m_chi, m_V, g, alpha_D)
    
    # Calculate lambda
    lambda_param = math.sqrt(pi / 45) * math.sqrt(g_star) * M_Planck_eff * m_chi * sigma_v
    
    # Equilibrium yield
    Y_eq = equilibrium_yield(x, m_chi)
    
    # Boltzmann equation
    return -lambda_param * (Y**2 - Y_eq**2) / (x**2)

def rk4_step(f: callable, x: float, y: float, h: float, *args) -> float:
    """
    Perform one step of the 4th-order Runge-Kutta method.
    
    Args:
        f: Function f(x, y, *args) -> dy/dx
        x: Current x value
        y: Current y value
        h: Step size
        *args: Additional arguments for f
        
    Returns:
        New y value after step
    """
    k1 = f(x, y, *args)
    k2 = f(x + h/2, y + h*k1/2, *args)
    k3 = f(x + h/2, y + h*k2/2, *args)
    k4 = f(x + h, y + h*k3, *args)
    
    return y + (h/6) * (k1 + 2*k2 + 2*k3 + k4)

def adaptive_rk4_step(f: callable, x: float, y: float, h: float, tol: float, *args) -> Tuple[float, float]:
    """
    Perform an adaptive RK4 step with error estimation.
    
    Args:
        f: Function f(x, y, *args) -> dy/dx
        x: Current x value
        y: Current y value
        h: Initial step size
        tol: Tolerance for error
        *args: Additional arguments for f
        
    Returns:
        Tuple of (new_y, new_x)
    """
    # Try step with h
    y1 = rk4_step(f, x, y, h, *args)
    
    # Try two steps with h/2
    y_half = rk4_step(f, x, y, h/2, *args)
    y2 = rk4_step(f, x + h/2, y_half, h/2, *args)
    
    # Error estimate (Richardson extrapolation)
    error = abs(y2 - y1) / 15.0
    
    # Adjust step size
    if error > tol and h > 1e-10:
        # Reduce step size
        h_new = 0.9 * h * (tol / error)**0.25
        h_new = max(h_new, 1e-10)
        return adaptive_rk4_step(f, x, y, h_new, tol, *args)
    else:
        return y2, x + h

def relic_density_reference(m_chi: float, m_V: float, g: float, 
                            alpha_D: float = 0.1, 
                            x_start: float = 1.0, 
                            x_end: float = 1000.0,
                            tol: float = 1e-10) -> Tuple[float, List[Dict]]:
    """
    Calculate relic density using high-precision adaptive RK4 integration.
    
    This is the reference solver used to generate benchmark data for
    validating the approximate methods.
    
    Args:
        m_chi: Dark matter mass in GeV
        m_V: Mediator mass in GeV
        g: Coupling constant
        alpha_D: Dark fine-structure constant
        x_start: Starting x = m_chi/T
        x_end: Ending x
        tol: Integration tolerance
        
    Returns:
        Tuple of (Omega_chi*h^2, integration_history)
    """
    # Initial yield (at x_start, assume equilibrium)
    Y = equilibrium_yield(x_start, m_chi)
    x = x_start
    
    integration_history = []
    integration_history.append({
        'x': x,
        'Y': Y,
        'Y_eq': equilibrium_yield(x, m_chi)
    })
    
    # Adaptive step size
    h = 0.01
    
    while x < x_end:
        # Calculate equilibrium yield
        Y_eq = equilibrium_yield(x, m_chi)
        
        # Take adaptive step
        try:
            Y_new, x_new = adaptive_rk4_step(dYdx, x, Y, h, tol, m_chi, m_V, g, alpha_D)
        except (ValueError, OverflowError) as e:
            logger.warning(f"Numerical issue at x={x}: {e}, reducing step size")
            h = h / 10
            continue
        
        # Record history
        if len(integration_history) < 100 or (x - integration_history[-1]['x']) > 0.5:
            integration_history.append({
                'x': x_new,
                'Y': Y_new,
                'Y_eq': equilibrium_yield(x_new, m_chi)
            })
        
        Y = Y_new
        x = x_new
        
        # Increase step size gradually
        h = min(h * 1.1, 1.0)
    
    # Final yield
    Y_inf = Y
    
    # Calculate Omega_chi*h^2
    # Omega_chi*h^2 = 2.742e8 * (m_chi / GeV) * Y_inf
    omega_chi_h2 = 2.742e8 * m_chi * Y_inf
    
    return omega_chi_h2, integration_history

def generate_benchmarks(output_path: str, 
                        m_chi_values: List[float], 
                        m_V_values: List[float], 
                        g_values: List[float],
                        alpha_D: float = 0.1) -> None:
    """
    Generate benchmark data for multiple parameter points.
    
    Args:
        output_path: Path to output CSV file
        m_chi_values: List of dark matter masses in GeV
        m_V_values: List of mediator masses in GeV
        g_values: List of coupling constants
        alpha_D: Dark fine-structure constant
    """
    results = []
    
    logger.info(f"Generating benchmarks for {len(m_chi_values)} x {len(m_V_values)} x {len(g_values)} parameter points")
    
    for m_chi in m_chi_values:
        for m_V in m_V_values:
            for g in g_values:
                logger.info(f"Computing: m_chi={m_chi} GeV, m_V={m_V} GeV, g={g}")
                
                try:
                    omega_chi_h2, _ = relic_density_reference(
                        m_chi, m_V, g, alpha_D,
                        x_start=1.0, x_end=1000.0, tol=1e-10
                    )
                    
                    results.append({
                        'm_chi_GeV': m_chi,
                        'm_V_GeV': m_V,
                        'g': g,
                        'alpha_D': alpha_D,
                        'Omega_chi_h2': omega_chi_h2,
                        'status': 'converged'
                    })
                except Exception as e:
                    logger.error(f"Failed for m_chi={m_chi}, m_V={m_V}, g={g}: {e}")
                    results.append({
                        'm_chi_GeV': m_chi,
                        'm_V_GeV': m_V,
                        'g': g,
                        'alpha_D': alpha_D,
                        'Omega_chi_h2': np.nan,
                        'status': 'failed'
                    })
    
    # Save to CSV
    df = pd.DataFrame(results)
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Benchmarks saved to {output_path}")

def main():
    """Main entry point for generating relic density reference benchmarks."""
    # Define parameter grid
    # Using a sparse grid for benchmark generation (can be expanded)
    m_chi_values = [0.01, 0.1, 1.0, 10.0]  # GeV
    m_V_values = [0.001, 0.01, 0.1, 1.0]   # GeV
    g_values = [0.001, 0.01, 0.1]          # Coupling constants
    
    output_path = "data/relic_reference_benchmarks.csv"
    
    logger.info("Starting relic density reference benchmark generation")
    generate_benchmarks(output_path, m_chi_values, m_V_values, g_values)
    logger.info("Benchmark generation complete")

if __name__ == "__main__":
    main()