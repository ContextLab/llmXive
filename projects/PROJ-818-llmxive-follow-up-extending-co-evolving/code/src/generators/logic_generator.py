"""
Propositional Logic Proof Generator

Generates valid propositional logic proofs using SymPy from parameterized axioms.
Includes retry logic for invalid generations to ensure data quality.
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
    Generates valid propositional logic proofs.

    Creates instances of the form:
    Premises: [A, A -> B, ...]
    Conclusion: B
    Proof: A valid derivation sequence or a logical equivalence check.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the generator.

        Args:
            seed: Random seed for reproducibility.
        """
        if seed is not None:
            random.seed(seed)
        self.symbol_counter = 0
        self._symbols: Dict[str, Symbol] = {}

    def _get_symbol(self, name: str = "p") -> Symbol:
        """Get or create a unique symbol."""
        key = f"{name}_{self.symbol_counter}"
        if key not in self._symbols:
            self._symbols[key] = symbols(key)
            self.symbol_counter += 1
        return self._symbols[key]

    def _reset_symbols(self):
        """Reset symbol state for a new generation batch."""
        self.symbol_counter = 0
        self._symbols = {}

    def _generate_axiom_set(self, complexity: int = 3) -> Tuple[List[Symbol], List[Any]]:
        """
        Generate a set of axioms (premises) and a conclusion.

        Args:
            complexity: Number of base propositions to use.

        Returns:
            Tuple of (list of premise expressions, conclusion expression)
        """
        # Create base symbols
        base_symbols = [self._get_symbol(f"p{i}") for i in range(complexity)]

        premises = []
        
        # Always include at least one atomic fact to anchor the proof
        if base_symbols:
            premises.append(base_symbols[0])

        # Generate implications and combinations
        for i in range(len(base_symbols) - 1):
            # Randomly choose a logical structure
            choice = random.choice(['imp', 'and', 'or'])
            
            if choice == 'imp' and i + 1 < len(base_symbols):
                # A -> B
                premises.append(Implies(base_symbols[i], base_symbols[i+1]))
            elif choice == 'and' and i + 2 < len(base_symbols):
                # A & B
                premises.append(And(base_symbols[i], base_symbols[i+1]))
            elif choice == 'or' and i + 1 < len(base_symbols):
                # A | B
                premises.append(Or(base_symbols[i], base_symbols[i+1]))

        # The conclusion should be derivable from premises
        # We construct it by simplifying the conjunction of premises
        if premises:
            combined = premises[0]
            for p in premises[1:]:
                combined = And(combined, p)
            # The conclusion is a simplified form of the premises
            conclusion = simplify_logic(combined)
        else:
            conclusion = base_symbols[0] if base_symbols else BooleanTrue()

        return premises, conclusion

    def _is_valid_proof(self, premises: List[Any], conclusion: Any) -> bool:
        """
        Verify that the conclusion logically follows from the premises.

        Uses SymPy's simplification to check if (Premises => Conclusion) is a tautology.
        """
        if not premises:
            return False

        # Combine premises
        premises_conjunction = premises[0]
        for p in premises[1:]:
            premises_conjunction = And(premises_conjunction, p)

        # Check if (Premises -> Conclusion) is a tautology
        implication = Implies(premises_conjunction, conclusion)
        simplified = simplify_logic(implication)

        # A valid proof results in a tautology (True)
        return simplified == BooleanTrue()

    def generate_proof(self, max_retries: int = 10) -> Dict[str, Any]:
        """
        Generate a valid logic proof with retry logic.

        Args:
            max_retries: Maximum number of attempts to generate a valid proof.

        Returns:
            Dictionary containing premises, conclusion, and validity status.

        Raises:
            LogicGenerationError: If no valid proof can be generated after retries.
        """
        self._reset_symbols()
        
        for attempt in range(max_retries):
            try:
                # Generate random complexity between 2 and 5
                complexity = random.randint(2, 5)
                premises, conclusion = self._generate_axiom_set(complexity)

                if self._is_valid_proof(premises, conclusion):
                    return {
                        "premises": [srepr(p) for p in premises],
                        "conclusion": srepr(conclusion),
                        "valid": True,
                        "attempt": attempt + 1,
                        "num_symbols": len(self._symbols)
                    }
            except Exception:
                # Retry on any generation error
                continue

        raise LogicGenerationError(
            f"Failed to generate a valid logic proof after {max_retries} retries"
        )

    def generate_dataset(self, count: int, output_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate a dataset of valid logic proofs.

        Args:
            count: Number of proofs to generate.
            output_path: Optional path to save the dataset as JSON.

        Returns:
            List of proof dictionaries.
        """
        proofs = []
        for i in range(count):
            proof = self.generate_proof(max_retries=10)
            proof["id"] = f"proof_{i:04d}"
            proofs.append(proof)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(proofs, f, indent=2)

        return proofs


def main():
    """Entry point for generating logic proof datasets."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate propositional logic proofs")
    parser.add_argument("--count", type=int, default=100, help="Number of proofs to generate")
    parser.add_argument("--output", type=str, default="data/logic_proofs.json", help="Output file path")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()

    generator = LogicProofGenerator(seed=args.seed)
    
    try:
        proofs = generator.generate_dataset(args.count, args.output)
        print(f"Generated {len(proofs)} valid logic proofs to {args.output}")
        
        # Validate a sample
        if proofs:
            sample = proofs[0]
            print(f"Sample proof ID: {sample['id']}")
            print(f"Validity: {sample['valid']}")
            print(f"Attempts: {sample['attempt']}")
            
    except LogicGenerationError as e:
        print(f"Generation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
