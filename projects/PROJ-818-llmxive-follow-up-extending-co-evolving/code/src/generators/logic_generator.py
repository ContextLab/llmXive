"""
Propositional Logic Proof Generator for Co-Evolving Policy Distillation.

Generates valid propositional logic proofs from parameterized axioms using sympy.
"""
import random
import json
import os
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from sympy import symbols, Implies, And, Or, Not, simplify_logic
from sympy.logic.boolalg import to_cnf, to_dnf
from sympy.abc import A, B, C, D

class LogicGenerationError(Exception):
    """Raised when logic proof generation fails."""
    pass

class LogicProofGenerator:
    """
    Generates valid propositional logic proofs with distinct rule sets.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the logic proof generator.
        
        Args:
            config: Configuration dictionary with generation parameters.
        """
        self.config = config or {}
        self.seed = self.config.get('seed', 42)
        random.seed(self.seed)
    
    def generate_proof(
        self,
        num_vars: int = 3,
        min_depth: int = 2,
        max_depth: int = 5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a valid propositional logic proof.
        
        Args:
            num_vars: Number of propositional variables.
            min_depth: Minimum proof depth.
            max_depth: Maximum proof depth.
            seed: Random seed for reproducibility.
            
        Returns:
            Dictionary containing the proof instance.
        """
        if seed is not None:
            random.seed(seed)
        
        # Generate variables
        var_names = [chr(65 + i) for i in range(num_vars)]  # A, B, C, ...
        vars_list = symbols(var_names[:num_vars])
        
        # Create random axioms
        axioms = []
        depth = random.randint(min_depth, max_depth)
        
        for i in range(depth):
            if i == 0:
                # First axiom is a simple implication
                axioms.append(Implies(vars_list[0], vars_list[1]))
            else:
                # Subsequent axioms chain implications
                idx1 = random.randint(0, len(vars_list) - 1)
                idx2 = random.randint(0, len(vars_list) - 1)
                while idx1 == idx2:
                    idx2 = random.randint(0, len(vars_list) - 1)
                axioms.append(Implies(vars_list[idx1], vars_list[idx2]))
        
        # Create conclusion that follows from axioms
        # For simplicity, we create a chain and derive the final implication
        conclusion = axioms[0]
        for axiom in axioms[1:]:
            # Combine implications
            conclusion = Implies(And(*[a for a in axioms if a != axiom]), axiom.rhs)
        
        # Generate proof steps
        proof_steps = []
        current_state = axioms.copy()
        
        for i, axiom in enumerate(axioms):
            proof_steps.append({
                'step': i + 1,
                'rule': 'axiom',
                'statement': str(axiom),
                'justification': f'Given axiom {i+1}'
            })
        
        # Add derived steps
        if len(axioms) > 1:
            for i in range(1, len(axioms)):
                prev = proof_steps[-1]['statement']
                curr = str(axioms[i])
                proof_steps.append({
                    'step': len(proof_steps) + 1,
                    'rule': 'modus_ponens',
                    'statement': f'{prev} and {curr}',
                    'justification': f'Modus ponens from steps {len(proof_steps)} and {i+1}'
                })
        
        # Verify proof validity
        premises = axioms
        try:
            implication = Implies(And(*premises), conclusion)
            if simplify_logic(implication) != True:
                # Try to find a valid conclusion
                conclusion = axioms[-1].rhs
                implication = Implies(And(*premises), conclusion)
                if simplify_logic(implication) != True:
                    raise LogicGenerationError("Could not generate valid proof")
        except Exception as e:
            raise LogicGenerationError(f"Proof verification failed: {e}")
        
        return {
            'premises': [str(p) for p in premises],
            'conclusion': str(conclusion),
            'proof_steps': proof_steps,
            'num_variables': num_vars,
            'depth': depth,
            'valid': True
        }

    def generate_multiple_proofs(
        self,
        count: int,
        seed_offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple proof instances.
        
        Args:
            count: Number of proofs to generate.
            seed_offset: Offset for seed to ensure uniqueness.
            
        Returns:
            List of proof instances.
        """
        proofs = []
        for i in range(count):
            seed = self.seed + seed_offset + i
            try:
                proof = self.generate_proof(seed=seed)
                proofs.append(proof)
            except LogicGenerationError as e:
                print(f"Warning: Failed to generate proof {i}: {e}")
        return proofs


def main():
    """Main entry point for testing the logic generator."""
    print("Testing Logic Proof Generator...")
    
    generator = LogicProofGenerator({'seed': 42})
    
    # Generate a single proof
    proof = generator.generate_proof(num_vars=3, min_depth=2, max_depth=4)
    print(f"Generated proof with {len(proof['proof_steps'])} steps")
    print(f"Conclusion: {proof['conclusion']}")
    
    # Generate multiple proofs
    proofs = generator.generate_multiple_proofs(count=5, seed_offset=100)
    print(f"Generated {len(proofs)} proofs successfully")
    
    return proofs


if __name__ == "__main__":
    main()
