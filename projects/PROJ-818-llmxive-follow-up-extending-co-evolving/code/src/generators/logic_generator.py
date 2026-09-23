"""
Propositional logic proof generator using sympy.
Implements T011: Generate valid proofs from parameterized axioms.
"""
import random
import json
import os
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from sympy import simplify_logic, symbols, Implies, And, Or, Not, Symbol
from sympy.logic.boolalg import to_cnf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogicGenerationError(Exception):
    """Custom exception for logic generation failures."""
    pass

class LogicProofGenerator:
    """Generates valid propositional logic proofs."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.symbol_counter = 0
        self.axiom_templates = [
            # Modus Ponens: (A -> B), A |- B
            lambda A, B: (Implies(A, B), A, B),
            # Hypothetical Syllogism: (A -> B), (B -> C) |- (A -> C)
            lambda A, B, C: (Implies(A, B), Implies(B, C), Implies(A, C)),
            # Disjunctive Syllogism: (A v B), ~A |- B
            lambda A, B: (Or(A, B), Not(A), B),
            # Conjunction: A, B |- (A ^ B)
            lambda A, B: (A, B, And(A, B)),
        ]

    def _new_symbol(self, prefix: str = "P") -> Symbol:
        """Generate a new unique symbol."""
        sym = Symbol(f"{prefix}{self.symbol_counter}")
        self.symbol_counter += 1
        return sym

    def _reset_symbols(self):
        """Reset symbol counter for reproducibility."""
        self.symbol_counter = 0

    def generate_proof(self, seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a single valid logic proof.

        Args:
            seed: Optional seed for this specific generation.

        Returns:
            Dictionary with proof details.
        """
        if seed is not None:
            random.seed(seed)
        self._reset_symbols()

        # Select a random axiom template
        template = random.choice(self.axiom_templates)

        # Determine number of symbols needed
        num_symbols = template.__code__.co_argcount
        sym_args = [self._new_symbol() for _ in range(num_symbols)]

        # Generate premises and conclusion
        premises_and_conclusion = template(*sym_args)
        premises = premises_and_conclusion[:-1]
        conclusion = premises_and_conclusion[-1]

        # Verify validity (tautology check)
        # Construct implication: (Premise1 ^ Premise2 ^ ...) -> Conclusion
        if len(premises) == 1:
            implication = Implies(premises[0], conclusion)
        else:
            premise_conjunction = And(*premises)
            implication = Implies(premise_conjunction, conclusion)

        # Simplify and check if tautology
        simplified = simplify_logic(implication)
        # In sympy, a tautology simplifies to True
        is_valid = simplified is True or simplified == True

        if not is_valid:
            # Fallback: try to verify via CNF
            cnf = to_cnf(implication)
            # If CNF is a tautology, it should be True
            is_valid = cnf is True or cnf == True

        if not is_valid:
            raise LogicGenerationError("Generated proof is not valid.")

        return {
            "id": f"proof_{random.randint(10000, 99999)}",
            "domain": "logic",
            "rule_set_id": f"axiom_{template.__name__ if hasattr(template, '__name__') else 'template'}",
            "premises": [str(p) for p in premises],
            "conclusion": str(conclusion),
            "implication": str(implication),
            "is_valid": is_valid,
            "seed": seed
        }

    def generate_proofs(self, count: int, seed_start: int = 0) -> List[Dict[str, Any]]:
        """
        Generate multiple valid logic proofs.

        Args:
            count: Number of proofs to generate.
            seed_start: Starting seed offset.

        Returns:
            List of proof dictionaries.
        """
        proofs = []
        max_retries = 3

        for i in range(count):
            seed = seed_start + i
            attempts = 0
            success = False

            while attempts < max_retries and not success:
                try:
                    proof = self.generate_proof(seed=seed + attempts)
                    proofs.append(proof)
                    success = True
                except LogicGenerationError as e:
                    attempts += 1
                    if attempts == max_retries:
                        logger.warning(f"Retry limit reached for instance {i}: {e}")
                    # Skip this instance if retries exhausted
            if not success:
                logger.warning(f"Skipping instance {i} after {max_retries} failed attempts.")

        return proofs

def main():
    """CLI entry point for logic generation."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate logic proofs")
    parser.add_argument('--count', type=int, default=10, help='Number of proofs')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--output', type=str, default='data/generated_proofs.json', help='Output file')
    args = parser.parse_args()

    generator = LogicProofGenerator(seed=args.seed)
    proofs = generator.generate_proofs(count=args.count, seed_start=args.seed)

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(proofs, f, indent=2)

    logger.info(f"Generated {len(proofs)} proofs to {args.output}")

if __name__ == "__main__":
    main()
