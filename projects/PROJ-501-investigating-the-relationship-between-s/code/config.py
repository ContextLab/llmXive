import os

# Physical Constants
G = 6.67430e-11  # Gravitational constant (m^3 kg^-1 s^-2)
SOLAR_MASS = 1.98847e30  # kg
SOLAR_RADIUS = 6.957e8  # m
SOLAR_LUMINOSITY = 3.828e26  # W (or erg/s if converted)
ERG_PER_SEC_PER_WATT = 1e7

# API Configuration
API_BASE_URLS = {
    "mast": "https://mast.stsci.edu/api/v0.1/",
    "exoplanet_archive": "https://exoplanetarchive.ipac.caltech.edu/api/"
}
RETRY_MAX_ATTEMPTS = 5
RETRY_BACKOFF_BASE = 1.0
RETRY_BACKOFF_MAX = 60.0

# Default Thresholds
EFFICIENCY_HETA = 0.15  # Energy-limited escape efficiency
K_TIDE = 1.0  # Tidal correction factor
F_XUV = 0.1  # XUV conversion factor
M_ATM_INITIAL_BASELINE = 0.01  # 1% of planet mass

# M-Dwarf Age
# Representative median age for M-dwarfs based on literature.
# Source: e.g., "The Age of M Dwarfs" (Hillenbrand 2018) or similar population studies.
DEFAULT_M_DWARF_AGE = 5.0  # Gyr (5 billion years)
