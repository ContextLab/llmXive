import numpy as np
from typing import Tuple, Dict, Optional, List
import json
import os

class SyntheticTabularMDP:
    """
    Synthetic Tabular MDP Generator for Multi-Objective RL.
    
    Supports:
    - Configurable number of objectives (N)
    - Explicit noise correlation structure (rho)
    - Deterministic seeded random state management
    - Sensitivity analysis for noise correlation structure (FR-009)
    """
    
    def __init__(
        self,
        n_states: int = 10,
        n_actions: int = 4,
        n_objectives: int = 5,
        rho: float = 0.0,
        seed: Optional[int] = None
    ):
        """
        Initialize the Synthetic MDP.
        
        Args:
            n_states: Number of states in the MDP
            n_actions: Number of actions available in each state
            n_objectives: Number of reward objectives (N)
            rho: Noise correlation parameter (ρ ∈ {0, 0.2, 0.5})
                - 0.0: Independent noise across objectives
                0.2: Low positive correlation
                0.5: Moderate positive correlation
            seed: Random seed for reproducibility
        """
        self.n_states = n_states
        self.n_actions = n_actions
        self.n_objectives = n_objectives
        self.rho = rho
        self.seed = seed if seed is not None else 42
        
        # Validate rho
        if not (-1.0 <= rho <= 1.0):
            raise ValueError(f"Noise correlation rho must be in [-1, 1], got {rho}")
        
        # Initialize random state
        self.rng = np.random.default_rng(self.seed)
        
        # Generate MDP components
        self._generate_transition_matrix()
        self._generate_reward_functions()
        
    def _generate_transition_matrix(self):
        """Generate sparse random transition probabilities."""
        # Create a transition matrix P[s, a, s']
        self.P = np.zeros((self.n_states, self.n_actions, self.n_states))
        
        for s in range(self.n_states):
            for a in range(self.n_actions):
                # Random transition probabilities
                probs = self.rng.random(self.n_states)
                probs /= probs.sum()
                self.P[s, a, :] = probs
                
    def _generate_reward_functions(self):
        """
        Generate reward functions with configurable noise correlation.
        
        For each state-action pair, generates a reward vector across N objectives.
        Noise correlation is controlled by rho parameter:
        - rho = 0: Independent noise for each objective
        - rho > 0: Positive correlation between objectives
        """
        # Base reward functions (deterministic component)
        # Shape: (n_states, n_actions, n_objectives)
        self.base_rewards = self.rng.random((self.n_states, self.n_actions, self.n_objectives))
        
        # Pre-compute correlation structure for noise
        self._build_noise_covariance()
        
    def _build_noise_covariance(self):
        """
        Build the covariance matrix for correlated noise across objectives.
        
        For rho ∈ {0, 0.2, 0.5}:
        - Diagonal elements = 1 (variance)
        - Off-diagonal elements = rho (covariance)
        """
        if self.n_objectives == 1:
            self.noise_cov = np.array([[1.0]])
            return
        
        # Create correlation matrix
        self.noise_cov = np.full((self.n_objectives, self.n_objectives), self.rho)
        np.fill_diagonal(self.noise_cov, 1.0)
        
        # Ensure positive semi-definiteness (adjust if needed)
        eigenvalues = np.linalg.eigvalsh(self.noise_cov)
        if np.any(eigenvalues < -1e-10):
            # Adjust to make PSD: set rho to max allowed value
            max_rho = 1.0 / (1 - self.n_objectives)
            if self.rho < max_rho:
                self.rho = max_rho + 1e-6
                self.noise_cov = np.full((self.n_objectives, self.n_objectives), self.rho)
                np.fill_diagonal(self.noise_cov, 1.0)
        
        # Compute Cholesky decomposition for noise generation
        try:
            self.noise_cholesky = np.linalg.cholesky(self.noise_cov)
        except np.linalg.LinAlgError:
            # Fallback: use eigendecomposition if Cholesky fails
            eigenvalues, eigenvectors = np.linalg.eigh(self.noise_cov)
            eigenvalues = np.maximum(eigenvalues, 1e-10)
            self.noise_cholesky = eigenvectors @ np.diag(np.sqrt(eigenvalues))
        
    def step(self, state: int, action: int, noise_scale: float = 0.1) -> Tuple[int, np.ndarray, bool, Dict]:
        """
        Execute one step in the MDP.
        
        Args:
            state: Current state index
            action: Action to take
            noise_scale: Scale factor for stochastic noise
            
        Returns:
            next_state: Next state index
            reward: Reward vector of shape (n_objectives,)
            done: Whether episode is terminated
            info: Additional information dictionary
        """
        # Sample next state
        next_state = self.rng.choice(
            self.n_states,
            p=self.P[state, action, :]
        )
        
        # Get base reward
        base_reward = self.base_rewards[state, action, :]
        
        # Generate correlated noise
        if self.rho == 0.0:
            # Independent noise
            noise = self.rng.standard_normal(self.n_objectives) * noise_scale
        else:
            # Correlated noise using Cholesky decomposition
            independent_noise = self.rng.standard_normal(self.n_objectives)
            correlated_noise = self.noise_cholesky @ independent_noise
            noise = correlated_noise * noise_scale
        
        reward = base_reward + noise
        
        # Termination condition (simple: random termination with low probability)
        done = self.rng.random() < 0.05
        
        info = {
            'rho': self.rho,
            'n_objectives': self.n_objectives,
            'noise_scale': noise_scale,
            'transition_prob': self.P[state, action, next_state]
        }
        
        return next_state, reward, done, info
        
    def reset(self, seed: Optional[int] = None) -> int:
        """
        Reset the MDP to a random initial state.
        
        Args:
            seed: Optional seed for reset (overrides class seed)
            
        Returns:
            initial_state: Starting state index
        """
        if seed is not None:
            self.rng = np.random.default_rng(seed)
            
        initial_state = self.rng.integers(0, self.n_states)
        return initial_state
        
    def get_state_features(self, state: int) -> np.ndarray:
        """
        Get feature representation of a state.
        
        Args:
            state: State index
            
        Returns:
            One-hot encoded state feature vector
        """
        features = np.zeros(self.n_states)
        features[state] = 1.0
        return features
        
    def get_objective_weights(self, n_weights: int = 10) -> np.ndarray:
        """
        Generate random objective weight vectors for scalarization.
        
        Args:
            n_weights: Number of weight vectors to generate
            
        Returns:
            Array of shape (n_weights, n_objectives) with normalized weights
        """
        weights = self.rng.random((n_weights, self.n_objectives))
        weights /= weights.sum(axis=1, keepdims=True)
        return weights
        
    def get_metadata(self) -> Dict:
        """
        Get MDP metadata including configuration parameters.
        
        Returns:
            Dictionary containing MDP configuration and properties
        """
        return {
            'n_states': self.n_states,
            'n_actions': self.n_actions,
            'n_objectives': self.n_objectives,
            'rho': self.rho,
            'seed': self.seed,
            'noise_covariance_matrix': self.noise_cov.tolist() if hasattr(self, 'noise_cov') else None,
            'transition_matrix_shape': self.P.shape,
            'base_reward_shape': self.base_rewards.shape
        }
        
    def save_to_file(self, filepath: str):
        """
        Save MDP configuration to a JSON file.
        
        Args:
            filepath: Path to save the configuration
        """
        metadata = self.get_metadata()
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
            
    @classmethod
    def load_from_file(cls, filepath: str) -> 'SyntheticTabularMDP':
        """
        Load MDP configuration from a JSON file.
        
        Args:
            filepath: Path to the configuration file
            
        Returns:
            SyntheticTabularMDP instance
        """
        with open(filepath, 'r') as f:
            metadata = json.load(f)
        
        mdp = cls(
            n_states=metadata['n_states'],
            n_actions=metadata['n_actions'],
            n_objectives=metadata['n_objectives'],
            rho=metadata['rho'],
            seed=metadata['seed']
        )
        return mdp

def main():
    """
    Main function to demonstrate MDP generation with sensitivity analysis
    for noise correlation structure (FR-009).
    
    Generates MDPs for different rho values and saves configurations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Synthetic MDP Generator for Sensitivity Analysis')
    parser.add_argument('--n-states', type=int, default=10, help='Number of states')
    parser.add_argument('--n-actions', type=int, default=4, help='Number of actions')
    parser.add_argument('--n-objectives', type=int, default=5, help='Number of objectives')
    parser.add_argument('--rho-values', type=str, default='0.0,0.2,0.5', 
                      help='Comma-separated noise correlation values')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output-dir', type=str, default='data/raw', 
                      help='Directory to save MDP configurations')
    
    args = parser.parse_args()
    
    # Parse rho values
    rho_values = [float(x.strip()) for x in args.rho_values.split(',')]
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Generating synthetic MDPs for sensitivity analysis...")
    print(f"Parameters: N={args.n_objectives}, States={args.n_states}, Actions={args.n_actions}")
    print(f"Rho values: {rho_values}")
    
    for rho in rho_values:
        print(f"\nGenerating MDP with rho={rho}...")
        
        try:
            mdp = SyntheticTabularMDP(
                n_states=args.n_states,
                n_actions=args.n_actions,
                n_objectives=args.n_objectives,
                rho=rho,
                seed=args.seed
            )
            
            # Save configuration
            output_path = os.path.join(args.output_dir, f'mdp_n{args.n_objectives}_rho{rho}.json')
            mdp.save_to_file(output_path)
            print(f"  Saved configuration to: {output_path}")
            
            # Verify noise correlation structure
            metadata = mdp.get_metadata()
            print(f"  Noise correlation matrix diagonal: {np.diag(metadata['noise_covariance_matrix'])[0]:.4f}")
            if args.n_objectives > 1:
                print(f"  Noise correlation matrix off-diagonal: {metadata['noise_covariance_matrix'][0][1]:.4f}")
            
            # Run a quick simulation to verify functionality
            state = mdp.reset()
            for step in range(5):
                action = mdp.rng.integers(0, mdp.n_actions)
                next_state, reward, done, info = mdp.step(state, action)
                if step == 0:
                    print(f"  Sample step: state={state}, action={action}, reward={reward[:3]}...")
                state = next_state
                if done:
                    state = mdp.reset()
            
            print(f"  MDP generated and validated successfully!")
            
        except Exception as e:
            print(f"  Error generating MDP with rho={rho}: {e}")
            continue
    
    print(f"\nSensitivity analysis setup complete.")
    print(f"Generated MDPs for rho values: {rho_values}")

if __name__ == '__main__':
    main()