import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, Any, List, Tuple, Optional
import logging
from dataclasses import dataclass, field
import os
from pathlib import Path

from utils import setup_logging, get_project_root, get_data_dir
from data_ingestion import GeometryConfig

logger = setup_logging(__name__)

@dataclass
class ThermalState:
    """State vector for the 1D thermal simulation."""
    T_glass: float  # Glass cover temperature (K)
    T_plate: float  # Absorber plate temperature (K)
    T_water: float  # Water bulk temperature (K)
    T_base: float   # Insulation base temperature (K)

def get_solar_irradiance_profile(time_hours: np.ndarray) -> np.ndarray:
    """
    Retrieve solar irradiance profile from the data fetched in T008.
    Interpolates the data to match the requested time steps.
    
    Args:
        time_hours: Array of time points in hours (0-24)
        
    Returns:
        Array of solar irradiance values (W/m^2)
    """
    data_dir = get_data_dir()
    irradiance_file = data_dir / "raw" / "solar_irradiance.csv"
    
    if not irradiance_file.exists():
        raise FileNotFoundError(
            f"Solar irradiance data not found at {irradiance_file}. "
            "Please ensure T008 has completed successfully."
        )
    
    import pandas as pd
    df = pd.read_csv(irradiance_file)
    
    # Ensure required columns exist
    if 'time' not in df.columns or 'irradiance' not in df.columns:
        raise ValueError(
            f"Irradiance file {irradiance_file} missing required columns. "
            "Expected 'time' and 'irradiance'."
        )
    
    # Filter for daylight hours (approx 6 AM to 6 PM) and interpolate
    daylight_mask = (df['time'] >= 6) & (df['time'] <= 18)
    daylight_df = df[daylight_mask].copy()
    
    if len(daylight_df) < 2:
        logger.warning("Insufficient daylight data points. Using flat profile.")
        return np.ones_like(time_hours) * 800.0  # Default midday value
        
    # Interpolate irradiance for requested times
    irradiance_values = np.interp(time_hours, daylight_df['time'], daylight_df['irradiance'])
    
    # Set night time to zero
    irradiance_values[time_hours < 6] = 0.0
    irradiance_values[time_hours > 18] = 0.0
    
    return irradiance_values

def calculate_view_factor(geometry: GeometryConfig, angle: float) -> float:
    """
    Calculate the view factor for the given geometry and solar angle.
    Uses geometric projections based on the inclination angle.
    """
    inclination_rad = np.radians(geometry.inclination_angle)
    solar_rad = np.radians(angle)
    
    # Simple projection model: cos(inclination - solar_angle)
    # Clamped to [0, 1]
    factor = np.cos(inclination_rad - solar_rad)
    return max(0.0, min(1.0, factor))

def calculate_convective_coeff(temp_diff: float, geometry: GeometryConfig) -> float:
    """
    Calculate convective heat transfer coefficient based on temperature difference.
    Uses a simplified natural convection model.
    """
    if temp_diff <= 0:
        return 5.0  # Minimum coefficient for still air
    
    # Empirical correlation for natural convection
    h = 1.31 * (temp_diff ** 0.33)
    return max(5.0, min(25.0, h))  # Clamp to realistic range

def thermal_ode_system(t: float, y: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """
    Define the 1D transient heat transfer ODE system.
    
    State vector y: [T_glass, T_plate, T_water, T_base]
    Returns: dT/dt for each component
    
    Boundary conditions incorporate solar irradiance from T008 data.
    """
    T_glass, T_plate, T_water, T_base = y
    
    # Extract parameters
    irradiance = params['irradiance'](t)  # W/m^2
    T_ambient = params['T_ambient']  # K
    geometry = params['geometry']
    materials = params['materials']
    
    # Physical constants
    sigma = 5.67e-8  # Stefan-Boltzmann constant
    
    # View factor and effective irradiance
    # Assume midday sun for simplicity in this ODE (or pass angle as function of time)
    angle = 90.0 - (t - 12.0) * 15.0  # Approximate solar angle at time t
    view_factor = calculate_view_factor(geometry, angle)
    G_eff = irradiance * view_factor * geometry.transmissivity_absorptivity_product
    
    # Material properties
    props_glass = materials['glass']
    props_plate = materials['plate']
    props_water = materials['water']
    props_insulation = materials['insulation']
    
    # Mass and heat capacities
    m_glass = props_glass['density'] * props_glass['volume']
    m_plate = props_plate['density'] * props_plate['volume']
    m_water = props_water['density'] * props_water['volume']
    m_base = props_insulation['density'] * props_insulation['volume']
    
    c_glass = props_glass['specific_heat']
    c_plate = props_plate['specific_heat']
    c_water = props_water['specific_heat']
    c_base = props_insulation['specific_heat']
    
    # Heat capacities
    C_glass = m_glass * c_glass
    C_plate = m_plate * c_plate
    C_water = m_water * c_water
    C_base = m_base * c_base
    
    # Heat transfer coefficients
    h_glass_amb = calculate_convective_coeff(T_glass - T_ambient, geometry)
    h_plate_glass = calculate_convective_coeff(T_plate - T_glass, geometry)
    h_plate_water = calculate_convective_coeff(T_plate - T_water, geometry)
    h_water_base = calculate_convective_coeff(T_water - T_base, geometry)
    
    # Radiative heat transfer (simplified linearized)
    eps_glass = props_glass['emissivity']
    eps_plate = props_plate['emissivity']
    
    # Net radiative exchange (simplified)
    Q_rad_glass = eps_glass * sigma * (T_glass**4 - T_ambient**4)
    Q_rad_plate = eps_plate * sigma * (T_plate**4 - T_glass**4)
    
    # Energy balances
    # Glass cover: Receives solar (transmitted), loses to ambient, gains from plate
    Q_solar_glass = 0.0  # Most solar passes through to plate
    dT_glass_dt = (
        Q_rad_plate - Q_rad_glass - h_glass_amb * (T_glass - T_ambient) -
        h_plate_glass * (T_glass - T_plate)
    ) / C_glass
    
    # Absorber plate: Receives solar, loses to glass and water
    Q_solar_plate = G_eff * geometry.surface_area
    dT_plate_dt = (
        Q_solar_plate - Q_rad_plate - h_plate_glass * (T_plate - T_glass) -
        h_plate_water * (T_plate - T_water)
    ) / C_plate
    
    # Water bulk: Receives from plate, loses to base
    dT_water_dt = (
        h_plate_water * (T_plate - T_water) - h_water_base * (T_water - T_base)
    ) / C_water
    
    # Base/Insulation: Receives from water, loses to ambient (through insulation)
    # Simplified: assume base is large thermal mass at near ambient
    dT_base_dt = (
        h_water_base * (T_water - T_base) - h_glass_amb * (T_base - T_ambient)
    ) / C_base
    
    return np.array([dT_glass_dt, dT_plate_dt, dT_water_dt, dT_base_dt])

def run_simulation(
    geometry: GeometryConfig,
    materials: Dict[str, Dict[str, Any]],
    time_span: Tuple[float, float] = (6.0, 18.0),
    T_ambient: float = 293.15,
    initial_state: Optional[ThermalState] = None
) -> Dict[str, Any]:
    """
    Run the 1D transient heat transfer simulation.
    
    Args:
        geometry: Geometry configuration
        materials: Dictionary of material properties
        time_span: (start_hour, end_hour)
        T_ambient: Ambient temperature in Kelvin
        initial_state: Initial temperatures (optional, defaults to ambient)
        
    Returns:
        Dictionary containing simulation results:
        - t: time points
        - y: state trajectories
        - success: boolean indicating if integration succeeded
        - message: status message
    """
    if initial_state is None:
        initial_state = ThermalState(
            T_glass=T_ambient,
            T_plate=T_ambient,
            T_water=T_ambient,
            T_base=T_ambient
        )
    
    y0 = np.array([
        initial_state.T_glass,
        initial_state.T_plate,
        initial_state.T_water,
        initial_state.T_base
    ])
    
    # Create irradiance profile function
    time_points = np.linspace(time_span[0], time_span[1], 100)
    irradiance_profile = get_solar_irradiance_profile(time_points)
    
    def irradiance_func(t):
        # Interpolate irradiance for any time t
        if t < time_span[0] or t > time_span[1]:
            return 0.0
        return np.interp(t, time_points, irradiance_profile)
    
    params = {
        'irradiance': irradiance_func,
        'T_ambient': T_ambient,
        'geometry': geometry,
        'materials': materials
    }
    
    # Solve ODE system
    try:
        sol = solve_ivp(
            thermal_ode_system,
            time_span,
            y0,
            args=(params,),
            method='RK45',
            dense_output=True,
            rtol=1e-6,
            atol=1e-9,
            max_step=60.0/3600.0  # Max 1 minute step
        )
        
        return {
            't': sol.t,
            'y': sol.y,
            'success': sol.success,
            'message': 'Simulation completed successfully' if sol.success else sol.message,
            'solution': sol
        }
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        return {
            't': np.array([]),
            'y': np.array([]),
            'success': False,
            'message': str(e),
            'solution': None
        }

def main():
    """
    Main entry point for running a sample simulation.
    """
    logger.info("Starting 1D transient heat transfer simulation...")
    
    # Load geometry and materials (simplified for demo)
    geometry = GeometryConfig(
        geometry_id="single_slope",
        inclination_angle=45.0,
        surface_area=1.0,
        transmissivity_absorptivity_product=0.85
    )
    
    # Define material properties (simplified)
    materials = {
        'glass': {
            'density': 2500.0,
            'specific_heat': 840.0,
            'emissivity': 0.9,
            'volume': 0.001  # m^3
        },
        'plate': {
            'density': 2700.0,
            'specific_heat': 900.0,
            'emissivity': 0.95,
            'volume': 0.0005
        },
        'water': {
            'density': 1000.0,
            'specific_heat': 4186.0,
            'emissivity': 0.96,
            'volume': 0.05
        },
        'insulation': {
            'density': 50.0,
            'specific_heat': 1200.0,
            'emissivity': 0.9,
            'volume': 0.01
        }
    }
    
    # Run simulation
    result = run_simulation(geometry, materials)
    
    if result['success']:
        logger.info(f"Simulation successful. Final T_water: {result['y'][2, -1]:.2f} K")
    else:
        logger.error(f"Simulation failed: {result['message']}")
    
    return result

if __name__ == "__main__":
    main()