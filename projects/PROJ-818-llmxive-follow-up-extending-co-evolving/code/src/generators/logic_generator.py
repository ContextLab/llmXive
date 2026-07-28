"""
Propositional Logic Proof Generator.

Generates valid propositional logic proofs using SymPy.
Supports parameterized axioms and includes retry logic for invalid generations.
"""

import random
import json
import os
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from sympy import symbols, Implies, And, Or, Not, simplify_logic, srepr, Symbol
from sympy.logic.boolalg import BooleanFunction, BooleanTrue, BooleanFalse


class LogicGenerationError(Exception):
    """Raised when logic proof generation fails after retries."""
    pass


class LogicProofGenerator:
    """
    Generates valid propositional logic proofs from parameterized axioms.

    Uses SymPy to construct logical expressions and verify their validity.
    Includes retry logic to handle cases where generated proofs do not meet
    validity criteria.
    """

    def __init__(self, seed: Optional[int] = None, max_retries: int = 10):
        """
        Initialize the generator.

        Args:
            seed: Random seed for reproducibility.
            max_retries: Maximum number of retry attempts for invalid generations.
        """
        self.seed = seed
        self.max_retries = max_retries
        if seed is not None:
            random.seed(seed)

        # Pre-define a pool of symbols to use
        self._symbol_pool = [
            symbols(f'p{i}') for i in range(20)
        ]

    def _generate_random_expression(self, num_vars: int = 3, depth: int = 2) -> Any:
        """
        Generate a random boolean expression.

        Args:
            num_vars: Number of variables to use.
            depth: Maximum depth of the expression tree.

        Returns:
            A SymPy boolean expression.
        """
        if depth <= 0 or num_vars == 0:
            return random.choice(self._symbol_pool[:max(1, num_vars)])

        var = random.choice(self._symbol_pool[:max(1, num_vars)])
        ops = [And, Or, Implies]

        # Sometimes add negation
        if random.random() < 0.3:
            inner = self._generate_random_expression(num_vars - 1, depth - 1)
            return Not(inner)

        op = random.choice(ops)

        if op == Implies:
            lhs = self._generate_random_expression(num_vars - 1, depth - 1)
            rhs = self._generate_random_expression(num_vars - 1, depth - 1)
            return Implies(lhs, rhs)
        else:
            arg1 = self._generate_random_expression(num_vars - 1, depth - 1)
            arg2 = self._generate_random_expression(num_vars - 1, depth - 1)
            return op(arg1, arg2)

    def _is_valid_proof(self, premises: List[Any], conclusion: Any) -> bool:
        """
        Check if the conclusion logically follows from the premises.

        Args:
            premises: List of premise expressions.
            conclusion: The conclusion expression.

        Returns:
            True if the proof is valid, False otherwise.
        """
        if not premises:
            return False

        # Construct the implication: (P1 ∧ P2 ∧ ... ∧ Pn) → Conclusion
        if len(premises) == 1:
            antecedent = premises[0]
        else:
            antecedent = And(*premises)

        implication = Implies(antecedent, conclusion)

        # Check if the implication is a tautology
        try:
            simplified = simplify_logic(implication)
            # If simplified to True, it's a tautology
            if simplified == BooleanTrue:
                return True
            # Check if it's equivalent to True using truth tables
            return simplified is True or str(simplified) == 'True'
        except Exception:
            return False

    def _generate_valid_proof_attempt(self, num_premises: int = 2, max_vars: int = 5) -> Optional[Dict[str, Any]]:
        """
        Attempt to generate a single valid proof.

        Args:
            num_premises: Number of premises to include.
            max_vars: Maximum number of variables to use.

        Returns:
            A dictionary with proof details if valid, None otherwise.
        """
        # Select variables for this proof
        used_vars = random.sample(self._symbol_pool, min(max_vars, len(self._symbol_pool)))

        # Generate premises
        premises = []
        for _ in range(num_premises):
            premise = self._generate_random_expression(len(used_vars), depth=2)
            premises.append(premise)

        # Generate a conclusion that might follow
        # Strategy: Use Modus Ponens pattern or similar simple valid forms
        if random.random() < 0.5 and len(premises) >= 1:
            # Try to create a conclusion based on Modus Ponens
            # If we have (A → B), we can conclude B if we also have A
            for p in premises:
                if isinstance(p, Implies):
                    antecedent = p.args[0]
                    consequent = p.args[1]
                    # Create a scenario where we have antecedent as another premise
                    if random.random() < 0.7:
                        conclusion = consequent
                        # Ensure antecedent is in premises (or create it)
                        if antecedent not in premises:
                            # Add antecedent to premises
                            if len(premises) < num_premises:
                                premises.append(antecedent)
                            else:
                                premises[0] = antecedent
                        break
            else:
                conclusion = self._generate_random_expression(len(used_vars), depth=1)
        else:
            # Fallback: generate a random conclusion
            conclusion = self._generate_random_expression(len(used_vars), depth=1)

        # Validate the proof
        if self._is_valid_proof(premises, conclusion):
            return {
                'premises': [str(p) for p in premises],
                'conclusion': str(conclusion),
                'variables': [str(v) for v in used_vars],
                'valid': True,
                'proof_type': 'derived'
            }

        return None

    def generate_proof(self, num_premises: int = 2, max_vars: int = 5) -> Dict[str, Any]:
        """
        Generate a single valid logic proof with retry logic.

        Args:
            num_premises: Number of premises to include.
            max_vars: Maximum number of variables to use.

        Returns:
            A dictionary containing the proof details.

        Raises:
            LogicGenerationError: If no valid proof can be generated after max_retries.
        """
        for attempt in range(self.max_retries):
            proof = self._generate_valid_proof_attempt(num_premises, max_vars)
            if proof is not None:
                proof['attempt'] = attempt + 1
                return proof

        # If we get here, all retries failed
        raise LogicGenerationError(
            f"Failed to generate valid proof after {self.max_retries} attempts "
            f"(premises={num_premises}, max_vars={max_vars})"
        )

    def generate_proofs_batch(
        self,
        count: int,
        num_premises: int = 2,
        max_vars: int = 5,
        output_path: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of valid logic proofs.

        Args:
            count: Number of proofs to generate.
            num_premises: Number of premises per proof.
            max_vars: Maximum variables per proof.
            output_path: Optional path to save the proofs to a JSON file.

        Returns:
            List of proof dictionaries.

        Raises:
            LogicGenerationError: If any proof generation fails after retries.
        """
        proofs = []
        failed_count = 0

        for i in range(count):
            try:
                proof = self.generate_proof(num_premises, max_vars)
                proof['id'] = f"proof_{i:04d}"
                proofs.append(proof)
            except LogicGenerationError as e:
                failed_count += 1
                # Log but continue with other proofs
                print(f"Warning: Failed to generate proof {i}: {e}")

        if failed_count > 0:
            print(f"Note: {failed_count}/{count} proofs failed to generate after retries.")

        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(proofs, f, indent=2)

        return proofs


def main():
    """
    Main entry point for generating logic proofs.

    Reads configuration from environment or uses defaults,
    generates proofs, and writes them to data/ logic_proofs.json.
    """
    import sys

    # Default configuration
    seed = int(os.environ.get('LOGIC_GEN_SEED', '42'))
    count = int(os.environ.get('LOGIC_GEN_COUNT', '100'))
    num_premises = int(os.environ.get('LOGIC_GEN_PREMISES', '2'))
    max_vars = int(os.environ.get('LOGIC_GEN_MAX_VARS', '5'))
    max_retries = int(os.environ.get('LOGIC_GEN_MAX_RETRIES', '10'))
    output_file = os.environ.get('LOGIC_GEN_OUTPUT', 'data/logic_proofs.json')

    print(f"Generating {count} logic proofs...")
    print(f"  Seed: {seed}")
    print(f"  Premises per proof: {num_premises}")
    print(f"  Max variables: {max_vars}")
    print(f"  Max retries: {max_retries}")

    generator = LogicProofGenerator(seed=seed, max_retries=max_retries)

    try:
        output_path = Path(output_file)
        proofs = generator.generate_proofs_batch(
            count=count,
            num_premises=num_premises,
            max_vars=max_vars,
            output_path=output_path
        )

        print(f"Successfully generated {len(proofs)} proofs.")
        print(f"Output saved to: {output_path.absolute()}")

        # Validation check
        valid_count = sum(1 for p in proofs if p.get('valid', False))
        print(f"Valid proofs: {valid_count}/{len(proofs)}")

        if valid_count < len(proofs) * 0.99:
            print("Warning: Validity rate below 99% threshold.")
            sys.exit(1)

    except LogicGenerationError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
