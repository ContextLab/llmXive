from __future__ import annotations

import hashlib
import json
import logging
import multiprocessing
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, Generator

import numpy as np

from .exceptions import SimulationError
from .regularization import is_condition_number_acceptable, regularize_covariance

logger = logging.getLogger(__name__)

# Type alias for distribution types supported in simulation
DistributionType = Literal["normal", "t", "skew_normal"]

@dataclass
class SimulationConfig:
    """Configuration for a single simulation run."""
    n: int  # Sample size
    p: int  # Number of dimensions
    rho: float  # Correlation threshold
    distribution_type: DistributionType
    seed: int
    degrees_of_freedom: Optional[float] = None  # For t-distribution
    skewness_param: Optional[float] = None  # For skew-normal

    def __post_init__(self):
        if self.distribution_type == "t" and self.degrees_of_freedom is None:
            self.degrees_of_freedom = 3.0
        if self.distribution_type == "skew_normal" and self.skewness_param is None:
            self.skewness_param = 5.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "p": self.p,
            "rho": self.rho,
            "distribution_type": self.distribution_type,
            "seed": self.seed,
            "degrees_of_freedom": self.degrees_of_freedom,
            "skewness_param": self.skewness_param,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SimulationConfig:
        return cls(
            n=data["n"],
            p=data["p"],
            rho=data["rho"],
            distribution_type=data["distribution_type"],
            seed=data["seed"],
            degrees_of_freedom=data.get("degrees_of_freedom"),
            skewness_param=data.get("skewness_param"),
        )

@dataclass
class SyntheticDataset:
    """
    Represents a single generated dataset with metadata.
    Implements the data model and schema for synthetic data.
    """
    data: np.ndarray
    config: SimulationConfig
    sha256: str = field(init=False)
    created_at: str = field(init=False)
    condition_number: Optional[float] = field(default=None, init=False)
    is_regularized: bool = field(default=False, init=False)

    def __post_init__(self):
        # Compute hash of the flattened data for integrity checking
        flat_data = self.data.tobytes()
        self.sha256 = hashlib.sha256(flat_data).hexdigest()
        self.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Compute condition number if data is 2D
        if self.data.ndim == 2 and self.data.shape[1] > 1:
            try:
                cov = np.cov(self.data, rowvar=False)
                if cov.size > 0:
                    eigenvalues = np.linalg.eigvalsh(cov)
                    if np.min(eigenvalues) > 0:
                        self.condition_number = np.max(eigenvalues) / np.min(eigenvalues)
                    else:
                        self.condition_number = np.inf
                else:
                    self.condition_number = np.nan
            except Exception:
                self.condition_number = np.nan

    def validate(self) -> bool:
        """Validate the dataset against schema constraints."""
        if self.data.ndim != 2:
            raise SimulationError(f"Data must be 2D, got {self.data.ndim}D")
        if self.data.shape[0] != self.config.n:
            raise SimulationError(f"Data rows {self.data.shape[0]} != config n {self.config.n}")
        if self.data.shape[1] != self.config.p:
            raise SimulationError(f"Data cols {self.data.shape[1]} != config p {self.config.p}")
        if not np.isfinite(self.data).all():
            raise SimulationError("Data contains non-finite values")
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sha256": self.sha256,
            "n": self.config.n,
            "p": self.config.p,
            "rho": self.config.rho,
            "distribution_type": self.config.distribution_type,
            "seed": self.config.seed,
            "condition_number": self.condition_number,
            "is_regularized": self.is_regularized,
            "created_at": self.created_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> SyntheticDataset:
        data = json.loads(json_str)
        # Note: This is a partial reconstruction; actual data loading requires the binary file
        return cls(
            data=np.array([]), # Placeholder for reconstruction logic
            config=SimulationConfig.from_dict({
                "n": data["n"],
                "p": data["p"],
                "rho": data["rho"],
                "distribution_type": data["distribution_type"],
                "seed": data["seed"],
            })
        )

class SimulationOrchestrator:
    """
    Manages simulation iterations, seeds, and parameter sweeps.
    Coordinates the generation of datasets across a grid of parameters.
    """

    def __init__(
        self,
        n_range: List[int],
        p_levels: List[int],
        rho_values: List[float],
        distribution_types: List[DistributionType],
        base_seed: int = 42,
        max_iterations: Optional[int] = None,
        output_dir: Optional[Path] = None,
        verbose: bool = True
    ):
        self.n_range = n_range
        self.p_levels = p_levels
        self.rho_values = rho_values
        self.distribution_types = distribution_types
        self.base_seed = base_seed
        self.max_iterations = max_iterations
        self.output_dir = output_dir or Path("data/synthetic")
        self.verbose = verbose

        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self._config_grid: List[SimulationConfig] = []
        self._results: List[Dict[str, Any]] = []
        self._current_seed = base_seed

    def _generate_seed(self) -> int:
        """Generate a unique seed for the next iteration."""
        self._current_seed += 1
        return self._current_seed

    def build_config_grid(self) -> List[SimulationConfig]:
        """
        Build the full Cartesian product of parameters.
        Returns a list of SimulationConfig objects.
        """
        configs = []
        for n in self.n_range:
            for p in self.p_levels:
                for rho in self.rho_values:
                    for dist_type in self.distribution_types:
                        seed = self._generate_seed()
                        config = SimulationConfig(
                            n=n,
                            p=p,
                            rho=rho,
                            distribution_type=dist_type,
                            seed=seed,
                        )
                        configs.append(config)

        self._config_grid = configs
        if self.verbose:
            logger.info(f"Built config grid with {len(configs)} configurations.")
        return configs

    def iterate_configs(self) -> Generator[SimulationConfig, None, None]:
        """
        Generator that yields configurations one by one.
        Useful for streaming large sweeps without loading all into memory.
        """
        if not self._config_grid:
            self.build_config_grid()

        count = 0
        for config in self._config_grid:
            if self.max_iterations and count >= self.max_iterations:
                break
            yield config
            count += 1

    def run_simulation_step(self, config: SimulationConfig) -> Tuple[Optional[SyntheticDataset], Optional[Dict[str, Any]]]:
        """
        Executes a single simulation step for a given configuration.
        This method delegates to the actual data generation logic (imported from generate_data).
        Since generate_data is not fully imported here to avoid circular dependencies,
        we assume the generation function is available or we mock the structure for the orchestrator logic.
        
        In a real execution flow, this would call:
        from code.generate_data import generate_correlated_data
        dataset = generate_correlated_data(config)
        
        For this implementation, we raise a NotImplementedError to indicate
        that the actual generation logic must be wired in, but the orchestration
        structure (loops, seeds, config management) is fully functional.
        """
        try:
            # Attempt to import the generation function dynamically
            # This avoids hard dependency on generate_data.py at import time of simulation.py
            import importlib
            generate_module = importlib.import_module("code.generate_data")
            generator_func = getattr(generate_module, "generate_correlated_data", None)
            
            if not generator_func:
                raise SimulationError("generate_correlated_data not found in code.generate_data")
            
            # Execute generation
            dataset = generator_func(config)
            
            # Validate
            dataset.validate()
            
            # Check condition number if necessary
            if dataset.condition_number and dataset.condition_number > 1e12:
                logger.warning(f"High condition number detected: {dataset.condition_number} for seed {config.seed}")
                # Optionally regularize here if required by spec
                # dataset = regularize_dataset(dataset) 
            
            # Save metadata
            metadata = {
                "config": config.to_dict(),
                "dataset_info": dataset.to_dict(),
                "status": "success"
            }
            
            # Save to disk if output_dir is set
            if self.output_dir:
                meta_path = self.output_dir / f"{config.seed}.json"
                with open(meta_path, "w") as f:
                    f.write(json.dumps(metadata, indent=2))
            
            return dataset, metadata

        except Exception as e:
            logger.error(f"Simulation failed for seed {config.seed}: {e}")
            return None, {"status": "failed", "error": str(e)}

    def run_full_sweep(self) -> List[Dict[str, Any]]:
        """
        Runs the full parameter sweep.
        Returns a list of result dictionaries.
        """
        if not self._config_grid:
            self.build_config_grid()

        results = []
        total = len(self._config_grid)
        
        if self.verbose:
            logger.info(f"Starting full sweep of {total} configurations.")

        for i, config in enumerate(self.iterate_configs()):
            if self.verbose:
                logger.info(f"Running {i+1}/{total}: n={config.n}, p={config.p}, rho={config.rho}, dist={config.distribution_type}")
            
            dataset, metadata = self.run_simulation_step(config)
            results.append(metadata)
            
            if self.verbose and (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{total}")

        self._results = results
        return results

    def get_results(self) -> List[Dict[str, Any]]:
        """Returns the list of results from the last run."""
        return self._results

def main():
    """Entry point for running the simulation orchestrator directly."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Define parameters
    n_range = [100, 500]
    p_levels = [50, 200]
    rho_values = [0.0, 0.5]
    dist_types: List[DistributionType] = ["normal", "t"]
    
    orchestrator = SimulationOrchestrator(
        n_range=n_range,
        p_levels=p_levels,
        rho_values=rho_values,
        distribution_types=dist_types,
        base_seed=12345,
        max_iterations=4, # Limit for testing
        verbose=True
    )
    
    results = orchestrator.run_full_sweep()
    print(f"Completed {len(results)} simulations.")
    for r in results:
        print(r)

if __name__ == "__main__":
    main()