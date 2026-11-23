import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, Any, List, Tuple, Optional
import logging
from dataclasses import dataclass, field
import os
import json
from pathlib import Path

from utils import get_project_root, get_data_dir, ensure_dir, setup_logging
from config import get_config
from data_ingestion import MaterialProfile, GeometryConfig, load_nist_materials

# Setup logger
logger = setup_logging(__name__)

@dataclass
class ThermalState:
    """
    State vector for the 1D transient heat transfer simulation.
    Contains temperature distribution across the material thickness.
    """
    temperatures: np.ndarray
    time: float = 0.0

def get_solar_irradiance_profile(duration_hours: float = 12, dt: float = 60) -> Tuple[np.ndarray, np.ndarray]:
    """
    Fetches or generates a representative solar irradiance profile for Sub-Saharan Africa.
    Uses the data fetched in T008 if available, otherwise generates a realistic diurnal curve.
    
    Args:
        duration_hours: Duration of simulation in hours.
        dt: Time step in seconds.
        
    Returns:
        Tuple of (time_array_seconds, irradiance_array_W_m2)
    """
    # Try to load from T008 output first
    irradiance_path = get_data_dir() / "raw" / "solar_irradiance.csv"
    
    if irradiance_path.exists():
        try:
            logger.info(f"Loading solar irradiance from {irradiance_path}")
            # Simple CSV parsing assuming columns: time, irradiance
            times = []
            irradiances = []
            with open(irradiance_path, 'r') as f:
                next(f) # Skip header
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        times.append(float(parts[0]))
                        irradiances.append(float(parts[1]))
            
            if len(times) > 0:
                return np.array(times), np.array(irradiances)
        except Exception as e:
            logger.warning(f"Failed to load solar irradiance from file: {e}. Generating synthetic profile.")
    
    # Fallback: Generate a realistic diurnal curve (sinusoidal approximation)
    # This represents a typical clear day in Sub-Saharan Africa
    total_seconds = int(duration_hours * 3600)
    time_array = np.linspace(0, total_seconds, int(total_seconds / dt))
    
    # Solar noon at t = duration/2
    peak_irradiance = 1000.0 # W/m^2
    sunrise_offset = duration_hours * 3600 / 4 # Sunrise at 1/4 of duration
    sunset_offset = duration_hours * 3600 * 3 / 4 # Sunset at 3/4 of duration
    
    irradiance_array = np.zeros_like(time_array)
    for i, t in enumerate(time_array):
        if sunrise_offset <= t <= sunset_offset:
            # Simple cosine approximation for diurnal cycle
            normalized_time = (t - sunrise_offset) / (sunset_offset - sunrise_offset)
            irradiance_array[i] = peak_irradiance * np.sin(np.pi * normalized_time)
        else:
            irradiance_array[i] = 0.0
            
    return time_array, irradiance_array

def calculate_view_factor(geometry: GeometryConfig, angle: float = 0.0) -> float:
    """
    Calculates the view factor for a specific geometry and solar incidence angle.
    This accounts for the effective projected area receiving solar radiation.
    
    Args:
        geometry: Geometry configuration object.
        angle: Solar incidence angle in degrees.
        
    Returns:
        View factor between 0 and 1.
    """
    # Convert angle to radians
    theta = np.radians(angle)
    
    # Base view factor depends on geometry type
    if geometry.geometry_type == "flat_plate":
        # Flat plate: view factor is cos(theta) for direct radiation
        view_factor = max(0.0, np.cos(theta))
    elif geometry.geometry_type == "single_slope":
        # Single slope: more complex, but simplified here
        # Assume optimal angle is 30 degrees
        optimal_angle = np.radians(30)
        view_factor = max(0.0, np.cos(theta - optimal_angle))
    elif geometry.geometry_type == "double_slope":
        # Double slope: V-shaped, captures radiation from both sides
        # Simplified model
        view_factor = max(0.0, np.cos(theta)) + max(0.0, np.cos(theta + np.radians(60)))
        view_factor = min(1.0, view_factor / 2.0) # Normalize
    else:
        view_factor = 0.0
        
    return view_factor

def calculate_convective_coeff(temp_diff: float, geometry: GeometryConfig) -> float:
    """
    Calculates the convective heat transfer coefficient based on temperature difference.
    Uses a simplified correlation for natural convection.
    
    Args:
        temp_diff: Temperature difference between surface and ambient (K).
        geometry: Geometry configuration object.
        
    Returns:
        Convective heat transfer coefficient (W/m^2/K).
    """
    # Simplified natural convection correlation
    # h = C * (DeltaT)^n, where C and n are constants
    if temp_diff <= 0:
        temp_diff = 0.1 # Avoid zero or negative values
        
    # Typical values for natural convection in air
    C = 1.42
    n = 0.25
    
    h = C * (temp_diff ** n)
    
    # Adjust based on geometry orientation
    if geometry.geometry_type == "flat_plate":
        h *= 1.0
    elif geometry.geometry_type == "single_slope":
        h *= 1.1 # Slightly enhanced convection due to slope
    elif geometry.geometry_type == "double_slope":
        h *= 1.2 # Enhanced convection in V-shape
        
    return h

def thermal_ode_system(t: float, y: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
    """
    Defines the 1D transient heat transfer ODE system.
    
    Args:
        t: Current time (seconds).
        y: Current state vector (temperatures at discrete points).
        params: Dictionary containing simulation parameters.
        
    Returns:
        Derivative of the state vector (dY/dt).
    """
    # Extract parameters
    num_nodes = len(y)
    dx = params['dx']
    k = params['thermal_conductivity']
    rho = params['density']
    cp = params['specific_heat']
    emissivity = params['emissivity']
    h_conv = params['convective_coeff']
    T_ambient = params['T_ambient']
    G_solar = params['G_solar']
    alpha = params['absorptivity']
    view_factor = params['view_factor']
    sigma = params['sigma']
    
    # Initialize derivative array
    dydt = np.zeros_like(y)
    
    # Thermal diffusivity
    alpha_thermal = k / (rho * cp)
    
    # Interior nodes (1 to num_nodes-2)
    for i in range(1, num_nodes - 1):
        # 1D heat equation: dT/dt = alpha * d^2T/dx^2
        dydt[i] = alpha_thermal * (y[i+1] - 2*y[i] + y[i-1]) / (dx ** 2)
        
    # Boundary conditions
    # Left boundary (i=0): Solar radiation + convection + radiation
    if num_nodes > 1:
        # Solar flux absorbed
        q_solar = alpha * G_solar * view_factor
        
        # Convective loss
        q_conv = h_conv * (y[0] - T_ambient)
        
        # Radiative loss (Stefan-Boltzmann)
        q_rad = emissivity * sigma * (y[0]**4 - T_ambient**4)
        
        # Net flux at boundary
        q_net = q_solar - q_conv - q_rad
        
        # Finite difference approximation for boundary
        dydt[0] = (2 * alpha_thermal / dx) * ( (y[1] - y[0]) / dx ) + (2 * q_net) / (rho * cp * dx)
        
    # Right boundary (i=num_nodes-1): Insulated or convective
    if num_nodes > 1:
        # Assume insulated back side (no heat flux)
        dydt[-1] = (2 * alpha_thermal / dx) * ( (y[-1] - y[-2]) / dx )
        
    return dydt

def run_simulation(
    material: MaterialProfile,
    geometry: GeometryConfig,
    irradiance_profile: Tuple[np.ndarray, np.ndarray],
    duration_hours: float = 12,
    num_nodes: int = 20,
    T_initial: float = 300.0
) -> Dict[str, Any]:
    """
    Runs the 1D transient heat transfer simulation for a given material and geometry.
    
    Args:
        material: Material profile containing thermal properties.
        geometry: Geometry configuration.
        irradiance_profile: Tuple of (time_array, irradiance_array).
        duration_hours: Simulation duration in hours.
        num_nodes: Number of spatial nodes for discretization.
        T_initial: Initial temperature (K).
        
    Returns:
        Dictionary containing simulation results:
        - 'time': Time array (seconds)
        - 'temperatures': Temperature history (2D array: time x nodes)
        - 'final_efficiency': Calculated thermal efficiency
        - 'convergence_status': Boolean indicating successful convergence
    """
    logger.info(f"Running simulation for {material.material_id} - {geometry.geometry_id}")
    
    # Extract material properties
    k = material.thermal_conductivity
    rho = material.density
    cp = material.specific_heat
    emissivity = material.emissivity
    
    # Geometry parameters
    thickness = geometry.thickness
    area = geometry.surface_area
    
    # Time discretization
    total_seconds = duration_hours * 3600
    time_points = irradiance_profile[0]
    irradiance_values = irradiance_profile[1]
    
    # Spatial discretization
    dx = thickness / (num_nodes - 1)
    
    # Initial state
    y0 = np.full(num_nodes, T_initial)
    
    # Constants
    sigma = 5.67e-8 # Stefan-Boltzmann constant
    T_ambient = 300.0 # Ambient temperature (K)
    alpha = 0.9 # Absorptivity (assumed)
    
    # Storage for results
    all_temperatures = []
    time_history = []
    
    # Run simulation in time steps
    dt = time_points[1] - time_points[0] if len(time_points) > 1 else 60.0
    
    for i, t in enumerate(time_points):
        # Get current solar irradiance
        G_solar = irradiance_values[i]
        
        # Calculate view factor (simplified, assumes fixed angle for now)
        view_factor = calculate_view_factor(geometry, 0.0)
        
        # Calculate convective coefficient (using average temp difference)
        avg_temp = np.mean(y0)
        h_conv = calculate_convective_coeff(avg_temp - T_ambient, geometry)
        
        # Parameters for ODE system
        params = {
            'dx': dx,
            'thermal_conductivity': k,
            'density': rho,
            'specific_heat': cp,
            'emissivity': emissivity,
            'convective_coeff': h_conv,
            'T_ambient': T_ambient,
            'G_solar': G_solar,
            'absorptivity': alpha,
            'view_factor': view_factor,
            'sigma': sigma
        }
        
        # Solve ODE for this time step
        try:
            sol = solve_ivp(
                thermal_ode_system,
                [t, t + dt],
                y0,
                args=(params,),
                method='RK45',
                max_step=dt
            )
            
            if sol.success:
                y0 = sol.y[:, -1]
                all_temperatures.append(y0.copy())
                time_history.append(t + dt)
            else:
                logger.warning(f"ODE solver failed at t={t}: {sol.message}")
                return {
                    'time': np.array(time_history),
                    'temperatures': np.array(all_temperatures) if all_temperatures else np.array([]),
                    'final_efficiency': 0.0,
                    'convergence_status': False,
                    'error': sol.message
                }
                
        except Exception as e:
            logger.error(f"Exception during ODE solve at t={t}: {e}")
            return {
                'time': np.array(time_history),
                'temperatures': np.array(all_temperatures) if all_temperatures else np.array([]),
                'final_efficiency': 0.0,
                'convergence_status': False,
                'error': str(e)
            }
    
    if not all_temperatures:
        return {
            'time': np.array([]),
            'temperatures': np.array([]),
            'final_efficiency': 0.0,
            'convergence_status': False,
            'error': "No time steps completed"
        }
    
    temperatures = np.array(all_temperatures)
    time_history = np.array(time_history)
    
    # Calculate time-averaged thermal efficiency over the final 30 minutes
    final_30_min_mask = time_history >= (total_seconds - 30 * 60)
    if np.any(final_30_min_mask):
        final_temps = temperatures[final_30_min_mask]
        avg_temp_final = np.mean(final_temps)
        
        # Calculate efficiency: useful energy / solar energy input
        # Useful energy: heat gained by the material
        # Simplified: based on average temperature rise
        delta_T = avg_temp_final - T_initial
        useful_energy = rho * cp * thickness * delta_T # Per unit area
        
        # Total solar energy input over final 30 minutes
        final_irradiance = irradiance_values[final_30_min_mask]
        total_solar_input = np.sum(final_irradiance) * (30 * 60 / len(final_irradiance)) # Approximate
        
        if total_solar_input > 0:
            efficiency = useful_energy / total_solar_input
            # Clamp efficiency to reasonable range [0, 1]
            efficiency = max(0.0, min(1.0, efficiency))
        else:
            efficiency = 0.0
    else:
        efficiency = 0.0
        
    return {
        'time': time_history,
        'temperatures': temperatures,
        'final_efficiency': efficiency,
        'convergence_status': True,
        'avg_final_temp': np.mean(temperatures[-1])
    }

def calculate_time_averaged_efficiency(
    simulation_results: List[Dict[str, Any]],
    irradiance_profile: Tuple[np.ndarray, np.ndarray],
    duration_hours: float = 12
) -> List[Dict[str, float]]:
    """
    Calculates the time-averaged thermal efficiency over the final 30 minutes
    for every valid material-geometry combination.
    
    Args:
        simulation_results: List of simulation result dictionaries.
        irradiance_profile: Tuple of (time_array, irradiance_array).
        duration_hours: Simulation duration in hours.
        
    Returns:
        List of dictionaries containing material_id, geometry_id, and time_averaged_efficiency.
    """
    logger.info("Calculating time-averaged thermal efficiency for final 30 minutes")
    
    total_seconds = duration_hours * 3600
    final_30_min_start = total_seconds - 30 * 60
    
    results = []
    
    for res in simulation_results:
        if not res.get('convergence_status', False):
            logger.warning(f"Skipping invalid simulation result: {res.get('material_id', 'unknown')}")
            continue
            
        time_array = res.get('time', np.array([]))
        temp_array = res.get('temperatures', np.array([]))
        
        if len(time_array) == 0 or len(temp_array) == 0:
            logger.warning(f"Empty simulation result for {res.get('material_id', 'unknown')}")
            continue
        
        # Filter for final 30 minutes
        final_mask = time_array >= final_30_min_start
        if not np.any(final_mask):
            logger.warning(f"No data in final 30 minutes for {res.get('material_id', 'unknown')}")
            continue
        
        final_times = time_array[final_mask]
        final_temps = temp_array[final_mask]
        
        # Calculate average temperature in final period
        avg_temp = np.mean(final_temps)
        
        # Get ambient temperature (assumed 300K)
        T_ambient = 300.0
        
        # Calculate efficiency based on temperature rise
        # This is a simplified model; in reality, efficiency would be calculated
        # based on the actual heat transfer to water or useful output
        delta_T = avg_temp - T_ambient
        
        # Get average solar irradiance in final period
        irradiance_times = irradiance_profile[0]
        irradiance_values = irradiance_profile[1]
        
        # Interpolate irradiance to match simulation times
        final_irradiance = np.interp(final_times, irradiance_times, irradiance_values)
        avg_irradiance = np.mean(final_irradiance)
        
        if avg_irradiance > 0:
            # Simplified efficiency calculation
            # Efficiency = (Useful Heat) / (Solar Input)
            # Useful Heat ~ delta_T * constant (material properties)
            # For simplicity, we use a normalized efficiency based on delta_T
            max_possible_delta_T = 100.0 # Assumed max temperature rise
            efficiency = min(1.0, max(0.0, delta_T / max_possible_delta_T))
        else:
            efficiency = 0.0
        
        results.append({
            'material_id': res.get('material_id', 'unknown'),
            'geometry_id': res.get('geometry_id', 'unknown'),
            'time_averaged_efficiency': float(efficiency),
            'avg_final_temp': float(avg_temp),
            'convergence_status': True
        })
        
        logger.info(f"Calculated efficiency {efficiency:.4f} for {res.get('material_id', 'unknown')} - {res.get('geometry_id', 'unknown')}")
        
    return results

def main():
    """
    Main function to run simulations for all valid material-geometry combinations
    and calculate time-averaged thermal efficiency.
    """
    logger.info("Starting T022: Time-averaged thermal efficiency calculation")
    
    # Load materials
    materials = load_nist_materials()
    valid_materials = [m for m in materials if m.status == 'valid']
    
    if not valid_materials:
        logger.error("No valid materials found. Cannot proceed with simulation.")
        return
    
    # Define geometries
    geometries = [
        GeometryConfig(geometry_id="flat_plate", geometry_type="flat_plate", thickness=0.002, surface_area=1.0, inclination_angle=30),
        GeometryConfig(geometry_id="single_slope", geometry_type="single_slope", thickness=0.002, surface_area=1.0, inclination_angle=30),
        GeometryConfig(geometry_id="double_slope", geometry_type="double_slope", thickness=0.002, surface_area=1.0, inclination_angle=30)
    ]
    
    # Get solar irradiance profile
    irradiance_profile = get_solar_irradiance_profile()
    
    # Run simulations for all combinations
    all_results = []
    
    for material in valid_materials:
        for geometry in geometries:
            result = run_simulation(
                material=material,
                geometry=geometry,
                irradiance_profile=irradiance_profile,
                duration_hours=12,
                num_nodes=20,
                T_initial=300.0
            )
            
            if result.get('convergence_status', False):
                result['material_id'] = material.material_id
                result['geometry_id'] = geometry.geometry_id
                all_results.append(result)
            else:
                logger.warning(f"Simulation failed for {material.material_id} - {geometry.geometry_id}")
    
    # Calculate time-averaged efficiency
    efficiency_results = calculate_time_averaged_efficiency(
        all_results,
        irradiance_profile,
        duration_hours=12
    )
    
    # Save results to CSV
    output_path = get_data_dir() / "processed" / "simulation_efficiency.csv"
    ensure_dir(output_path.parent)
    
    import csv
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['material_id', 'geometry_id', 'time_averaged_efficiency', 'avg_final_temp', 'convergence_status'])
        writer.writeheader()
        writer.writerows(efficiency_results)
    
    logger.info(f"Saved efficiency results to {output_path}")
    logger.info(f"Total combinations simulated: {len(efficiency_results)}")
    
    return efficiency_results

if __name__ == "__main__":
    main()