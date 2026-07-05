"""
Simplified Ising spin-flip dynamics for spin networks.
CPU-only implementation with default float precision.
"""
import numpy as np
import networkx as nx
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class IsingDynamics:
    """
    Implements simplified Ising spin-flip dynamics on a given network.
    
    The system evolves via single-spin flips accepted/rejected based on
    the Metropolis-Hastings criterion at a given temperature.
    """

    def __init__(
        self,
        graph: nx.Graph,
        initial_spins: Optional[np.ndarray] = None,
        temperature: float = 1.0,
        coupling_strength: float = 1.0,
        seed: Optional[int] = None
    ):
        """
        Initialize the dynamics simulator.
        
        Args:
            graph: The network topology (nodes are spins).
            initial_spins: Optional initial spin configuration (array of +1/-1).
                           If None, initialized randomly.
            temperature: Thermal energy kT (float).
            coupling_strength: J coupling constant (float).
            seed: Random seed for reproducibility.
        """
        if not isinstance(graph, nx.Graph):
            raise TypeError("graph must be a networkx Graph")
        
        self.graph = graph
        self.num_nodes = graph.number_of_nodes()
        self.nodes = list(graph.nodes())
        self.adj = graph.adj
        
        # Map node indices to array indices for efficient access
        self.node_to_idx = {node: i for i, node in enumerate(self.nodes)}
        self.idx_to_node = {i: node for i, node in enumerate(self.nodes)}
        
        # Initialize spins
        if initial_spins is not None:
            if len(initial_spins) != self.num_nodes:
                raise ValueError(f"initial_spins length ({len(initial_spins)}) "
                               f"must match number of nodes ({self.num_nodes})")
            self.spins = initial_spins.astype(np.float64)
        else:
            if seed is not None:
                np.random.seed(seed)
            self.spins = np.random.choice([-1.0, 1.0], size=self.num_nodes).astype(np.float64)
        
        self.temperature = float(temperature)
        self.J = float(coupling_strength)
        self.seed = seed
        
        # Precompute neighbor indices for each node
        self.neighbors_idx = [
            [self.node_to_idx[neighbor] for neighbor in self.adj[node]]
            for node in self.nodes
        ]

    def _energy_change(self, node_idx: int, flip_value: float) -> float:
        """
        Calculate energy change if spin at node_idx flips.
        
        In the Ising model: E = -J * sum(s_i * s_j) over edges.
        Flipping s_i -> -s_i changes energy by:
        delta_E = 2 * J * s_i * sum(s_j over neighbors)
        
        Args:
            node_idx: Index of the node to flip.
            flip_value: The value to flip TO (should be -current).
        
        Returns:
            Energy change (delta_E).
        """
        current_spin = self.spins[node_idx]
        neighbor_spins_sum = sum(self.spins[n_idx] for n_idx in self.neighbors_idx[node_idx])
        
        # Delta E = -J * (new_spin * neighbor_sum - old_spin * neighbor_sum)
        #         = -J * neighbor_sum * (new_spin - old_spin)
        # If flipping: new_spin = -old_spin, so (new - old) = -2*old_spin
        # Delta E = -J * neighbor_sum * (-2 * old_spin) = 2 * J * old_spin * neighbor_sum
        
        delta_e = 2.0 * self.J * current_spin * neighbor_spins_sum
        return delta_e

    def step(self, n_steps: Optional[int] = None) -> Dict[str, Any]:
        """
        Perform one Monte Carlo step (n_trials = number of nodes).
        
        Args:
            n_steps: Optional override for number of flip attempts. 
                     Defaults to number of nodes (1 MC step per spin).
        
        Returns:
            Dictionary with simulation statistics for this step.
        """
        if n_steps is None:
            n_steps = self.num_nodes
        
        accepted_flips = 0
        total_attempts = 0
        
        # Determine random order of spins to visit
        order = np.random.permutation(self.num_nodes)
        
        for _ in range(n_steps):
            node_idx = order[total_attempts % self.num_nodes]
            total_attempts += 1
            
            current_spin = self.spins[node_idx]
            proposed_spin = -current_spin
            
            delta_e = self._energy_change(node_idx, proposed_spin)
            
            # Metropolis criterion
            if delta_e <= 0:
                # Always accept if energy decreases or stays same
                self.spins[node_idx] = proposed_spin
                accepted_flips += 1
            else:
                # Accept with probability exp(-delta_E / kT)
                if self.temperature > 0:
                    prob = np.exp(-delta_e / self.temperature)
                    if np.random.random() < prob:
                        self.spins[node_idx] = proposed_spin
                        accepted_flips += 1
        
        return {
            "accepted_flips": accepted_flips,
            "total_attempts": total_attempts,
            "acceptance_rate": accepted_flips / total_attempts if total_attempts > 0 else 0.0
        }

    def get_energy(self) -> float:
        """
        Calculate total system energy: E = -J * sum(s_i * s_j) over edges.
        
        Returns:
            Total energy (float).
        """
        energy = 0.0
        for u, v in self.graph.edges():
            i, j = self.node_to_idx[u], self.node_to_idx[v]
            energy += self.spins[i] * self.spins[j]
        return -self.J * energy

    def get_magnetization(self) -> float:
        """
        Calculate total magnetization: M = sum(s_i).
        
        Returns:
            Total magnetization (float).
        """
        return float(np.sum(self.spins))

    def get_magnetization_density(self) -> float:
        """
        Calculate magnetization density: m = M / N.
        
        Returns:
            Magnetization density (float).
        """
        return self.get_magnetization() / self.num_nodes

    def get_spin_configuration(self) -> np.ndarray:
        """
        Return a copy of the current spin configuration.
        
        Returns:
            Numpy array of spins (+1/-1).
        """
        return self.spins.copy()

    def run_simulation(
        self,
        n_steps: int,
        verbose: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Run the simulation for a specified number of steps.
        
        Args:
            n_steps: Number of Monte Carlo steps to run.
            verbose: If True, log progress.
        
        Returns:
            Tuple of (time_steps, energies, magnetizations) arrays.
        """
        time_steps = np.arange(n_steps + 1)
        energies = np.zeros(n_steps + 1)
        magnetizations = np.zeros(n_steps + 1)
        
        # Record initial state
        energies[0] = self.get_energy()
        magnetizations[0] = self.get_magnetization()
        
        for t in range(1, n_steps + 1):
            self.step()
            energies[t] = self.get_energy()
            magnetizations[t] = self.get_magnetization()
            
            if verbose and t % 100 == 0:
                logger.info(f"Step {t}/{n_steps}: E={energies[t]:.4f}, M={magnetizations[t]:.4f}")
        
        return time_steps, energies, magnetizations

def create_dynamics(
    graph: nx.Graph,
    temperature: float = 1.0,
    seed: Optional[int] = None
) -> IsingDynamics:
    """
    Factory function to create an IsingDynamics instance.
    
    Args:
        graph: The network topology.
        temperature: Thermal energy kT.
        seed: Random seed for initialization.
    
    Returns:
        IsingDynamics instance.
    """
    return IsingDynamics(graph, temperature=temperature, seed=seed)
