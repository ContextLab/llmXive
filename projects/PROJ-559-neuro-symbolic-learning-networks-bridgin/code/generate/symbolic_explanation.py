"""
Symbolic Explanation Generator for Neuro-Symbolic Learning Networks.

Implements a fixed rule-based engine to solve arithmetic/logic problems
found in the ASSISTments subset. Generates a JSON trace of rule applications
(commutativity, associativity, distributive property, identity element).
"""
import json
import logging
import os
import re
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SymbolicRule:
    """Base class for symbolic rules."""
    name: str
    description: str

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def apply(self, expression: str) -> Optional[Tuple[str, str]]:
        """
        Apply rule to expression.
        Returns (new_expression, explanation) if applied, else None.
        """
        raise NotImplementedError


class CommutativityRule(SymbolicRule):
    """Rule for commutativity: a + b = b + a, a * b = b * a."""
    def __init__(self):
        super().__init__("commutativity", "Swap order of operands for + or *")

    def apply(self, expression: str) -> Optional[Tuple[str, str]]:
        # Match simple binary operations with space separators
        # Pattern: (operand) (operator) (operand)
        # We look for addition or multiplication
        pattern_add = r'^(-?\d+)\s*\+\s*(-?\d+)$'
        pattern_mul = r'^(-?\d+)\s*\*\s*(-?\d+)$'

        match = re.match(pattern_add, expression.strip())
        if match:
            a, b = match.group(1), match.group(2)
            if a != b:  # Only swap if operands are different
                return f"{b} + {a}", f"Applied commutativity: {a} + {b} = {b} + {a}"

        match = re.match(pattern_mul, expression.strip())
        if match:
            a, b = match.group(1), match.group(2)
            if a != b:
                return f"{b} * {a}", f"Applied commutativity: {a} * {b} = {b} * {a}"

        return None


class AssociativityRule(SymbolicRule):
    """Rule for associativity: (a + b) + c = a + (b + c), etc."""
    def __init__(self):
        super().__init__("associativity", "Re-group operands for + or *")

    def apply(self, expression: str) -> Optional[Tuple[str, str]]:
        # Simplified: handle (a + b) + c pattern
        pattern_left_add = r'^\((-?\d+)\s*\+\s*(-?\d+)\)\s*\+\s*(-?\d+)$'
        pattern_right_add = r'^(-?\d+)\s*\+\s*\((-?\d+)\s*\+\s*(-?\d+)\)$'

        match = re.match(pattern_left_add, expression.strip())
        if match:
            a, b, c = match.group(1), match.group(2), match.group(3)
            new_expr = f"{a} + ({b} + {c})"
            return new_expr, f"Applied associativity: ({a} + {b}) + {c} = {a} + ({b} + {c})"

        match = re.match(pattern_right_add, expression.strip())
        if match:
            a, b, c = match.group(1), match.group(2), match.group(3)
            new_expr = f"({a} + {b}) + {c}"
            return new_expr, f"Applied associativity: {a} + ({b} + {c}) = ({a} + {b}) + {c}"

        # Multiplication patterns
        pattern_left_mul = r'^\((-?\d+)\s*\*\s*(-?\d+)\)\s*\*\s*(-?\d+)$'
        pattern_right_mul = r'^(-?\d+)\s*\*\s*\((-?\d+)\s*\*\s*(-?\d+)\)$'

        match = re.match(pattern_left_mul, expression.strip())
        if match:
            a, b, c = match.group(1), match.group(2), match.group(3)
            new_expr = f"{a} * ({b} * {c})"
            return new_expr, f"Applied associativity: ({a} * {b}) * {c} = {a} * ({b} * {c})"

        match = re.match(pattern_right_mul, expression.strip())
        if match:
            a, b, c = match.group(1), match.group(2), match.group(3)
            new_expr = f"({a} * {b}) * {c}"
            return new_expr, f"Applied associativity: {a} * ({b} * {c}) = ({a} * {b}) * {c}"

        return None


class DistributiveRule(SymbolicRule):
    """Rule for distributivity: a * (b + c) = a * b + a * c."""
    def __init__(self):
        super().__init__("distributivity", "Distribute multiplication over addition")

    def apply(self, expression: str) -> Optional[Tuple[str, str]]:
        # Pattern: a * (b + c)
        pattern = r'^(-?\d+)\s*\*\s*\((-?\d+)\s*\+\s*(-?\d+)\)$'
        match = re.match(pattern, expression.strip())

        if match:
            a, b, c = match.group(1), match.group(2), match.group(3)
            new_expr = f"({a} * {b}) + ({a} * {c})"
            return new_expr, f"Applied distributivity: {a} * ({b} + {c}) = ({a} * {b}) + ({a} * {c})"

        # Pattern: (b + c) * a (commutative case)
        pattern_rev = r'^\((-?\d+)\s*\+\s*(-?\d+)\)\s*\*\s*(-?\d+)$'
        match = re.match(pattern_rev, expression.strip())

        if match:
            b, c, a = match.group(1), match.group(2), match.group(3)
            new_expr = f"({a} * {b}) + ({a} * {c})"
            return new_expr, f"Applied distributivity: ({b} + {c}) * {a} = ({a} * {b}) + ({a} * {c})"

        return None


class IdentityElementRule(SymbolicRule):
    """Rule for identity elements: a + 0 = a, a * 1 = a."""
    def __init__(self):
        super().__init__("identity_element", "Remove identity elements (0 for +, 1 for *)")

    def apply(self, expression: str) -> Optional[Tuple[str, str]]:
        # a + 0 = a
        pattern_add_zero_left = r'^0\s*\+\s*(-?\d+)$'
        pattern_add_zero_right = r'^(-?\d+)\s*\+\s*0$'

        match = re.match(pattern_add_zero_left, expression.strip())
        if match:
            a = match.group(1)
            return a, f"Applied identity: 0 + {a} = {a}"

        match = re.match(pattern_add_zero_right, expression.strip())
        if match:
            a = match.group(1)
            return a, f"Applied identity: {a} + 0 = {a}"

        # a * 1 = a
        pattern_mul_one_left = r'^1\s*\*\s*(-?\d+)$'
        pattern_mul_one_right = r'^(-?\d+)\s*\*\s*1$'

        match = re.match(pattern_mul_one_left, expression.strip())
        if match:
            a = match.group(1)
            return a, f"Applied identity: 1 * {a} = {a}"

        match = re.match(pattern_mul_one_right, expression.strip())
        if match:
            a = match.group(1)
            return a, f"Applied identity: {a} * 1 = {a}"

        return None


class SymbolicSolver:
    """
    Symbolic solver that applies rules to simplify arithmetic expressions.
    """
    def __init__(self):
        self.rules: List[SymbolicRule] = [
            CommutativityRule(),
            AssociativityRule(),
            DistributiveRule(),
            IdentityElementRule()
        ]
        self.max_steps = 20

    def solve(self, problem_id: str, expression: str) -> Dict[str, Any]:
        """
        Solve the expression using symbolic rules.
        Returns a trace of rule applications.
        """
        trace = []
        current_expr = expression.strip()
        steps = 0

        trace.append({
            "step": 0,
            "expression": current_expr,
            "rule_applied": None,
            "explanation": "Initial expression"
        })

        while steps < self.max_steps:
            applied = False
            for rule in self.rules:
                result = rule.apply(current_expr)
                if result:
                    new_expr, explanation = result
                    trace.append({
                        "step": steps + 1,
                        "expression": new_expr,
                        "rule_applied": rule.name,
                        "explanation": explanation
                    })
                    current_expr = new_expr
                    applied = True
                    steps += 1
                    break  # Apply one rule at a time

            if not applied:
                break

        # Final evaluation if it's a simple arithmetic expression
        try:
            # Safe evaluation of simple arithmetic
            final_value = eval(current_expr)
            trace.append({
                "step": steps + 1,
                "expression": str(final_value),
                "rule_applied": "evaluation",
                "explanation": f"Evaluated expression to {final_value}"
            })
        except Exception as e:
            logger.warning(f"Could not evaluate final expression '{current_expr}': {e}")

        return {
            "problem_id": problem_id,
            "original_expression": expression,
            "final_expression": current_expr,
            "final_value": final_value if 'final_value' in locals() else None,
            "trace": trace,
            "rules_applied_count": len([t for t in trace if t["rule_applied"] != "evaluation" and t["rule_applied"] is not None])
        }


def generate_symbolic_explanation(problem_id: str, expression: str, output_path: str) -> Dict[str, Any]:
    """
    Generate a symbolic explanation for a given arithmetic problem.

    Args:
        problem_id: Unique identifier for the problem
        expression: Arithmetic expression string (e.g., "2 + 3 * 4")
        output_path: Path to save the JSON trace

    Returns:
        Dictionary containing the explanation trace
    """
    logger.info(f"Generating symbolic explanation for problem {problem_id}: {expression}")

    solver = SymbolicSolver()
    result = solver.solve(problem_id, expression)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write JSON trace
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Symbolic explanation saved to {output_path}")
    return result


def main():
    """
    Main entry point for testing the symbolic explanation generator.
    Reads problems from a sample input or generates test cases.
    """
    # Test cases based on ASSISTments-style arithmetic problems
    test_cases = [
        ("P001", "2 + 3"),
        ("P002", "5 * 1"),
        ("P003", "0 + 7"),
        ("P004", "2 * (3 + 4)"),
        ("P005", "(1 + 2) * 3"),
        ("P006", "4 + 5 + 6"),
        ("P007", "2 * 3 * 4"),
        ("P008", "10 * 1 + 0")
    ]

    output_dir = "data/symbolic_traces"
    os.makedirs(output_dir, exist_ok=True)

    all_results = []

    for problem_id, expression in test_cases:
        output_path = os.path.join(output_dir, f"trace_{problem_id}.json")
        result = generate_symbolic_explanation(problem_id, expression, output_path)
        all_results.append(result)

    # Save aggregate summary
    summary_path = os.path.join(output_dir, "symbolic_explanations_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Generated {len(all_results)} symbolic explanations")
    logger.info(f"Summary saved to {summary_path}")

    return all_results


if __name__ == "__main__":
    main()
