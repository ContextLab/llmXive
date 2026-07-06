"""
Configuration schema for the simulation engine.

Defines the `SimulationConfig` dataclass used to parameterize
synthetic dataset generation, including sample size, predictors,
correlation structure, noise levels, and true coefficients.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Union
import numpy as np
from numpy.typing import ArrayLike


@dataclass
class SimulationConfig:
    """
    Configuration for generating a synthetic regression dataset.

    Attributes:
        N (int): Sample size (number of observations).
        n_predictors (int): Number of predictor variables (features).
        true_coefficients (ArrayLike): True regression coefficients (beta).
            Length must match n_predictors + 1 (if intercept is included)
            or n_predictors (if no intercept). Defaults to zeros.
        rho (float): Target correlation coefficient between adjacent predictors
            in an autoregressive structure (AR(1)). Range: (-1, 1).
            If None, predictors are independent.
        noise_std (float): Standard deviation of the Gaussian noise term (sigma).
        seed (Optional[int]): Random seed for reproducibility.
        intercept (bool): Whether to include an intercept term in the design matrix.
    """
    N: int
    n_predictors: int
    true_coefficients: Optional[ArrayLike] = None
    rho: Optional[float] = None
    noise_std: float = 1.0
    seed: Optional[int] = None
    intercept: bool = True

    def __post_init__(self):
        """Validate and initialize configuration parameters."""
        if self.N <= 0:
            raise ValueError(f"Sample size N must be positive, got {self.N}")
        
        if self.n_predictors <= 0:
            raise ValueError(f"Number of predictors must be positive, got {self.n_predictors}")
        
        if self.rho is not None:
            if not (-1 < self.rho < 1):
                raise ValueError(f"Correlation rho must be in (-1, 1), got {self.rho}")
        
        if self.noise_std < 0:
            raise ValueError(f"Noise standard deviation must be non-negative, got {self.noise_std}")

        # Initialize coefficients if not provided
        if self.true_coefficients is None:
            # Default to small random coefficients if not specified
            # This ensures a non-trivial signal
            if self.seed is not None:
                rng = np.random.default_rng(self.seed)
            else:
                rng = np.random.default_rng()
            
            # Generate coefficients for predictors
            coeffs = rng.normal(loc=0.0, scale=0.5, size=self.n_predictors)
            
            # If intercept is requested, add a coefficient for the intercept term
            # Convention: The first element of true_coefficients is the intercept
            if self.intercept:
                # Add an intercept coefficient (e.g., mean of y)
                intercept_val = rng.normal(loc=10.0, scale=2.0)
                coeffs = np.concatenate([[intercept_val], coeffs])
            
            self.true_coefficients = coeffs
        else:
            # Convert to numpy array if it isn't already
            self.true_coefficients = np.asarray(self.true_coefficients, dtype=float)
            
            # Validate length if intercept is handled explicitly
            expected_len = self.n_predictors + 1 if self.intercept else self.n_predictors
            if len(self.true_coefficients) != expected_len:
                raise ValueError(
                    f"true_coefficients length ({len(self.true_coefficients)}) "
                    f"does not match expected length ({expected_len}) "
                    f"based on n_predictors={self.n_predictors} and intercept={self.intercept}"
                )

    def to_dict(self) -> dict:
        """
        Convert the configuration to a dictionary for serialization.
        
        Returns:
            dict: Dictionary representation of the config.
        """
        return {
            "N": self.N,
            "n_predictors": self.n_predictors,
            "true_coefficients": self.true_coefficients.tolist() if self.true_coefficients is not None else None,
            "rho": self.rho,
            "noise_std": self.noise_std,
            "seed": self.seed,
            "intercept": self.intercept
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SimulationConfig":
        """
        Create a SimulationConfig instance from a dictionary.
        
        Args:
            data (dict): Dictionary containing configuration parameters.
        
        Returns:
            SimulationConfig: Instance constructed from the dictionary.
        """
        # Handle coefficient list from JSON
        coeffs = data.get("true_coefficients")
        if coeffs is not None:
            coeffs = np.array(coeffs)
        
        return cls(
            N=data["N"],
            n_predictors=data["n_predictors"],
            true_coefficients=coeffs,
            rho=data.get("rho"),
            noise_std=data.get("noise_std", 1.0),
            seed=data.get("seed"),
            intercept=data.get("intercept", True)
        )

    def __repr__(self) -> str:
        return (
            f"SimulationConfig(N={self.N}, n_predictors={self.n_predictors}, "
            f"rho={self.rho}, noise_std={self.noise_std}, seed={self.seed})"
        )