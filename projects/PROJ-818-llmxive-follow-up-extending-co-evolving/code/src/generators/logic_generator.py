import random
import json
import os
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from sympy import symbols, Implies, And, Or, Not, simplify_logic, Symbol, Eq
from sympy.logic.boolalg import BooleanFunction

logger = logging.getLogger(__name__)

class LogicGenerationError(Exception):
    """Custom exception for logic generation failures."""
    pass

class LogicProofGenerator:
    """
    Generates valid propositional logic proofs using sympy.
    Implements bounded retry logic for invalid generations.
    """

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.symbol_counter = 0
        self._symbol_pool: List[Symbol] = []

    def _get_symbol(self, name_base: str = "p") -> Symbol:
        """Get or create a new unique symbol."""
        if not self._symbol_pool:
            # Pre-generate a pool of symbols to ensure consistency within a run
            # We create enough for the max expected usage in a single proof
            self._symbol_pool = [Symbol(f"{name_base}{i}") for i in range(20)]
        return self._symbol_pool.pop()

    def _restore_symbol(self, sym: Symbol):
        """Return a symbol to the pool for reuse."""
        self._symbol_pool.append(sym)

    def _generate_random_axiom_set(self, num_axioms: int = 3, num_vars: int = 3) -> Tuple[List[Symbol], List[BooleanFunction]]:
        """Generate a set of random axioms involving a subset of variables."""
        vars_list = [self._get_symbol(f"p{i}") for i in range(num_vars)]
        
        axioms = []
        # Create a mix of simple implications and conjunctions
        for i in range(num_axioms):
            if i == 0:
                # First axiom is often a simple implication to start the chain
                p = random.choice(vars_list)
                q = random.choice([v for v in vars_list if v != p])
                axioms.append(Implies(p, q))
            elif i == 1 and num_axioms > 1:
                # Second axiom connects back or adds complexity
                p = random.choice(vars_list)
                q = random.choice([v for v in vars_list if v != p])
                axioms.append(And(p, q))
            else:
                # Random boolean expression
                p = random.choice(vars_list)
                q = random.choice([v for v in vars_list if v != p])
                r = random.choice([v for v in vars_list if v != p and v != q])
                expr_type = random.randint(0, 3)
                if expr_type == 0:
                    axioms.append(Implies(p, q))
                elif expr_type == 1:
                    axioms.append(Or(p, Not(q)))
                elif expr_type == 2:
                    axioms.append(And(p, Implies(q, r)))
                else:
                    axioms.append(Implies(And(p, q), r))
        
        return vars_list, axioms

    def _generate_consequent(self, vars_list: List[Symbol], axioms: List[BooleanFunction]) -> Optional[BooleanFunction]:
        """
        Generate a valid consequent derived from axioms.
        We use a simple forward-chaining approach on a subset of axioms.
        """
        if not axioms:
            return None

        # Try to find a chain: A -> B, B -> C, therefore A -> C
        # Or A, A -> B, therefore B
        
        # Strategy: Pick a random variable as the start, try to derive a target
        start_var = random.choice(vars_list)
        
        # Simple derivation: If we have (A & B) -> C, and we have A and B, then C.
        # Or if we have A -> B, and A, then B.
        
        # Let's try a specific pattern:
        # 1. Find an implication P -> Q
        # 2. Find P in axioms (or a conjunction containing P)
        # 3. Conclude Q
        
        for axiom in axioms:
            if isinstance(axiom, Implies):
                antecedent = axiom.args[0]
                consequent = axiom.args[1]
                
                # Case 1: Antecedent is a single symbol present as a standalone axiom or part of a conjunction
                if isinstance(antecedent, Symbol):
                    # Check if antecedent is in axioms
                    if antecedent in axioms:
                        return consequent
                    # Check if antecedent is part of a conjunction in axioms
                    for other_axiom in axioms:
                        if isinstance(other_axiom, And) and antecedent in other_axiom.args:
                            return consequent
                
                # Case 2: Antecedent is a conjunction
                if isinstance(antecedent, And):
                    required_vars = set(antecedent.args)
                    available_vars = set()
                    for other_axiom in axioms:
                        if other_axiom == antecedent:
                            return consequent
                        if isinstance(other_axiom, And):
                            available_vars.update(other_axiom.args)
                        elif isinstance(other_axiom, Symbol):
                            available_vars.add(other_axiom)
                    
                    if required_vars.issubset(available_vars):
                        return consequent

        # Fallback: If no complex derivation found, try a simple tautology check on a random subset
        # This is less "derived" but valid if we construct the proof statement carefully.
        # Instead, let's construct a proof where we assert the axioms imply the conclusion.
        # We'll pick a random subset of axioms and see if their conjunction implies a random variable.
        # This is risky for "validity" without a solver, so we stick to the constructive method above.
        
        # If we can't find a natural deduction, we construct a trivial one:
        # If we have P, then P v Q.
        for axiom in axioms:
            if isinstance(axiom, Symbol):
                return Or(axiom, random.choice([s for s in vars_list if s != axiom]))
        
        return None

    def generate_proof(self, max_vars: int = 4, max_axioms: int = 4) -> Dict[str, Any]:
        """
        Generate a single valid logic proof instance.
        Returns a dictionary with 'axioms', 'consequent', 'proof_steps'.
        """
        vars_list, axioms = self._generate_random_axiom_set(num_axioms=max_axioms, num_vars=max_vars)
        consequent = self._generate_consequent(vars_list, axioms)
        
        if consequent is None:
            # Fallback: construct a trivial valid proof
            # A, (A -> B) |- B
            p = self._get_symbol("p")
            q = self._get_symbol("q")
            # Reset pool to avoid duplicates if we reuse symbols, but for now just return
            self._restore_symbol(p)
            self._restore_symbol(q)
            
            # Construct specific valid case
            axiom1 = p
            axiom2 = Implies(p, q)
            consequent = q
            axioms = [axiom1, axiom2]
            vars_list = [p, q]

        # Reconstruct proof steps for clarity
        proof_steps = []
        proof_steps.append({"step": 1, "formula": str(axioms[0]), "reason": "Premise"})
        proof_steps.append({"step": 2, "formula": str(axioms[1]), "reason": "Premise"})
        
        if len(axioms) > 2:
            for i, axiom in enumerate(axioms[2:], start=3):
                proof_steps.append({"step": i, "formula": str(axiom), "reason": "Premise"})

        # Deduction step
        proof_steps.append({
            "step": len(proof_steps) + 1,
            "formula": str(consequent),
            "reason": "Modus Ponens / Simplification from previous steps"
        })

        # Verify validity using sympy
        # Construct the implication: (A1 & A2 & ... & An) -> C
        conjunction = axioms[0]
        for axiom in axioms[1:]:
            conjunction = And(conjunction, axiom)
        
        implication = Implies(conjunction, consequent)
        
        # Check if the implication is a tautology
        # sympy's simplify_logic might not directly say "tautology" for all forms,
        # but we can check if it's equivalent to True or if the negation is unsatisfiable.
        # A simpler check for validity in this context:
        # If we constructed it via Modus Ponens, it should be valid.
        # Let's double check with a truth table check if possible or simplify.
        
        try:
            # Check if the implication is a tautology
            # We can check if the negation is unsatisfiable or if it simplifies to True
            # However, simplify_logic on implications can be tricky.
            # A robust check: check if the implication is True for all assignments?
            # For small n, we can iterate, but sympy has `is_tautology` in some versions or via satisfiability.
            # Let's use `simplify_logic` to see if it reduces to True.
            simplified = simplify_logic(implication)
            if simplified is not True:
                # If it doesn't simplify to True, it might still be a tautology in a different form.
                # But for our constructive method, it should be.
                # If it fails, we mark it invalid.
                return None 
        except Exception:
            return None

        return {
            "id": f"proof_{random.randint(10000, 99999)}",
            "domain": "propositional_logic",
            "rule_set_id": "implication_chain",
            "instance_data": {
                "axioms": [str(a) for a in axioms],
                "consequent": str(consequent),
                "proof_steps": proof_steps,
                "variables": [str(v) for v in vars_list]
            }
        }

    def generate_proofs_with_retry(self, count: int, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Generate `count` valid proofs with bounded retry logic.
        If a proof fails validation after max_retries, it is skipped and a warning is logged.
        """
        proofs = []
        failed_instances = []

        for i in range(count):
            attempt = 0
            proof = None
            while attempt < max_retries:
                try:
                    proof = self.generate_proof()
                    if proof is not None:
                        break
                except Exception as e:
                    logger.warning(f"Generation attempt {attempt + 1} failed with exception: {e}")
                
                attempt += 1
                if attempt < max_retries:
                    # Reset symbol pool for fresh attempt to avoid state pollution
                    self._symbol_pool = []

            if proof:
                proofs.append(proof)
            else:
                logger.warning(f"Retry limit reached for instance {i}. Skipping.")
                failed_instances.append(i)

        if failed_instances:
            logger.warning(f"Skipped {len(failed_instances)} instances due to generation failures.")

        return proofs

def main():
    """Main entry point for the logic generator script."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Generate propositional logic proofs.")
    parser.add_argument("--count", type=int, default=10, help="Number of proofs to generate.")
    parser.add_argument("--output", type=str, default="data/generated_proofs.json", help="Output file path.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    parser.add_argument("--max-retries", type=int, default=3, help="Max retry attempts per instance.")
    
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    generator = LogicProofGenerator(seed=args.seed)
    proofs = generator.generate_proofs_with_retry(args.count, max_retries=args.max_retries)

    if not proofs:
        logger.error("No valid proofs were generated.")
        sys.exit(1)

    with open(output_path, 'w') as f:
        json.dump(proofs, f, indent=2)

    logger.info(f"Successfully generated {len(proofs)} proofs to {output_path}")

if __name__ == "__main__":
    main()
