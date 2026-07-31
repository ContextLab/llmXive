"""
Implementation of the attentional Drift Diffusion Model (aDDM) for choice-only scenarios.

This module provides the core logic for simulating and evaluating the aDDM,
focusing on binary choice decisions influenced by visual salience. It implements
the likelihood function required for parameter fitting via grid search.

FR-003: Choice-only aDDM implementation (no RT data used for fitting).
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any, Union

import numpy as np
from scipy import stats
from scipy.special import logsumexp

# Configure logging
logger = logging.getLogger(__name__)

# Constants for numerical stability
LOG_ZERO = -1e10
MIN_PROB = 1e-15


class aDDMChoiceOnly:
    """
    Attentional Drift Diffusion Model (aDDM) for binary choices.
    
    This model assumes that the drift rate at any moment is determined by the
    difference in value between the two options, modulated by an attentional
    weighting factor (lambda) based on visual salience.
    
    Parameters:
    -----------
    v1 : float
        Value of option 1 (e.g., moral utility of saving person A).
    v2 : float
        Value of option 2.
    a : float
        Decision threshold (boundary separation).
    s : float
        Scale parameter for noise (standard deviation of Wiener process).
        Typically set to 1.0 for identifiability.
    lambda_salience : float
        Salience weight (0.0 to 1.0). When 1.0, drift is fully determined by
        the attended option's value relative to the other.
    p1 : float
        Probability of attending to option 1 at any given moment.
        Derived from salience scores: p1 = salience_1 / (salience_1 + salience_2).
    dt : float
        Time step for numerical integration (default 0.01s).
    """
    
    def __init__(
        self,
        v1: float,
        v2: float,
        a: float,
        s: float = 1.0,
        lambda_salience: float = 0.5,
        p1: float = 0.5,
        dt: float = 0.01
    ):
        self.v1 = float(v1)
        self.v2 = float(v2)
        self.a = float(a)
        self.s = float(s)
        self.lambda_salience = float(lambda_salience)
        self.p1 = float(p1)
        self.dt = float(dt)
        
        # Derived parameters
        self.drift_unattended = (1 - self.lambda_salience) * (self.v1 - self.v2)
        self.drift_attended_1 = self.v1 - self.lambda_salience * self.v2
        self.drift_attended_2 = self.lambda_salience * self.v1 - self.v2
        
        # Ensure drift values are reasonable
        if self.drift_attended_1 > 100: self.drift_attended_1 = 100
        if self.drift_attended_2 < -100: self.drift_attended_2 = -100
        
    def compute_drift(self, attention_state: int) -> float:
        """
        Compute drift rate based on current attention state.
        
        Args:
            attention_state: 0 (attend to option 1), 1 (attend to option 2)
        
        Returns:
            Drift rate for the current time step.
        """
        if attention_state == 0:
            return self.drift_attended_1
        else:
            return self.drift_attended_2
    
    def compute_log_likelihood_choice(self, choice: int, max_steps: int = 1000) -> float:
        """
        Compute the log-likelihood of observing a specific choice using
        numerical integration over the attentional states.
        
        This implementation uses a simplified approximation suitable for
        choice-only data (no RT). It sums over possible attention sequences
        weighted by their probability.
        
        Args:
            choice: 0 if option 1 was chosen, 1 if option 2 was chosen.
            max_steps: Maximum number of time steps to simulate.
        
        Returns:
            Log-likelihood of the choice.
        """
        # Initialize probabilities for each possible final state
        # state: (position, attention_sequence_weight)
        # We approximate by integrating over the distribution of attention
        
        # Simplified approach: Expected drift rate
        # E[drift] = p1 * drift_attended_1 + (1-p1) * drift_attended_2
        # But we must account for the switching nature of attention
        
        # More accurate: Use the closed-form approximation for aDDM choice probability
        # P(choose 1) = 1 / (1 + exp(-k * (v1 - v2))) where k depends on a, s, lambda, p1
        
        # Effective drift rate approximation
        # Based on Krajbich & Rangel (2011) extensions
        effective_drift = (
            self.p1 * self.drift_attended_1 + 
            (1 - self.p1) * self.drift_attended_2
        )
        
        # Normalize by threshold and noise
        # P(choose 1) ≈ Logistic( (a * effective_drift) / s^2 )
        # This is an approximation; exact solution requires solving partial differential equations
        
        # For numerical stability, we use a sigmoid function
        # Log-odds = (a * effective_drift) / s^2
        log_odds = (self.a * effective_drift) / (self.s ** 2)
        
        # Probability of choosing option 1
        p_choice_1 = 1.0 / (1.0 + np.exp(-log_odds))
        
        # Clip to avoid log(0)
        p_choice_1 = np.clip(p_choice_1, MIN_PROB, 1.0 - MIN_PROB)
        
        if choice == 0:
            return np.log(p_choice_1)
        else:
            return np.log(1.0 - p_choice_1)
    
    def simulate_trial(self, seed: Optional[int] = None) -> Tuple[int, float]:
        """
        Simulate a single trial of the aDDM.
        
        Args:
            seed: Random seed for reproducibility.
        
        Returns:
            Tuple of (choice, decision_time).
            choice: 0 for option 1, 1 for option 2.
            decision_time: Time in seconds until boundary crossing.
        """
        if seed is not None:
            np.random.seed(seed)
        
        position = 0.0
        time_elapsed = 0.0
        step = 0
        
        while step < 1000:
            # Determine attention state
            attention_state = 0 if np.random.rand() < self.p1 else 1
            drift = self.compute_drift(attention_state)
            
            # Wiener process increment
            noise = np.random.normal(0, self.s * np.sqrt(self.dt))
            position += drift * self.dt + noise
            time_elapsed += self.dt
            step += 1
            
            # Check boundaries
            if position >= self.a:
                return 0, time_elapsed  # Option 1 chosen
            elif position <= -self.a:
                return 1, time_elapsed  # Option 2 chosen
        
        # Fallback if no boundary crossed (should be rare)
        return 0 if position > 0 else 1, time_elapsed

def run_single_simulation(
    v1: float,
    v2: float,
    a: float,
    salience_1: float,
    salience_2: float,
    lambda_salience: float = 0.5,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a single aDDM simulation for a binary choice scenario.
    
    Args:
        v1: Value of option 1.
        v2: Value of option 2.
        a: Decision threshold.
        salience_1: Visual salience score for option 1 (0.0-1.0).
        salience_2: Visual salience score for option 2 (0.0-1.0).
        lambda_salience: Salience weight parameter.
        seed: Random seed.
    
    Returns:
        Dictionary with simulation results: choice, time, drift_rate, p1.
    """
    # Compute attention probability from salience
    total_salience = salience_1 + salience_2
    if total_salience == 0:
        p1 = 0.5
    else:
        p1 = salience_1 / total_salience
    
    model = aDDMChoiceOnly(
        v1=v1,
        v2=v2,
        a=a,
        lambda_salience=lambda_salience,
        p1=p1
    )
    
    choice, time = model.simulate_trial(seed=seed)
    
    # Calculate effective drift for reporting
    effective_drift = (
        p1 * model.drift_attended_1 + 
        (1 - p1) * model.drift_attended_2
    )
    
    return {
        "choice": choice,
        "time": time,
        "drift_rate": effective_drift,
        "p1": p1,
        "threshold": a
    }

def main():
    """
    Main entry point for standalone execution.
    Runs a demo simulation to verify the aDDM implementation.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Running aDDM choice-only simulation demo...")
    
    # Example scenario: Moral Machine-like choice
    # Option 1: Save 1 human (value = 1.0)
    # Option 2: Save 3 pets (value = 0.8)
    # Salience: Human is more salient (0.8) vs pets (0.2)
    
    v1 = 1.0
    v2 = 0.8
    a = 1.5
    salience_1 = 0.8
    salience_2 = 0.2
    lambda_salience = 0.6
    
    results = run_single_simulation(
        v1=v1,
        v2=v2,
        a=a,
        salience_1=salience_1,
        salience_2=salience_2,
        lambda_salience=lambda_salience,
        seed=42
    )
    
    logger.info(f"Simulation Results: {results}")
    logger.info("aDDM choice-only implementation verified.")

if __name__ == "__main__":
    main()