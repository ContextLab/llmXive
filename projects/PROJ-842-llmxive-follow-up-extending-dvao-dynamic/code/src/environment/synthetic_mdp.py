import numpy as np
from typing import Tuple, Dict, Optional, List, Any
import json
import os
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SyntheticTabularMDP:
    n_objectives: int
    state_space: List[np.ndarray]
    action_space: List[int]
    transition_probs: np.ndarray  # [S, A, S]
    reward_vectors: List[np.ndarray]  # List of reward vectors per objective
    noise_correlation: float
    degraded_flag: bool = False
    effective_n: int = 0
    reduced_state_space_size: int = 0
    _rng: np.random.Generator = field(default_factory=lambda: np.random.default_rng(42))

    def get_state_features(self, state_idx: int) -> np.ndarray:
        return self.state_space[state_idx]

    def get_reward_for_state_action(self, state_idx: int, action: int) -> np.ndarray:
        # Return a vector of shape (n_objectives,)
        base_reward = np.dot(self.state_space[state_idx], self.reward_vectors[0]) # Simplified for demo
        # In a real multi-objective setup, this would sum over objectives
        # For this task, we assume reward_vectors is a list of weight vectors per objective
        rewards = []
        for i in range(self.n_objectives):
            # Example: linear combination of features
            w = self.reward_vectors[i]
            r = np.dot(self.state_space[state_idx], w)
            rewards.append(r)
        return np.array(rewards)

    def step(self, state: int, action: int) -> Tuple[int, np.ndarray, bool]:
        next_state = self._rng.choice(self.action_space, p=self.transition_probs[state, action])
        reward = self.get_reward_for_state_action(next_state, action)
        done = False # Simplified
        return next_state, reward, done

def generate_non_convex_rewards(state_features: np.ndarray) -> List[np.ndarray]:
    # Placeholder for non-convex logic
    return [np.random.rand(len(state_features)) for _ in range(5)]

def generate_heavy_tailed_mdp(n_objectives: int, seed: int) -> SyntheticTabularMDP:
    rng = np.random.default_rng(seed)
    S = 20
    A = 5
    features = rng.standard_normal((S, 5))
    rewards = [rng.standard_cauchy(5) for _ in range(n_objectives)] # Heavy tailed
    trans = np.ones((S, A, S)) / S
    return SyntheticTabularMDP(
        n_objectives=n_objectives,
        state_space=list(features),
        action_space=list(range(A)),
        transition_probs=trans,
        reward_vectors=rewards,
        noise_correlation=0.0
    )

def validate_distribution(dist_name: str) -> bool:
    return dist_name in ["linear", "sparse", "non-convex", "heavy_tailed"]

def _generate_correlated_noise_matrix(
    n_objectives: int,
    rho: float,
    rng: np.random.Generator
) -> np.ndarray:
    """
    Generates a noise covariance matrix with off-diagonal correlation rho.
    Returns the matrix and a log summary.
    """
    if n_objectives == 1:
        return np.array([[1.0]]), {"mean_off_diagonal": 0.0, "diag_mean": 1.0}

    # Construct correlation matrix
    # R_ij = rho if i != j, 1.0 if i == j
    R = np.full((n_objectives, n_objectives), rho)
    np.fill_diagonal(R, 1.0)

    # Check positive semi-definiteness (rho must be > -1/(n-1))
    min_eig = np.min(np.linalg.eigvalsh(R))
    if min_eig <= 0:
        logger.warning(f"Target correlation rho={rho} with N={n_objectives} yields non-PSD matrix (min_eig={min_eig}). Adjusting rho.")
        # Adjust rho to be safe
        rho_safe = -1.0 / (n_objectives - 1) + 1e-4
        R = np.full((n_objectives, n_objectives), rho_safe)
        np.fill_diagonal(R, 1.0)

    # Compute Cholesky decomposition to generate correlated samples if needed
    # Here we just return the theoretical matrix properties for logging
    mean_off_diag = np.mean(R[np.triu_indices(n_objectives, k=1)])
    diag_mean = np.mean(np.diag(R))

    log_summary = {
        "target_rho": rho,
        "actual_rho": mean_off_diag,
        "mean_off_diagonal": float(mean_off_diag),
        "diag_mean": float(diag_mean),
        "min_eigenvalue": float(min_eig) if n_objectives > 1 else 1.0
    }

    return R, log_summary

def generate_mdp(
    n_objectives: int,
    seed: int,
    noise_correlation: float = 0.0,
    distribution: str = "linear",
    rollout_size: int = 1000
) -> SyntheticTabularMDP:
    """
    Generates a synthetic tabular MDP with N objectives.
    Implements T087: Logs correlation matrix properties when rho > 0.
    """
    rng = np.random.default_rng(seed)

    # State space generation (simplified for memory efficiency in T086 context)
    S = max(10, n_objectives * 2)
    if n_objectives > 50:
        # Degradation logic from T034
        S = max(10, S // 2)
        degraded_flag = True
        effective_n = n_objectives
        reduced_state_space_size = S
    else:
        degraded_flag = False
        effective_n = n_objectives
        reduced_state_space_size = S

    state_features = rng.standard_normal((S, 5))
    action_space = list(range(5))
    
    # Transition probabilities (uniform for simplicity)
    transition_probs = np.ones((S, len(action_space), S)) / S

    # Reward vectors
    reward_vectors = []
    for i in range(n_objectives):
        if distribution == "sparse":
            w = rng.standard_normal(5)
            w[rng.random(5) < 0.9] = 0.0 # 90% sparsity
            reward_vectors.append(w)
        elif distribution == "non-convex":
            # Placeholder for non-convex generation
            reward_vectors.append(generate_non_convex_rewards(state_features[0])[0])
        else: # linear
            reward_vectors.append(rng.standard_normal(5))

    # Noise Correlation Logic (T087)
    achieved_corr_log = None
    if noise_correlation > 0:
        R, log_summary = _generate_correlated_noise_matrix(n_objectives, noise_correlation, rng)
        achieved_corr_log = log_summary
        
        # Log to console
        logger.info(f"Generated Correlated Noise (rho={noise_correlation}):")
        logger.info(f"  Mean Off-Diagonal: {log_summary['mean_off_diagonal']:.4f}")
        logger.info(f"  Diagonal Mean: {log_summary['diag_mean']:.4f}")
        logger.info(f"  Min Eigenvalue: {log_summary['min_eigenvalue']:.4f}")

        # Write to JSON file
        output_dir = "data/processed"
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, "noise_properties.json")
        
        # Load existing if present to append, or create new
        existing_data = []
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = []

        entry = {
            "n_objectives": n_objectives,
            "seed": seed,
            "target_rho": noise_correlation,
            "summary": log_summary,
            "timestamp": str(rng.integers(0, 2**32)) # Simple timestamp
        }
        existing_data.append(entry)

        with open(json_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        logger.info(f"Correlation properties written to {json_path}")

    return SyntheticTabularMDP(
        n_objectives=n_objectives,
        state_space=list(state_features),
        action_space=action_space,
        transition_probs=transition_probs,
        reward_vectors=reward_vectors,
        noise_correlation=noise_correlation,
        degraded_flag=degraded_flag,
        effective_n=effective_n,
        reduced_state_space_size=reduced_state_space_size,
        _rng=rng
    )

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-objectives", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--noise-correlation", type=float, default=0.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    mdp = generate_mdp(
        n_objectives=args.n_objectives,
        seed=args.seed,
        noise_correlation=args.noise_correlation
    )
    print(f"MDP generated: N={mdp.n_objectives}, Degraded={mdp.degraded_flag}")
    if args.noise_correlation > 0:
        print("Check data/processed/noise_properties.json for correlation details.")

if __name__ == "__main__":
    main()
