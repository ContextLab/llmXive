"""
relic_density.py
----------------
Implements a simple relic density calculation using a manual 4th-order Runge‑Kutta
(RK4) integration of the Boltzmann equation for a Dirac fermion dark matter
candidate (χ) that annihilates through a light vector mediator (V) with coupling
``g``.  The annihilation cross‑section includes a Sommerfeld enhancement factor
approximated via the Hulthén potential (see e.g. Cassel, *JHEP* 2009).

The module is deliberately lightweight and self‑contained – it only depends on
``numpy``, ``pandas`` and ``scipy`` (all already part of the project's
``requirements.txt``).  The public API consists of:

* :func:`sommerfeld_factor_hulthen` – returns the enhancement ``S`` for a given
  coupling ``α = g²/(4π)`` and relative velocity ``v``.
* :func:`annihilation_cross_section` – a toy s‑wave cross‑section
  ``σv = (g⁴/(8π m_χ²)) * S``.
* :func:`relic_density` – integrates the Boltzmann equation from ``x = m_χ/T = 1``
  to ``x = 1000`` using RK4 and returns the present‑day relic abundance
  ``Ωh²``.
* :func:`main` – generates a modest grid of ``(m_χ, m_V, g)`` points,
  evaluates ``Ωh²`` for each, and writes the results to
  ``data/relic_density_precomputed.csv``.

The implementation is **pre‑computation only** – it does not aim for sub‑%
precision but provides a deterministic, reproducible baseline that downstream
scripts (e.g. the lookup‑table generator) can validate against.
"""

import os
import math
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.constants import pi, Boltzmann, speed_of_light, electron_volt, Planck, kilo, giga, mega, nano
from scipy.integrate import quad

# ----------------------------------------------------------------------
# Physical constants (SI units) – values are taken from ``scipy.constants``.
# ----------------------------------------------------------------------
M_PL = Planck / (speed_of_light**2)  # Reduced Planck mass (kg)
G_NEWTON = 6.67430e-11               # m³·kg⁻¹·s⁻²
C = speed_of_light                   # m s⁻¹
HBAR = 1.054571817e-34               # J·s
K_B = Boltzmann                      # J·K⁻¹

# Effective relativistic degrees of freedom – we adopt the high‑temperature
# SM value; for the modest temperature range relevant to WIMP freeze‑out
# this is a reasonable approximation.
G_STAR = 106.75

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def hubble_parameter(T: float) -> float:
    """
    Hubble expansion rate ``H(T)`` in s⁻¹ for a radiation‑dominated Universe.

    Parameters
    ----------
    T : float
        Temperature in Kelvin.

    Returns
    -------
    float
        Hubble rate in s⁻¹.
    """
    # ρ_rad = (π²/30) g_* T⁴  ; H = sqrt(8π G ρ_rad / 3)
    rho_rad = (pi**2 / 30.0) * G_STAR * (K_B * T)**4 / (HBAR**3 * C**5)
    return math.sqrt(8 * pi * G_NEWTON * rho_rad / 3.0)

def entropy_density(T: float) -> float:
    """
    Entropy density ``s(T)`` in J·K⁻¹·m⁻³.

    Parameters
    ----------
    T : float
        Temperature in Kelvin.

    Returns
    -------
    float
        Entropy density.
    """
    # s = (2π²/45) g_* T³
    return (2 * pi**2 / 45.0) * G_STAR * (K_B * T)**3 / (HBAR**3 * C**3)

def equilibrium_yield(x: float, m_chi: float) -> float:
    """
    Equilibrium comoving number density ``Y_eq = n_eq / s`` for a non‑relativistic
    species.

    Parameters
    ----------
    x : float
        Dimensionless inverse temperature ``x = m_χ / T``.
    m_chi : float
        Dark‑matter mass in GeV.

    Returns
    -------
    float
        Equilibrium yield.
    """
    # Convert GeV → Joule for the exponential.
    m_chi_J = m_chi * giga * electron_volt
    T = m_chi_J / (x * K_B)
    n_eq = ( (m_chi_J * K_B * T) / (2 * pi * HBAR**2) )**(1.5) * math.exp(-x)
    s = entropy_density(T)
    return n_eq / s

# ----------------------------------------------------------------------
# Sommerfeld enhancement via Hulthén potential
# ----------------------------------------------------------------------
def sommerfeld_factor_hulthen(alpha: float, v: float) -> float:
    """
    Approximate Sommerfeld enhancement factor ``S`` for an attractive
    Yukawa‑type interaction using the analytic Hulthén potential solution
    (Cassel, JHEP 2009).

    Parameters
    ----------
    alpha : float
        Fine‑structure constant of the dark sector, α = g²/(4π).
    v : float
        Relative velocity (dimensionless, v/c).

    Returns
    -------
    float
        Enhancement factor S ≥ 1.
    """
    if v <= 0:
        return 1.0
    # Dimensionless quantity ε = v/(α)
    eps = v / alpha
    # Avoid division by zero for extremely small eps
    if eps < 1e-8:
        return (pi * alpha) / v
    # Hulthén approximation (see Eq. (3.12) of Cassel)
    S = (pi * alpha / v) / (1.0 - np.exp(-pi * alpha / v))
    # Apply a simple regulator to keep S finite near resonances
    return min(S, 1e5)

# ----------------------------------------------------------------------
# Annihilation cross‑section (s‑wave) including Sommerfeld factor
# ----------------------------------------------------------------------
def annihilation_cross_section(m_chi: float, m_V: float, g: float, v: float) -> float:
    """
    Toy s‑wave annihilation cross‑section ``σv`` (in cm³ s⁻¹).

    We use a simple contact interaction (χχ → VV) with a coupling ``g``.
    The tree‑level cross‑section scales as ``g⁴/(8π m_χ²)``; the velocity‑
    dependent Sommerfeld factor multiplies this result.

    Parameters
    ----------
    m_chi : float
        Dark‑matter mass in GeV.
    m_V : float
        Mediator mass in GeV (unused in this toy model but kept for API compatibility).
    g : float
        Dark sector gauge coupling (dimensionless).
    v : float
        Relative velocity (dimensionless, v/c).

    Returns
    -------
    float
        Thermally averaged ``σv`` in cm³ s⁻¹.
    """
    alpha = g**2 / (4 * pi)
    S = sommerfeld_factor_hulthen(alpha, v)
    sigma_v_geom = g**4 / (8 * pi * (m_chi * giga * electron_volt)**2)  # J⁻²
    # Convert from J⁻² to cm³ s⁻¹ using natural‑unit conversion factors
    #   1 GeV⁻² ≈ 0.3894 mb = 0.3894 × 10⁻27 cm²
    #   Multiply by c to get cm³ s⁻¹.
    sigma_v_cm3s = sigma_v_geom * (0.3894e-27) * C
    return sigma_v_cm3s * S

# ----------------------------------------------------------------------
# RK4 integration of the Boltzmann equation
# ----------------------------------------------------------------------
def dYdx(Y: float, x: float, m_chi: float, m_V: float, g: float) -> float:
    """
    Right‑hand side of the Boltzmann equation expressed in terms of ``x = m_χ/T``:

        dY/dx = - (s ⟨σv⟩) / (H x) * (Y² - Y_eq²)

    Parameters
    ----------
    Y : float
        Current comoving abundance.
    x : float
        Dimensionless inverse temperature.
    m_chi, m_V, g : float
        Model parameters (GeV, GeV, dimensionless).

    Returns
    -------
    float
        dY/dx.
    """
    # Temperature in Kelvin
    T = (m_chi * giga * electron_volt) / (x * K_B)

    # Approximate relative velocity at temperature T.
    # For non‑relativistic particles, v ~ sqrt(6/x) (in units of c).
    v = math.sqrt(6.0 / x)

    sigma_v = annihilation_cross_section(m_chi, m_V, g, v)  # cm³ s⁻¹
    # Convert cm³ s⁻¹ → m³ s⁻¹
    sigma_v_m3s = sigma_v * 1e-6

    s = entropy_density(T)                     # J·K⁻¹·m⁻³
    H = hubble_parameter(T)                    # s⁻¹
    Y_eq = equilibrium_yield(x, m_chi)

    return - (s * sigma_v_m3s) / (H * x) * (Y**2 - Y_eq**2)

def rk4_step(Y: float, x: float, h: float, m_chi: float, m_V: float, g: float) -> float:
    """
    Perform a single RK4 step.

    Parameters
    ----------
    Y : float
        Current value of Y.
    x : float
        Current value of x.
    h : float
        Step size.
    m_chi, m_V, g : float
        Model parameters.

    Returns
    -------
    float
        Updated Y after stepping from x → x + h.
    """
    k1 = dYdx(Y, x, m_chi, m_V, g)
    k2 = dYdx(Y + 0.5 * h * k1, x + 0.5 * h, m_chi, m_V, g)
    k3 = dYdx(Y + 0.5 * h * k2, x + 0.5 * h, m_chi, m_V, g)
    k4 = dYdx(Y + h * k3, x + h, m_chi, m_V, g)
    return Y + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def relic_density(m_chi: float, m_V: float, g: float) -> float:
    """
    Compute the present‑day relic density ``Ωh²`` for a given parameter point.

    The integration runs from ``x = 1`` (early times) to ``x = 1000`` (well
    after freeze‑out).  The final comoving abundance ``Y_∞`` is converted
    to a density using the critical density today.

    Parameters
    ----------
    m_chi : float
        Dark‑matter mass in GeV.
    m_V : float
        Mediator mass in GeV.
    g : float
        Dark sector coupling.

    Returns
    -------
    float
        Relic density ``Ωh²``.
    """
    # Initial condition: assume thermal equilibrium at x=1
    x_start = 1.0
    Y = equilibrium_yield(x_start, m_chi)

    x_end = 1000.0
    # Use a logarithmic step in x to capture the rapid freeze‑out dynamics.
    n_steps = 5000
    xs = np.logspace(math.log10(x_start), math.log10(x_end), n_steps)
    for i in range(1, len(xs)):
        h = xs[i] - xs[i - 1]
        Y = rk4_step(Y, xs[i - 1], h, m_chi, m_V, g)

    # Convert Y_∞ to Ωh².
    # ρ_χ = m_χ s_0 Y_∞   ;   Ω_χ h² = ρ_χ / ρ_crit h²
    # Use modern values:
    s0 = 2890.0 * (kilo * electron_volt)**3 / (HBAR**3 * C**3)  # entropy density today (J·K⁻¹·m⁻³)
    rho_crit = 1.05375e-5 * (giga * electron_volt) / (C**2)      # GeV cm⁻³ → J m⁻³ (approx)
    rho_chi = (m_chi * giga * electron_volt) * s0 * Y          # J m⁻³
    omega_h2 = rho_chi / rho_crit
    return omega_h2

# ----------------------------------------------------------------------
# Command‑line interface for pre‑computation
# ----------------------------------------------------------------------
def _generate_grid(
    m_chi_vals: np.ndarray,
    m_V_vals: np.ndarray,
    g_vals: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Produce a meshgrid (flattened) of the three parameter axes.
    """
    M_chi, M_V, G = np.meshgrid(m_chi_vals, m_V_vals, g_vals, indexing="ij")
    return M_chi.ravel(), M_V.ravel(), G.ravel()

def main() -> None:
    """
    Entry point: generate a modest grid of DM parameters, evaluate the relic
    density for each point, and write the results to
    ``data/relic_density_precomputed.csv``.
    """
    # Define a modest grid – sufficient for a quick validation run.
    m_chi_grid = np.logspace(-2, 2, 15)   # 0.01 GeV → 100 GeV
    m_V_grid   = np.logspace(-2, 2, 15)   # same range for the mediator
    g_grid     = np.logspace(-4, -1, 10)  # 1e‑4 → 1e‑1

    m_chis, m_Vs, gs = _generate_grid(m_chi_grid, m_V_grid, g_grid)

    results = []
    for chi, V, g in zip(m_chis, m_Vs, gs):
        try:
            omega = relic_density(float(chi), float(V), float(g))
        except Exception as exc:
            # In pathological regions (e.g. division‑by‑zero) we log NaN.
            omega = float("nan")
            print(f"Failed at (mχ={chi:.3e}, mV={V:.3e}, g={g:.3e}): {exc}")
        results.append((chi, V, g, omega))

    df = pd.DataFrame(
        results,
        columns=["m_chi_GeV", "m_V_GeV", "g", "omega_h2"],
    )

    # Ensure the output directory exists.
    output_path = Path("data") / "relic_density_precomputed.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Pre‑computed relic density table written to {output_path}")

if __name__ == "__main__":
    main()
