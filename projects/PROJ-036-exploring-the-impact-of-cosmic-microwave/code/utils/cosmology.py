"""
Base cosmology constants module for llmXive PROJ-036.

Provides standard cosmological parameters and utility functions for
calculating derived cosmological quantities based on the Lambda-CDM model
and anomaly configurations.

This module interfaces with config/lambdacdm.yaml and config/anomaly.yaml
via the existing config_manager.
"""

import numpy as np
from typing import Dict, Any, Optional, Tuple

from utils.config_manager import load_lambdacdm_config, load_anomaly_config, get_combined_config


# Physical constants (SI units)
C_SPEED = 299792458.0  # Speed of light in m/s
G_NEWTON = 6.67430e-11  # Gravitational constant in m^3 kg^-1 s^-2
H0_SI = 100.0  # h * 100 km/s/Mpc conversion factor (km/s/Mpc)

# Standard cosmological constants (Planck 2018 baseline)
# These serve as defaults if config is unavailable
DEFAULT_LAMBDACDM = {
    'H0': 67.66,  # km/s/Mpc
    'Omega_m': 0.30966,
    'Omega_b': 0.04897,
    'Omega_Lambda': 0.69034,
    'Omega_r': 9.15e-5,
    'sigma8': 0.8102,
    'n_s': 0.9665,
    'age_gyr': 13.797,
    'h': 0.6766,
}

# Anomaly baseline parameters (Planck 2018 Cold Spot region)
DEFAULT_ANOMALY = {
    'cold_spot_center_galactic': (209.0, -57.0),  # l, b in degrees
    'cold_spot_radius_deg': 5.0,
    'low_quad_multipoles': [2, 3, 4],  # l values for low quadrupole
    'phase_injection_strength': 0.0,  # Default: no injection
    'mode_coupling_epsilon': 0.1,  # Mode coupling approximation parameter
}


class CosmologyParams:
    """
    Container for cosmological parameters with derived quantities.

    Attributes:
        H0 (float): Hubble constant in km/s/Mpc
        h (float): Dimensionless Hubble parameter (H0 / 100)
        Omega_m (float): Matter density parameter
        Omega_b (float): Baryon density parameter
        Omega_Lambda (float): Dark energy density parameter
        Omega_r (float): Radiation density parameter
        sigma8 (float): RMS matter fluctuation at 8 h^-1 Mpc
        n_s (float): Spectral index
        age_gyr (float): Age of the universe in Gyr
    """

    def __init__(self, params: Dict[str, Any]):
        """Initialize with a dictionary of parameters."""
        self.H0 = float(params.get('H0', DEFAULT_LAMBDACDM['H0']))
        self.h = float(params.get('h', self.H0 / 100.0))
        self.Omega_m = float(params.get('Omega_m', DEFAULT_LAMBDACDM['Omega_m']))
        self.Omega_b = float(params.get('Omega_b', DEFAULT_LAMBDACDM['Omega_b']))
        self.Omega_Lambda = float(params.get('Omega_Lambda', DEFAULT_LAMBDACDM['Omega_Lambda']))
        self.Omega_r = float(params.get('Omega_r', DEFAULT_LAMBDACDM['Omega_r']))
        self.sigma8 = float(params.get('sigma8', DEFAULT_LAMBDACDM['sigma8']))
        self.n_s = float(params.get('n_s', DEFAULT_LAMBDACDM['n_s']))
        self.age_gyr = float(params.get('age_gyr', DEFAULT_LAMBDACDM['age_gyr']))

    @property
    def Omega_k(self) -> float:
        """Calculate curvature density parameter (assuming flatness: Omega_k = 1 - Omega_total)."""
        return 1.0 - (self.Omega_m + self.Omega_Lambda + self.Omega_b + self.Omega_r)

    @property
    def critical_density_h(self) -> float:
        """
        Calculate critical density in units of h^2 M_sun / Mpc^3.

        Returns:
            float: Critical density parameter
        """
        # Critical density rho_c = 3H0^2 / (8πG)
        # In units of M_sun/Mpc^3: rho_c = 2.775e11 * h^2 M_sun/Mpc^3
        return 2.775e11 * self.h ** 2

    def hubble_distance_mpc(self) -> float:
        """
        Calculate Hubble distance in Mpc.

        Returns:
            float: c / H0 in Mpc
        """
        # c in km/s, H0 in km/s/Mpc -> result in Mpc
        return C_SPEED / 1000.0 / self.H0 * 1e6 / 1e6  # Convert to Mpc

    def comoving_distance_to_z(self, z: float) -> float:
        """
        Calculate approximate comoving distance to redshift z (flat universe).

        Args:
            z (float): Redshift

        Returns:
            float: Comoving distance in Mpc
        """
        if z < 0:
            raise ValueError("Redshift must be non-negative")

        # Simple approximation: integrate 1/E(z) from 0 to z
        # E(z) = sqrt(Omega_m*(1+z)^3 + Omega_Lambda)
        # For small z, D_c ≈ c/H0 * z
        if z < 0.1:
            return self.hubble_distance_mpc() * z

        # Numerical integration (trapezoidal rule)
        n_steps = 1000
        dz = z / n_steps
        integral = 0.0

        for i in range(n_steps):
            z_i = i * dz
            E_z = np.sqrt(
                self.Omega_m * (1 + z_i) ** 3 +
                self.Omega_Lambda +
                self.Omega_r * (1 + z_i) ** 4
            )
            integral += 1.0 / E_z

        # Average for trapezoidal
        integral *= dz
        return self.hubble_distance_mpc() * integral

    def to_dict(self) -> Dict[str, float]:
        """Return parameters as a dictionary."""
        return {
            'H0': self.H0,
            'h': self.h,
            'Omega_m': self.Omega_m,
            'Omega_b': self.Omega_b,
            'Omega_Lambda': self.Omega_Lambda,
            'Omega_r': self.Omega_r,
            'Omega_k': self.Omega_k,
            'sigma8': self.sigma8,
            'n_s': self.n_s,
            'age_gyr': self.age_gyr,
            'critical_density_h': self.critical_density_h,
            'hubble_distance_mpc': self.hubble_distance_mpc(),
        }

    def __repr__(self) -> str:
        return f"CosmologyParams(H0={self.H0}, Omega_m={self.Omega_m}, Omega_Lambda={self.Omega_Lambda})"


class AnomalyConfig:
    """
    Container for CMB anomaly configuration parameters.

    Attributes:
        cold_spot_center (Tuple[float, float]): Galactic coordinates (l, b) in degrees
        cold_spot_radius (float): Radius of Cold Spot region in degrees
        low_quad_multipoles (List[int]): Multipole moments for low quadrupole
        phase_injection_strength (float): Strength of phase injection
        mode_coupling_epsilon (float): Mode coupling approximation parameter
    """

    def __init__(self, params: Dict[str, Any]):
        """Initialize with anomaly configuration."""
        self.cold_spot_center = tuple(params.get(
            'cold_spot_center_galactic',
            DEFAULT_ANOMALY['cold_spot_center_galactic']
        ))
        self.cold_spot_radius = float(params.get(
            'cold_spot_radius_deg',
            DEFAULT_ANOMALY['cold_spot_radius_deg']
        ))
        self.low_quad_multipoles = list(params.get(
            'low_quad_multipoles',
            DEFAULT_ANOMALY['low_quad_multipoles']
        ))
        self.phase_injection_strength = float(params.get(
            'phase_injection_strength',
            DEFAULT_ANOMALY['phase_injection_strength']
        ))
        self.mode_coupling_epsilon = float(params.get(
            'mode_coupling_epsilon',
            DEFAULT_ANOMALY['mode_coupling_epsilon']
        ))

    def is_cold_spot_region(self, galactic_l: float, galactic_b: float) -> bool:
        """
        Check if a point is within the Cold Spot region.

        Args:
            galactic_l (float): Galactic longitude in degrees
            galactic_b (float): Galactic latitude in degrees

        Returns:
            bool: True if point is within Cold Spot radius
        """
        # Angular distance on sphere (approximate for small angles)
        dl = np.radians(galactic_l - self.cold_spot_center[0])
        db = np.radians(galactic_b - self.cold_spot_center[1])
        angular_dist = np.degrees(np.sqrt(dl**2 + db**2))
        return angular_dist <= self.cold_spot_radius

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return {
            'cold_spot_center_galactic': self.cold_spot_center,
            'cold_spot_radius_deg': self.cold_spot_radius,
            'low_quad_multipoles': self.low_quad_multipoles,
            'phase_injection_strength': self.phase_injection_strength,
            'mode_coupling_epsilon': self.mode_coupling_epsilon,
        }

    def __repr__(self) -> str:
        return f"AnomalyConfig(center={self.cold_spot_center}, radius={self.cold_spot_radius}°)"


def get_cosmology_params(
    use_config: bool = True,
    config_path: Optional[str] = None
) -> CosmologyParams:
    """
    Get cosmological parameters from config or defaults.

    Args:
        use_config (bool): If True, load from config files; otherwise use defaults
        config_path (str, optional): Path to config directory (relative to project root)

    Returns:
        CosmologyParams: Initialized cosmology parameters object
    """
    if use_config:
        try:
            config = get_combined_config(config_path=config_path)
            return CosmologyParams(config)
        except Exception as e:
            # Fallback to defaults if config loading fails
            print(f"Warning: Failed to load config, using defaults: {e}")
            return CosmologyParams(DEFAULT_LAMBDACDM)
    else:
        return CosmologyParams(DEFAULT_LAMBDACDM)


def get_anomaly_config(
    use_config: bool = True,
    config_path: Optional[str] = None
) -> AnomalyConfig:
    """
    Get anomaly configuration from config or defaults.

    Args:
        use_config (bool): If True, load from config files; otherwise use defaults
        config_path (str, optional): Path to config directory

    Returns:
        AnomalyConfig: Initialized anomaly configuration object
    """
    if use_config:
        try:
            config = load_anomaly_config(config_path=config_path)
            return AnomalyConfig(config)
        except Exception as e:
            # Fallback to defaults if config loading fails
            print(f"Warning: Failed to load anomaly config, using defaults: {e}")
            return AnomalyConfig(DEFAULT_ANOMALY)
    else:
        return AnomalyConfig(DEFAULT_ANOMALY)


def calculate_hubble_parameter(z: float, params: CosmologyParams) -> float:
    """
    Calculate H(z) = H0 * E(z) at redshift z.

    Args:
        z (float): Redshift
        params (CosmologyParams): Cosmological parameters

    Returns:
        float: Hubble parameter at redshift z in km/s/Mpc
    """
    E_z = np.sqrt(
        params.Omega_m * (1 + z) ** 3 +
        params.Omega_Lambda +
        params.Omega_r * (1 + z) ** 4 +
        params.Omega_k * (1 + z) ** 2
    )
    return params.H0 * E_z


def calculate_growth_factor(z: float, params: CosmologyParams) -> float:
    """
    Calculate linear growth factor D(z) relative to D(z=0)=1.

    Args:
        z (float): Redshift
        params (CosmologyParams): Cosmological parameters

    Returns:
        float: Growth factor at redshift z
    """
    # Approximate growth factor for flat Lambda-CDM
    # D(z) ≈ g(z) / (1+z) where g(z) is growth suppression factor
    # g(z) ≈ 5/2 * Omega_m(z) / [Omega_m(z)^(4/7) - Omega_Lambda(z) + (1 + Omega_m(z)/2)*(1 + Omega_Lambda(z)/70)]

    Omega_m_z = params.Omega_m * (1 + z) ** 3 / (
        params.Omega_m * (1 + z) ** 3 +
        params.Omega_Lambda +
        params.Omega_r * (1 + z) ** 4 +
        params.Omega_k * (1 + z) ** 2
    )

    Omega_Lambda_z = params.Omega_Lambda / (
        params.Omega_m * (1 + z) ** 3 +
        params.Omega_Lambda +
        params.Omega_r * (1 + z) ** 4 +
        params.Omega_k * (1 + z) ** 2
    )

    denominator = (
        Omega_m_z ** (4/7) -
        Omega_Lambda_z +
        (1 + Omega_m_z / 2) * (1 + Omega_Lambda_z / 70)
    )

    g_z = (5/2) * Omega_m_z / denominator
    return g_z / (1 + z)


def main():
    """Main function for standalone testing of cosmology module."""
    print("Testing Cosmology module...")

    # Test default parameters
    params = get_cosmology_params(use_config=False)
    print(f"Default Cosmology: {params}")
    print(f"  H0 = {params.H0} km/s/Mpc")
    print(f"  Omega_m = {params.Omega_m}")
    print(f"  Omega_Lambda = {params.Omega_Lambda}")
    print(f"  Critical density (h^2) = {params.critical_density_h:.2e} M_sun/Mpc^3")

    # Test H(z) calculation
    for z in [0, 0.5, 1.0, 2.0, 5.0]:
        h_z = calculate_hubble_parameter(z, params)
        growth = calculate_growth_factor(z, params)
        print(f"  z={z}: H(z)={h_z:.2f} km/s/Mpc, D(z)={growth:.4f}")

    # Test anomaly config
    anomaly = get_anomaly_config(use_config=False)
    print(f"\nDefault Anomaly Config: {anomaly}")
    print(f"  Cold Spot center: {anomaly.cold_spot_center}")
    print(f"  Cold Spot radius: {anomaly.cold_spot_radius}°")

    # Test cold spot region check
    test_l, test_b = 209.0, -57.0  # Center
    print(f"  Point at center ({test_l}, {test_b}): {anomaly.is_cold_spot_region(test_l, test_b)}")
    test_l, test_b = 209.0, -50.0  # Within radius
    print(f"  Point at ({test_l}, {test_b}): {anomaly.is_cold_spot_region(test_l, test_b)}")
    test_l, test_b = 209.0, -5.0  # Outside radius
    print(f"  Point at ({test_l}, {test_b}): {anomaly.is_cold_spot_region(test_l, test_b)}")

    print("\nCosmology module tests completed.")


if __name__ == "__main__":
    main()