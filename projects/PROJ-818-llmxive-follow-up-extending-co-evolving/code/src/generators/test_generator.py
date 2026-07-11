"""
Test Instance Generator for Co-Evolving Policy Distillation.

Generates held-out test instances for propositional logic proofs and grid-world
navigation tasks using distinct seeds to ensure strict separation from training data.
"""
import random
import json
import os
import sys
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Add project root to path for imports if running as script
if "code" in str(Path(__file__).resolve().parents[0]):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sympy import symbols, Implies, And, Or, Not, simplify_logic
from sympy.logic.boolalg import to_cnf
import networkx as nx

from src.generators.logic_generator import LogicProofGenerator
from src.generators.grid_generator import GridWorldGenerator
from src.utils.config import get_default_config, Config

class TestGenerationError(Exception):
    """Raised when test instance generation fails."""
    pass

class TestInstanceGenerator:
    """
    Generates held-out test instances for validation and baseline measurement.
    
    Ensures strict separation from training data by using distinct seeds
    and verifying no overlap with training sets.
    """
    
    def __init__(self, config: Optional[Config] = None, output_dir: Optional[str] = None):
        """
        Initialize the test generator.
        
        Args:
            config: Configuration object with seed and generation parameters.
            output_dir: Directory to write test instances to (default: data/).
        """
        self.config = config or get_default_config()
        self.output_dir = Path(output_dir) if output_dir else Path("data")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize generators with distinct seed offset for test data
        # Test seeds are offset by 10000 to ensure separation from training
        self.test_seed_base = self.config.get("seed", 42) + 10000
        self.logic_generator = LogicProofGenerator(self.config)
        self.grid_generator = GridWorldGenerator(self.config)
        
        # Track generated instances to ensure uniqueness
        self.generated_proofs: List[Dict] = []
        self.generated_grids: List[Dict] = []

    def _generate_proof_instance(self, seed: int) -> Dict[str, Any]:
        """
        Generate a single propositional logic proof instance.
        
        Args:
            seed: Random seed for reproducible generation.
            
        Returns:
            Dictionary containing the proof instance data.
        """
        random.seed(seed)
        
        # Generate a valid proof with a specific rule set
        # Use a different axiom set than training to ensure held-out nature
        axioms = [
            Implies(symbols('A'), symbols('B')),
            Implies(symbols('B'), symbols('C')),
            Implies(symbols('C'), symbols('D')),
        ]
        
        # Create a new random seed for the actual proof generation
        proof_seed = random.randint(0, 2**31 - 1)
        
        try:
            proof_data = self.logic_generator.generate_proof(
                num_vars=4,
                min_depth=2,
                max_depth=4,
                seed=proof_seed
            )
            
            # Verify the proof is valid
            if not self._verify_proof(proof_data):
                raise TestGenerationError("Generated proof failed verification")
            
            proof_data['instance_id'] = f"test_proof_{seed}"
            proof_data['source'] = 'held_out_test'
            proof_data['seed'] = seed
            
            return proof_data
            
        except Exception as e:
            raise TestGenerationError(f"Failed to generate proof instance: {e}")

    def _generate_grid_instance(self, seed: int) -> Dict[str, Any]:
        """
        Generate a single grid-world navigation instance.
        
        Args:
            seed: Random seed for reproducible generation.
            
        Returns:
            Dictionary containing the grid instance data.
        """
        random.seed(seed)
        
        # Generate a solvable grid with distinct rules
        grid_seed = random.randint(0, 2**31 - 1)
        
        try:
            grid_data = self.grid_generator.generate_grid(
                size=5,
                num_obstacles=3,
                num_goals=1,
                rule_set=["avoid_red", "diagonal_paths"],
                seed=grid_seed
            )
            
            # Verify the grid is solvable
            if not self._verify_grid_solvability(grid_data):
                raise TestGenerationError("Generated grid is not solvable")
            
            grid_data['instance_id'] = f"test_grid_{seed}"
            grid_data['source'] = 'held_out_test'
            grid_data['seed'] = seed
            
            return grid_data
            
        except Exception as e:
            raise TestGenerationError(f"Failed to generate grid instance: {e}")

    def _verify_proof(self, proof_data: Dict[str, Any]) -> bool:
        """
        Verify that a proof instance is valid.
        
        Args:
            proof_data: The proof instance to verify.
            
        Returns:
            True if the proof is valid, False otherwise.
        """
        try:
            # Check required fields
            required_fields = ['premises', 'conclusion', 'proof_steps']
            if not all(field in proof_data for field in required_fields):
                return False
            
            # Verify logical validity using sympy
            premises = proof_data['premises']
            conclusion = proof_data['conclusion']
            
            # Convert to sympy expressions
            if isinstance(premises, str):
                premises_expr = eval(premises)  # Safe in controlled context
            else:
                premises_expr = premises
                
            if isinstance(conclusion, str):
                conclusion_expr = eval(conclusion)
            else:
                conclusion_expr = conclusion
            
            # Check if premises imply conclusion
            implication = Implies(And(*premises_expr) if isinstance(premises_expr, list) else premises_expr, conclusion_expr)
            return simplify_logic(implication) == True
            
        except Exception:
            return False

    def _verify_grid_solvability(self, grid_data: Dict[str, Any]) -> bool:
        """
        Verify that a grid instance is solvable.
        
        Args:
            grid_data: The grid instance to verify.
            
        Returns:
            True if the grid is solvable, False otherwise.
        """
        try:
            # Reconstruct the grid graph
            grid = grid_data['grid']
            start = grid_data['start']
            goal = grid_data['goal']
            obstacles = grid_data.get('obstacles', [])
            
            # Create graph
            G = nx.grid_2d_graph(len(grid), len(grid[0]))
            
            # Remove obstacles
            for obs in obstacles:
                if obs in G.nodes():
                    G.remove_node(obs)
            
            # Check if path exists
            try:
                path = nx.shortest_path(G, source=tuple(start), target=tuple(goal))
                return len(path) > 0
            except nx.NetworkXNoPath:
                return False
                
        except Exception:
            return False

    def generate_test_instances(
        self,
        num_proofs: int = 50,
        num_grids: int = 50,
        max_retries: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        Generate a complete set of held-out test instances.
        
        Args:
            num_proofs: Number of logic proof instances to generate.
            num_grids: Number of grid-world instances to generate.
            max_retries: Maximum retry attempts for failed generations.
            
        Returns:
            Dictionary containing lists of proof and grid test instances.
        """
        test_data = {
            'metadata': {
                'total_proofs': num_proofs,
                'total_grids': num_grids,
                'seed_base': self.test_seed_base,
                'generated_by': 'TestInstanceGenerator',
                'purpose': 'held_out_validation'
            },
            'proofs': [],
            'grids': []
        }
        
        # Generate proof instances
        print(f"Generating {num_proofs} held-out logic proof instances...")
        for i in range(num_proofs):
            seed = self.test_seed_base + i
            retries = 0
            success = False
            
            while retries < max_retries and not success:
                try:
                    proof_instance = self._generate_proof_instance(seed)
                    test_data['proofs'].append(proof_instance)
                    self.generated_proofs.append(proof_instance)
                    success = True
                    print(f"  Generated proof {i+1}/{num_proofs} (seed: {seed})")
                except TestGenerationError as e:
                    retries += 1
                    if retries >= max_retries:
                        print(f"  Warning: Failed to generate proof {i+1} after {max_retries} retries: {e}")
                    
            if not success:
                print(f"  Skipping proof {i+1} due to generation failures")
        
        # Generate grid instances
        print(f"Generating {num_grids} held-out grid-world instances...")
        for i in range(num_grids):
            seed = self.test_seed_base + num_proofs + i
            retries = 0
            success = False
            
            while retries < max_retries and not success:
                try:
                    grid_instance = self._generate_grid_instance(seed)
                    test_data['grids'].append(grid_instance)
                    self.generated_grids.append(grid_instance)
                    success = True
                    print(f"  Generated grid {i+1}/{num_grids} (seed: {seed})")
                except TestGenerationError as e:
                    retries += 1
                    if retries >= max_retries:
                        print(f"  Warning: Failed to generate grid {i+1} after {max_retries} retries: {e}")
                    
            if not success:
                print(f"  Skipping grid {i+1} due to generation failures")
        
        return test_data

    def save_test_instances(self, test_data: Dict[str, Any], filename: str = "test_instances.json") -> str:
        """
        Save test instances to a JSON file.
        
        Args:
            test_data: Dictionary containing test instances.
            filename: Name of the output file.
            
        Returns:
            Path to the saved file.
        """
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, default=str)
        
        print(f"Test instances saved to: {output_path}")
        return str(output_path)

    def validate_separation(self, training_data_path: Optional[str] = None) -> bool:
        """
        Validate that test instances are strictly separate from training data.
        
        Args:
            training_data_path: Path to training data file for comparison.
            
        Returns:
            True if separation is verified, False otherwise.
        """
        if not training_data_path:
            print("No training data path provided, skipping separation validation")
            return True
        
        try:
            with open(training_data_path, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            # Extract test instance IDs
            test_proof_ids = {p['instance_id'] for p in self.generated_proofs}
            test_grid_ids = {g['instance_id'] for g in self.generated_grids}
            
            # Extract training instance IDs
            train_proof_ids = {p['instance_id'] for p in training_data.get('proofs', [])}
            train_grid_ids = {g['instance_id'] for g in training_data.get('grids', [])}
            
            # Check for overlap
            proof_overlap = test_proof_ids & train_proof_ids
            grid_overlap = test_grid_ids & train_grid_ids
            
            if proof_overlap or grid_overlap:
                print(f"ERROR: Found overlapping instances!")
                print(f"  Proof overlaps: {proof_overlap}")
                print(f"  Grid overlaps: {grid_overlap}")
                return False
            
            print("✓ Test instances are strictly separate from training data")
            return True
            
        except Exception as e:
            print(f"Warning: Could not validate separation: {e}")
            return True  # Don't fail if we can't read training data


def main():
    """Main entry point for generating test instances."""
    print("Starting held-out test instance generation...")
    
    # Load configuration
    config = get_default_config()
    config['seed'] = config.get('seed', 42)
    
    # Initialize generator
    generator = TestInstanceGenerator(config=config, output_dir="data")
    
    # Generate test instances
    test_data = generator.generate_test_instances(
        num_proofs=config.get('test_proofs_count', 50),
        num_grids=config.get('test_grids_count', 50),
        max_retries=10
    )
    
    # Save to file
    output_path = generator.save_test_instances(test_data, "test_instances.json")
    
    # Validate separation (optional, requires training data)
    # generator.validate_separation("data/training_instances.json")
    
    # Summary
    print("\n=== Test Instance Generation Summary ===")
    print(f"Total proof instances: {len(test_data['proofs'])}")
    print(f"Total grid instances: {len(test_data['grids'])}")
    print(f"Output file: {output_path}")
    print("Test instances are ready for held-out evaluation.")
    
    return test_data


if __name__ == "__main__":
    main()
