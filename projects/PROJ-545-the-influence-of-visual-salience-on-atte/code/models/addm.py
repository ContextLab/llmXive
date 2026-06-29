"""
Implementation of the choice-only Attentional Drift Diffusion Model (aDDM).

This module implements the core logic of the aDDM adapted for choice-only data
(no Reaction Time data available). It simulates the evidence accumulation process
where visual salience modulates the drift rate based on the current fixation.

Key features:
- Choice-only variant: Fits to binary choices without RT constraints.
- Salience modulation: Drift rate is weighted by visual salience of options.
- Numerical stability: Uses float64 and bounded integration steps.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union
import numpy as np
from scipy.special import erf
from scipy.stats import norm

# Project root path resolution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logger import get_logger, log_error_to_file

logger = get_logger(__name__)

# Model Constants
DEFAULT_DT = 0.01  # Time step in seconds
DEFAULT_A = 1.0    # Decision threshold
DEFAULT_S = 1.0    # Noise scaling factor
DEFAULT_W = 0.9    # Salience weight parameter (0 to 1)
MAX_TIME = 10.0    # Maximum simulation time to prevent infinite loops


class aDDMChoiceOnly:
    """
    Attentional Drift Diffusion Model for Choice-Only Data.

    This model simulates the drift diffusion process where the drift rate at
    any time step depends on the salience of the currently fixated option.
    Since we lack RT data, we fit parameters based on the probability of
    choosing the left or right option.

    Attributes:
        threshold (float): Decision boundary (a).
        dt (float): Integration time step.
        w (float): Salience weight parameter.
        s (float): Noise scaling factor.
    """

    def __init__(
        self,
        threshold: float = DEFAULT_A,
        dt: float = DEFAULT_DT,
        w: float = DEFAULT_W,
        s: float = DEFAULT_S,
        max_time: float = MAX_TIME
    ):
        self.threshold = threshold
        self.dt = dt
        self.w = w
        self.s = s
        self.max_time = max_time
        self._validate_params()

    def _validate_params(self) -> None:
        """Validate that model parameters are within logical bounds."""
        if not (0.0 <= self.w <= 1.0):
            raise ValueError(f"Salience weight 'w' must be in [0, 1], got {self.w}")
        if self.threshold <= 0:
            raise ValueError(f"Threshold must be positive, got {self.threshold}")
        if self.dt <= 0:
            raise ValueError(f"Time step 'dt' must be positive, got {self.dt}")

    def compute_drift_rate(
        self,
        value_diff: float,
        salience_diff: float,
        is_fixated_left: bool
    ) -> float:
        """
        Compute the instantaneous drift rate based on value difference and salience.

        In the aDDM, the drift rate is modulated by attention.
        If fixated on Left: drift = (Value_L - Value_R) + w * (Salience_L - Salience_R)
        If fixated on Right: drift = (Value_L - Value_R) - w * (Salience_L - Salience_R)

        Since we don't have dynamic fixation data, we approximate the "fixation effect"
        by using the salience difference as a proxy for attentional bias.
        For choice-only fitting, we often assume a static bias or average fixation
        probability. Here, we implement the core logic:

        Args:
            value_diff (float): V_L - V_R (Value of Left minus Value of Right).
            salience_diff (float): S_L - S_R (Salience of Left minus Salience of Right).
            is_fixated_left (bool): True if currently fixating Left, False if Right.

        Returns:
            float: The instantaneous drift rate.
        """
        base_drift = value_diff
        salience_contribution = self.w * salience_diff

        if is_fixated_left:
            # Attention amplifies the difference in the direction of fixation
            # If S_L > S_R, salience_contribution is positive, boosting Left choice
            current_drift = base_drift + salience_contribution
        else:
            # Attention on Right reduces the effective drift towards Left
            current_drift = base_drift - salience_contribution

        return current_drift

    def simulate_trial(
        self,
        value_diff: float,
        salience_diff: float,
        fixation_sequence: Optional[List[bool]] = None,
        seed: Optional[int] = None
    ) -> Tuple[bool, float]:
        """
        Simulate a single trial of the aDDM.

        Args:
            value_diff (float): V_L - V_R.
            salience_diff (float): S_L - S_R.
            fixation_sequence (Optional[List[bool]]): List of booleans indicating
                fixation at each time step (True=Left, False=Right).
                If None, a random sequence is generated based on salience.
            seed (Optional[int]): Random seed for reproducibility.

        Returns:
            Tuple[bool, float]: (Choice: True for Left, False for Right), Time taken.
        """
        if seed is not None:
            np.random.seed(seed)

        x = 0.0  # Accumulator state
        t = 0.0

        # Generate fixation sequence if not provided
        # Simple heuristic: probability of fixating Left is proportional to its salience
        if fixation_sequence is None:
            # Normalize salience to probability [0, 1]
            # Sigmoid-like mapping or simple normalization if we had absolute values.
            # For this implementation, we assume salience_diff is small and use a
            # logistic function or a simple bias.
            # Let's use a simple bias: P(Left) = 0.5 + 0.2 * tanh(salience_diff)
            p_left = 0.5 + 0.2 * np.tanh(salience_diff)
            # Generate enough steps for max_time
            n_steps = int(self.max_time / self.dt)
            fixation_sequence = [np.random.rand() < p_left for _ in range(n_steps)]

        steps = int(self.max_time / self.dt)
        for i in range(steps):
            t += self.dt
            is_left = fixation_sequence[i] if i < len(fixation_sequence) else (i % 2 == 0)

            # Compute drift
            drift = self.compute_drift_rate(value_diff, salience_diff, is_left)

            # Add noise: N(0, s * sqrt(dt))
            noise = np.random.normal(0.0, self.s * np.sqrt(self.dt))

            # Update accumulator
            x += drift * self.dt + noise

            # Check for boundary crossing
            if x >= self.threshold:
                return True, t  # Chose Left
            elif x <= -self.threshold:
                return False, t  # Chose Right

        # If no boundary crossed, return based on final state (or default)
        logger.warning(f"Trial did not converge within max_time ({self.max_time}s).")
        return x > 0, t

    def predict_choice_probability(
        self,
        value_diff: float,
        salience_diff: float,
        n_simulations: int = 1000,
        seed: Optional[int] = None
    ) -> float:
        """
        Estimate the probability of choosing the Left option via Monte Carlo simulation.

        Args:
            value_diff (float): V_L - V_R.
            salience_diff (float): S_L - S_R.
            n_simulations (int): Number of trials to simulate.
            seed (Optional[int]): Random seed.

        Returns:
            float: Probability of choosing Left (0.0 to 1.0).
        """
        if seed is not None:
            np.random.seed(seed)

        choices = []
        for _ in range(n_simulations):
            choice, _ = self.simulate_trial(value_diff, salience_diff)
            choices.append(1 if choice else 0)

        return np.mean(choices)

    def log_likelihood(
        self,
        params: Dict[str, float],
        data: pd.DataFrame,
        value_col: str = 'value_diff',
        salience_col: str = 'salience_diff',
        choice_col: str = 'choice'
    ) -> float:
        """
        Calculate the log-likelihood of the observed data given the parameters.

        Note: This is a simplified version. For choice-only data, we often compare
        the predicted probability to the observed choice.

        Args:
            params (Dict): Model parameters (e.g., {'w': 0.5, 'a': 1.0}).
            data (pd.DataFrame): DataFrame containing value_diff, salience_diff, choice.
            value_col (str): Column name for value difference.
            salience_col (str): Column name for salience difference.
            choice_col (str): Column name for choice (1=Left, 0=Right).

        Returns:
            float: Log-likelihood value.
        """
        import pandas as pd
        # Update instance parameters
        if 'w' in params: self.w = params['w']
        if 'a' in params: self.threshold = params['a']

        total_ll = 0.0
        # Vectorized approximation or loop?
        # For simplicity and robustness with the existing pipeline, we loop.
        # Optimization can be added later.
        
        for idx, row in data.iterrows():
            v_diff = row[value_col]
            s_diff = row[salience_col]
            obs_choice = row[choice_col]

            # Predict probability
            p_left = self.predict_choice_probability(v_diff, s_diff, n_simulations=200)
            
            # Clamp probability to avoid log(0)
            p_left = np.clip(p_left, 1e-7, 1 - 1e-7)

            if obs_choice == 1:
                total_ll += np.log(p_left)
            else:
                total_ll += np.log(1 - p_left)

        return total_ll


def run_single_simulation(
    value_diff: float,
    salience_diff: float,
    w: float = DEFAULT_W,
    threshold: float = DEFAULT_A,
    dt: float = DEFAULT_DT,
    seed: Optional[int] = None
) -> Tuple[bool, float]:
    """
    Convenience function to run a single aDDM simulation.

    Args:
        value_diff: V_L - V_R
        salience_diff: S_L - S_R
        w: Salience weight
        threshold: Decision threshold
        dt: Time step
        seed: Random seed

    Returns:
        Tuple[bool, float]: (Chose Left, Time)
    """
    model = aDDMChoiceOnly(w=w, threshold=threshold, dt=dt)
    return model.simulate_trial(value_diff, salience_diff, seed=seed)


def main():
    """
    Main entry point for testing the aDDM implementation.
    Runs a quick simulation to verify the module works.
    """
    logger.info("Running aDDM Choice-Only Self-Test...")

    # Test 1: Basic simulation
    v_diff = 0.5
    s_diff = 0.2
    choice, time = run_single_simulation(v_diff, s_diff, seed=42)
    logger.info(f"Simulation 1: ValueDiff={v_diff}, SalDiff={s_diff} -> Choice={'Left' if choice else 'Right'}, Time={time:.2f}s")

    # Test 2: Probability estimation
    model = aDDMChoiceOnly(w=0.9, threshold=1.0)
    p_left = model.predict_choice_probability(v_diff, s_diff, n_simulations=500, seed=123)
    logger.info(f"Predicted P(Left) for v_diff={v_diff}, s_diff={s_diff}: {p_left:.3f}")

    # Test 3: High salience bias
    # If value_diff is 0 but salience_diff is high, Left should be favored
    p_bias = model.predict_choice_probability(0.0, 1.0, n_simulations=500, seed=456)
    logger.info(f"Predicted P(Left) for v_diff=0.0, s_diff=1.0: {p_bias:.3f} (Should be > 0.5)")

    logger.info("aDDM Self-Test Complete.")


if __name__ == "__main__":
    main()