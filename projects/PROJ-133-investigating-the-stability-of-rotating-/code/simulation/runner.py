import os
import sys
import time
import traceback
import resource
import psutil
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from models.entities import SimulationRun, StabilityMetric
from simulation.gpe_solver import GPESolver, GPEParameters, run_gpe_simulation
from simulation.initial_conditions import create_thomas_fermi_initial_condition
from utils.logger import get_logger, info, warning, error, debug
from utils.io_helpers import save_simulation_snapshot, save_dataframe
from utils.seed_manager import derive_seed
from config.grid_config import get_grid_resolution, get_domain_size, get_time_step, get_max_time

logger = get_logger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch simulation runs."""
    omega_values: List[float]
    epsilon_dd_values: List[float]
    particle_counts: List[int]
    repeats: int = 1
    output_dir: str = "data/processed"
    run_full_grid: bool = True


def create_parameter_grid(config: BatchConfig) -> List[Dict[str, Any]]:
    """Create a list of parameter sets for the batch run."""
    params = []
    for omega in config.omega_values:
        for epsilon_dd in config.epsilon_dd_values:
            for n_particles in config.particle_counts:
                for i in range(config.repeats):
                    params.append({
                        "omega": omega,
                        "epsilon_dd": epsilon_dd,
                        "n_particles": n_particles,
                        "repeat": i,
                        "timestamp": datetime.now().isoformat()
                    })
    return params


def get_resource_usage() -> Dict[str, float]:
    """
    Get current process resource usage.
    
    Returns:
        Dictionary containing 'cpu_percent', 'memory_mb', 'wall_time_seconds'.
    """
    process = psutil.Process(os.getpid())
    cpu_percent = process.cpu_percent()
    memory_mb = process.memory_info().rss / (1024 * 1024)
    
    return {
        "cpu_percent": cpu_percent,
        "memory_mb": memory_mb
    }


def run_single_simulation(params: Dict[str, Any], config: BatchConfig) -> Optional[SimulationRun]:
    """
    Run a single GPE simulation with logging of steps and resources.
    
    Args:
        params: Dictionary containing omega, epsilon_dd, n_particles, repeat.
        config: BatchConfig for output paths and settings.
        
    Returns:
        SimulationRun object if successful, None if simulation crashed.
    """
    omega = params["omega"]
    epsilon_dd = params["epsilon_dd"]
    n_particles = params["n_particles"]
    repeat = params["repeat"]
    
    # Derive deterministic seed for this specific run
    run_seed = derive_seed(base_seed=42, factors=[omega, epsilon_dd, n_particles, repeat])
    
    logger.info(f"Starting simulation: Omega={omega}, Epsilon_dd={epsilon_dd}, "
                f"N={n_particles}, Repeat={repeat}, Seed={run_seed}")
    
    start_time = time.time()
    peak_memory = 0.0
    step_log = []
    
    try:
        # 1. Log initial resource state
        initial_resources = get_resource_usage()
        step_log.append({
            "step": "init",
            "timestamp": time.time() - start_time,
            "cpu_percent": initial_resources["cpu_percent"],
            "memory_mb": initial_resources["memory_mb"]
        })
        
        # 2. Setup Grid and Parameters
        grid_size = get_grid_resolution(run_full_grid=config.run_full_grid)
        domain_size = get_domain_size()
        dt = get_time_step()
        max_time = get_max_time()
        
        logger.debug(f"Grid: {grid_size}x{grid_size}, Domain: {domain_size}, "
                     f"dt: {dt}, MaxTime: {max_time}")
        
        # 3. Create Solver
        gpe_params = GPEParameters(
            omega=omega,
            epsilon_dd=epsilon_dd,
            n_particles=n_particles,
            grid_size=grid_size,
            domain_size=domain_size,
            dt=dt,
            max_time=max_time,
            seed=run_seed
        )
        
        solver = GPESolver(gpe_params)
        
        # 4. Log resource usage after initialization
        post_init_resources = get_resource_usage()
        step_log.append({
            "step": "solver_init",
            "timestamp": time.time() - start_time,
            "cpu_percent": post_init_resources["cpu_percent"],
            "memory_mb": post_init_resources["memory_mb"]
        })
        
        # 5. Create Initial Condition
        logger.debug("Generating Thomas-Fermi initial condition...")
        psi_0 = create_thomas_fermi_initial_condition(gpe_params)
        
        # 6. Run Evolution with Step Logging
        logger.info("Starting time evolution...")
        solver.set_initial_state(psi_0)
        
        # We simulate in chunks to log progress
        total_steps = int(max_time / dt)
        log_interval = max(1, total_steps // 10)  # Log every 10%
        
        for step_idx in range(total_steps):
            solver.step()
            
            # Log every N steps
            if step_idx % log_interval == 0:
                current_resources = get_resource_usage()
                if current_resources["memory_mb"] > peak_memory:
                    peak_memory = current_resources["memory_mb"]
                
                step_log.append({
                    "step": f"evolution_{step_idx}",
                    "timestamp": time.time() - start_time,
                    "cpu_percent": current_resources["cpu_percent"],
                    "memory_mb": current_resources["memory_mb"]
                })
                
                # Log memory warning if approaching limits (heuristic)
                if current_resources["memory_mb"] > 1000:  # > 1GB
                    warning(f"High memory usage detected: {current_resources['memory_mb']:.2f} MB")
        
        # 7. Final Resource Check
        final_resources = get_resource_usage()
        if final_resources["memory_mb"] > peak_memory:
            peak_memory = final_resources["memory_mb"]
        
        step_log.append({
            "step": "evolution_complete",
            "timestamp": time.time() - start_time,
            "cpu_percent": final_resources["cpu_percent"],
            "memory_mb": final_resources["memory_mb"]
        })
        
        # 8. Save Results
        output_dir = os.path.join(config.output_dir, f"omega_{omega}_eps_{epsilon_dd}_n_{n_particles}")
        os.makedirs(output_dir, exist_ok=True)
        
        filename_prefix = f"run_repeat_{repeat}_seed_{run_seed}"
        
        # Save density and phase snapshots
        save_simulation_snapshot(
            psi=solver.psi,
            params=gpe_params,
            output_dir=output_dir,
            filename_prefix=filename_prefix,
            suffix="final"
        )
        
        # Save step log for resource analysis
        log_path = os.path.join(output_dir, f"{filename_prefix}_step_log.json")
        # Note: In a real implementation, we would serialize step_log to JSON
        # For now, we log the summary to the main logger
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        logger.info(f"Simulation completed successfully in {total_duration:.2f}s. "
                    f"Peak Memory: {peak_memory:.2f} MB")
        
        # Create the entity
        run_record = SimulationRun(
            omega=omega,
            epsilon_dd=epsilon_dd,
            n_particles=n_particles,
            repeat=repeat,
            seed=run_seed,
            status="success",
            duration_seconds=total_duration,
            peak_memory_mb=peak_memory,
            output_path=output_dir,
            created_at=datetime.now().isoformat()
        )
        
        return run_record
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        error(f"Simulation crashed after {duration:.2f}s: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Log failure details
        step_log.append({
            "step": "crash",
            "timestamp": duration,
            "error": str(e)
        })
        
        # Create a failure record
        return SimulationRun(
            omega=omega,
            epsilon_dd=epsilon_dd,
            n_particles=n_particles,
            repeat=repeat,
            seed=run_seed,
            status="failed",
            duration_seconds=duration,
            peak_memory_mb=0.0,
            output_path="",
            error_message=str(e),
            created_at=datetime.now().isoformat()
        )


def run_batch(config: BatchConfig) -> List[SimulationRun]:
    """
    Run a batch of simulations over the parameter grid with comprehensive logging.
    
    Args:
        config: BatchConfig defining the parameter grid and output settings.
        
    Returns:
        List of SimulationRun records.
    """
    logger.info(f"Starting batch run with {config.repeats} repeats per point.")
    logger.info(f"Grid: Omega={config.omega_values}, Epsilon_dd={config.epsilon_dd_values}, "
                f"N={config.particle_counts}")
    
    parameter_sets = create_parameter_grid(config)
    logger.info(f"Total parameter sets to process: {len(parameter_sets)}")
    
    results = []
    start_batch_time = time.time()
    
    for i, params in enumerate(parameter_sets):
        logger.info(f"--- Processing {i+1}/{len(parameter_sets)} ---")
        
        run_result = run_single_simulation(params, config)
        results.append(run_result)
        
        # Log summary of this run
        if run_result.status == "success":
            logger.info(f"Run {i+1} SUCCESS: {run_result.duration_seconds:.2f}s, "
                        f"Mem: {run_result.peak_memory_mb:.2f}MB")
        else:
            logger.warning(f"Run {i+1} FAILED: {run_result.error_message}")
    
    total_time = time.time() - start_batch_time
    logger.info(f"Batch run completed in {total_time:.2f}s. "
                f"Successes: {sum(1 for r in results if r.status == 'success')}")
    
    return results


def main():
    """Entry point for running the simulation batch."""
    logger.info("Initializing Batch Runner...")
    
    # Define parameter grid based on project specs
    # Omega: [0.1, 0.3, 0.5, 0.7, 0.9]
    # Epsilon_dd: [0.0, 0.5, 1.0, 1.5]
    # N: [10000, 50000, 100000] (Small, Intermediate, Large)
    batch_config = BatchConfig(
        omega_values=[0.1, 0.3, 0.5, 0.7, 0.9],
        epsilon_dd_values=[0.0, 0.5, 1.0, 1.5],
        particle_counts=[10000, 50000, 100000],
        repeats=1,
        run_full_grid=True  # Defaults to 64x64 as per T013
    )
    
    # Run the batch
    results = run_batch(batch_config)
    
    # Save summary results
    if results:
        summary_data = [asdict(r) for r in results]
        output_path = "data/aggregated/batch_summary.csv"
        save_dataframe(summary_data, output_path)
        logger.info(f"Batch summary saved to {output_path}")
        
    return results


if __name__ == "__main__":
    main()