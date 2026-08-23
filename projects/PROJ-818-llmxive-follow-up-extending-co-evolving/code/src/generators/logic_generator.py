"""
Propositional Logic Proof Generator using SymPy.
Generates valid proofs from parameterized axioms with retry logic.
"""
import random
import json
import os
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from sympy import symbols, Implies, And, Or, Not, simplify_logic, srepr, Symbol
from sympy.logic.boolalg import BooleanFunction

class LogicGenerationError(Exception):
    """Raised when logic proof generation fails."""
    pass

class LogicProofGenerator:
    """Generates valid propositional logic proofs using SymPy."""

    def __init__(self, seed: Optional[int] = None, max_retries: int = 100):
        """
        Initialize the generator.

        Args:
            seed: Random seed for reproducibility.
            max_retries: Maximum number of retry attempts for invalid generations.
        """
        if seed is not None:
            random.seed(seed)
        self.max_retries = max_retries
        self._symbols_cache: Dict[str, Symbol] = {}

    def _get_symbol(self, name: str) -> Symbol:
        """Get or create a cached SymPy Symbol."""
        if name not in self._symbols_cache:
            self._symbols_cache[name] = Symbol(name)
        return self._symbols_cache[name]

    def _generate_random_axiom(self, num_vars: int) -> Tuple[Symbol, ...]:
        """Generate a set of random propositional variables."""
        vars = []
        for i in range(num_vars):
            name = f"P{i}"
            vars.append(self._get_symbol(name))
        return tuple(vars)

    def _construct_random_formula(self, vars: Tuple[Symbol, ...], complexity: int = 3) -> Symbol:
        """
        Construct a random boolean formula from given variables.
        Supports complexity levels: 1 (simple), 2 (binary ops), 3 (nested).
        """
        if not vars:
            raise ValueError("At least one variable required")

        # Base case: return a random variable or its negation
        if complexity == 1:
            var = random.choice(vars)
            if random.random() < 0.3:
                return Not(var)
            return var

        # Binary operations
        op_choice = random.choice(['and', 'or', 'implies'])
        left = self._construct_random_formula(vars, complexity - 1)
        right = self._construct_random_formula(vars, complexity - 1)

        if op_choice == 'and':
            return And(left, right)
        elif op_choice == 'or':
            return Or(left, right)
        else:
            return Implies(left, right)

    def _generate_valid_proof_instance(self, num_vars: int = 3, complexity: int = 3) -> Optional[Dict[str, Any]]:
        """
        Generate a single valid proof instance.
        Returns a dictionary with premises, conclusion, and validity proof.
        """
        try:
            vars = self._generate_random_axiom(num_vars)

            # Generate a random premise (antecedent)
            premise = self._construct_random_formula(vars, complexity)

            # Generate a random conclusion (consequent)
            # To ensure validity, we'll construct the conclusion based on the premise
            # or generate a random one and check validity
            conclusion = self._construct_random_formula(vars, complexity)

            # Create the implication: premise -> conclusion
            implication = Implies(premise, conclusion)

            # Simplify to check if it's a tautology (always true)
            # A valid proof requires that (premise -> conclusion) is a tautology
            simplified = simplify_logic(implication, force=True)

            # Check if it's a tautology (simplified to True)
            if simplified is True:
                return {
                    "premises": [srepr(premise)],
                    "conclusion": srepr(conclusion),
                    "implication": srepr(implication),
                    "is_valid": True,
                    "variables": [srepr(v) for v in vars]
                }
            else:
                # Try to construct a valid conclusion from the premise
                # A simple valid conclusion is the premise itself (identity)
                # Or we can use the premise as part of a valid implication
                valid_conclusion = premise
                valid_implication = Implies(premise, valid_conclusion)

                if simplify_logic(valid_implication, force=True) is True:
                    return {
                        "premises": [srepr(premise)],
                        "conclusion": srepr(valid_conclusion),
                        "implication": srepr(valid_implication),
                        "is_valid": True,
                        "variables": [srepr(v) for v in vars]
                    }

                # Try a few more combinations
                for _ in range(5):
                    # Try adding a tautological condition
                    tautology = Or(vars[0], Not(vars[0]))
                    new_premise = And(premise, tautology)
                    new_implication = Implies(new_premise, premise)

                    if simplify_logic(new_implication, force=True) is True:
                        return {
                            "premises": [srepr(new_premise)],
                            "conclusion": srepr(premise),
                            "implication": srepr(new_implication),
                            "is_valid": True,
                            "variables": [srepr(v) for v in vars]
                        }

                return None

        except Exception as e:
            raise LogicGenerationError(f"Failed to generate proof instance: {str(e)}")

    def generate_proofs(self, count: int, num_vars: int = 3, complexity: int = 3) -> List[Dict[str, Any]]:
        """
        Generate a list of valid proof instances.

        Args:
            count: Number of proofs to generate.
            num_vars: Number of propositional variables per proof.
            complexity: Complexity level of formulas (1-3).

        Returns:
            List of dictionaries containing proof data.

        Raises:
            LogicGenerationError: If unable to generate valid proofs after retries.
        """
        proofs = []
        retries_total = 0

        while len(proofs) < count:
            if retries_total >= self.max_retries:
                raise LogicGenerationError(
                    f"Failed to generate {count} valid proofs after {self.max_retries} retries. "
                    f"Generated {len(proofs)} valid proofs so far."
                )

            try:
                proof = self._generate_valid_proof_instance(num_vars, complexity)
                if proof:
                    proofs.append(proof)
                else:
                    retries_total += 1

            except LogicGenerationError:
                retries_total += 1
                if retries_total >= self.max_retries:
                    raise

        return proofs

    def save_proofs(self, proofs: List[Dict[str, Any]], output_path: str) -> None:
        """
        Save generated proofs to a JSON file.

        Args:
            proofs: List of proof dictionaries.
            output_path: Path to the output JSON file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "generator": "LogicProofGenerator",
                    "count": len(proofs),
                    "timestamp": str(Path(output_path).stat().st_mtime)
                },
                "proofs": proofs
            }, f, indent=2)

    def load_proofs(self, input_path: str) -> List[Dict[str, Any]]:
        """
        Load proofs from a JSON file.

        Args:
            input_path: Path to the input JSON file.

        Returns:
            List of proof dictionaries.
        """
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Proof file not found: {input_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("proofs", [])

def main():
    """Main entry point for standalone execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate propositional logic proofs")
    parser.add_argument("--count", type=int, default=100, help="Number of proofs to generate")
    parser.add_argument("--num-vars", type=int, default=3, help="Number of variables per proof")
    parser.add_argument("--complexity", type=int, default=3, help="Formula complexity (1-3)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/generated_proofs.json", help="Output file path")

    args = parser.parse_args()

    print(f"Generating {args.count} logic proofs...")
    generator = LogicProofGenerator(seed=args.seed)

    try:
        proofs = generator.generate_proofs(
            count=args.count,
            num_vars=args.num_vars,
            complexity=args.complexity
        )
        generator.save_proofs(proofs, args.output)
        print(f"Successfully generated and saved {len(proofs)} proofs to {args.output}")

    except LogicGenerationError as e:
        print(f"Generation failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
