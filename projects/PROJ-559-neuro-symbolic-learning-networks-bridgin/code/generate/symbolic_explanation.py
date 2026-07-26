"""
Symbolic Explanation Generator for Neuro-Symbolic Learning Networks.

This module implements a fixed rule-based engine to solve arithmetic and logic
problems found in ASSISTments 'algebra' and 'geometry' subsets. It generates
deterministic symbolic traces based on hand-coded mathematical rules, ensuring
the symbolic layer is distinct from neural approximation.

Rules Implemented:
- Commutativity: a + b = b + a, a * b = b * a
- Associativity: (a + b) + c = a + (b + c), (a * b) * c = a * (b * c)
- Distributive Property: a * (b + c) = a*b + a*c
- Identity Element: a + 0 = a, a * 1 = a

Output: JSON trace of rule applications.
"""

import json
import logging
import os
import re
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SymbolicRule:
    """Base class for symbolic transformation rules."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def applies(self, expression: str) -> bool:
        """Check if the rule applies to the given expression."""
        raise NotImplementedError

    def apply(self, expression: str) -> Tuple[str, str]:
        """Apply the rule and return (new_expression, explanation)."""
        raise NotImplementedError


class CommutativityRule(SymbolicRule):
    """Implements commutativity: a + b = b + a, a * b = b * a."""

    def __init__(self):
        super().__init__(
            "Commutativity",
            "Order of operands does not affect result for addition and multiplication."
        )
        # Patterns for commutative operations
        self.add_pattern = re.compile(r'^(-?\d+(?:\.\d+)?)\s*\+\s*(-?\d+(?:\.\d+)?)$')
        self.mul_pattern = re.compile(r'^(-?\d+(?:\.\d+)?)\s*\*\s*(-?\d+(?:\.\d+)?)$')

    def applies(self, expression: str) -> bool:
        expression = expression.strip()
        return bool(self.add_pattern.match(expression) or self.mul_pattern.match(expression))

    def apply(self, expression: str) -> Tuple[str, str]:
        expression = expression.strip()
        if self.add_pattern.match(expression):
            match = self.add_pattern.match(expression)
            a, b = match.group(1), match.group(2)
            return f"{b} + {a}", f"Applied commutativity of addition: {expression} -> {b} + {a}"
        elif self.mul_pattern.match(expression):
            match = self.mul_pattern.match(expression)
            a, b = match.group(1), match.group(2)
            return f"{b} * {a}", f"Applied commutativity of multiplication: {expression} -> {b} * {a}"
        raise ValueError(f"Commutativity rule does not apply to: {expression}")


class AssociativityRule(SymbolicRule):
    """Implements associativity: (a + b) + c = a + (b + c), etc."""

    def __init__(self):
        super().__init__(
            "Associativity",
            "Grouping of operands does not affect result for addition and multiplication."
        )
        # Patterns for associativity (left-associative to right-associative)
        self.add_pattern = re.compile(r'^\((-?\d+(?:\.\d+)?)\s*\+\s*(-?\d+(?:\.\d+)?)\)\s*\+\s*(-?\d+(?:\.\d+)?)$')
        self.mul_pattern = re.compile(r'^\((-?\d+(?:\.\d+)?)\s*\*\s*(-?\d+(?:\.\d+)?)\)\s*\*\s*(-?\d+(?:\.\d+)?)$')

    def applies(self, expression: str) -> bool:
        expression = expression.strip()
        return bool(self.add_pattern.match(expression) or self.mul_pattern.match(expression))

    def apply(self, expression: str) -> Tuple[str, str]:
        expression = expression.strip()
        if self.add_pattern.match(expression):
            match = self.add_pattern.match(expression)
            a, b, c = match.group(1), match.group(2), match.group(3)
            new_expr = f"{a} + ({b} + {c})"
            return new_expr, f"Applied associativity of addition: {expression} -> {new_expr}"
        elif self.mul_pattern.match(expression):
            match = self.mul_pattern.match(expression)
            a, b, c = match.group(1), match.group(2), match.group(3)
            new_expr = f"{a} * ({b} * {c})"
            return new_expr, f"Applied associativity of multiplication: {expression} -> {new_expr}"
        raise ValueError(f"Associativity rule does not apply to: {expression}")


class DistributiveRule(SymbolicRule):
    """Implements distributive property: a * (b + c) = a*b + a*c."""

    def __init__(self):
        super().__init__(
            "Distributive Property",
            "Multiplication distributes over addition: a * (b + c) = a*b + a*c"
        )
        # Pattern: a * (b + c)
        self.distrib_pattern = re.compile(r'^(-?\d+(?:\.\d+)?)\s*\*\s*\((-?\d+(?:\.\d+)?)\s*\+\s*(-?\d+(?:\.\d+)?)\)$')

    def applies(self, expression: str) -> bool:
        expression = expression.strip()
        return bool(self.distrib_pattern.match(expression))

    def apply(self, expression: str) -> Tuple[str, str]:
        expression = expression.strip()
        if self.distrib_pattern.match(expression):
            match = self.distrib_pattern.match(expression)
            a, b, c = match.group(1), match.group(2), match.group(3)
            new_expr = f"({a} * {b}) + ({a} * {c})"
            return new_expr, f"Applied distributive property: {expression} -> {new_expr}"
        raise ValueError(f"Distributive rule does not apply to: {expression}")


class IdentityElementRule(SymbolicRule):
    """Implements identity elements: a + 0 = a, a * 1 = a."""

    def __init__(self):
        super().__init__(
            "Identity Element",
            "Adding 0 or multiplying by 1 leaves the operand unchanged."
        )
        self.add_identity_pattern = re.compile(r'^(-?\d+(?:\.\d+)?)\s*\+\s*0$')
        self.mul_identity_pattern = re.compile(r'^(-?\d+(?:\.\d+)?)\s*\*\s*1$')

    def applies(self, expression: str) -> bool:
        expression = expression.strip()
        return bool(self.add_identity_pattern.match(expression) or self.mul_identity_pattern.match(expression))

    def apply(self, expression: str) -> Tuple[str, str]:
        expression = expression.strip()
        if self.add_identity_pattern.match(expression):
            match = self.add_identity_pattern.match(expression)
            a = match.group(1)
            return a, f"Applied identity of addition: {expression} -> {a}"
        elif self.mul_identity_pattern.match(expression):
            match = self.mul_identity_pattern.match(expression)
            a = match.group(1)
            return a, f"Applied identity of multiplication: {expression} -> {a}"
        raise ValueError(f"Identity rule does not apply to: {expression}")


class SymbolicSolver:
    """
    Symbolic solver that applies a sequence of deterministic rules to solve
    arithmetic and logic problems.
    """

    def __init__(self):
        self.rules: List[SymbolicRule] = [
            CommutativityRule(),
            AssociativityRule(),
            DistributiveRule(),
            IdentityElementRule()
        ]
        self.trace: List[Dict[str, Any]] = []

    def solve(self, problem_expression: str) -> Dict[str, Any]:
        """
        Solve a problem expression by applying rules step-by-step.

        Args:
            problem_expression: The mathematical expression to solve (e.g., "2 * (3 + 4)")

        Returns:
            Dictionary containing the final result and the full trace of rule applications.
        """
        self.trace = []
        current_expr = problem_expression.strip()
        steps = 0
        max_steps = 100  # Prevent infinite loops

        self.trace.append({
            "step": 0,
            "expression": current_expr,
            "rule_applied": "Initial State",
            "explanation": "Starting expression"
        })

        while steps < max_steps:
            applied = False
            for rule in self.rules:
                if rule.applies(current_expr):
                    new_expr, explanation = rule.apply(current_expr)
                    self.trace.append({
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
                # No more rules apply; we may have a final result or a simplified form
                break

        # If the expression is a simple number, we have our result
        try:
            result = float(current_expr)
            if result.is_integer():
                result = int(result)
        except ValueError:
            result = current_expr  # Keep as string if not a number

        return {
            "original_expression": problem_expression,
            "final_expression": current_expr,
            "result": result,
            "trace": self.trace,
            "steps_taken": steps
        }


def generate_symbolic_explanation(problem_id: str, problem_expression: str, problem_type: str) -> Dict[str, Any]:
    """
    Generate a symbolic explanation for a given problem.

    Args:
        problem_id: Unique identifier for the problem.
        problem_expression: The mathematical expression string.
        problem_type: Type of problem ('algebra', 'geometry', etc.).

    Returns:
        Dictionary containing the symbolic trace and metadata.
    """
    logger.info(f"Generating symbolic explanation for problem {problem_id} (type: {problem_type})")

    # Validate problem type support
    supported_types = ['algebra', 'geometry']
    if problem_type not in supported_types:
        logger.warning(f"Problem type '{problem_type}' not explicitly supported, attempting general arithmetic solve.")

    solver = SymbolicSolver()
    result = solver.solve(problem_expression)

    explanation_output = {
        "problem_id": problem_id,
        "problem_type": problem_type,
        "generator": "SymbolicRuleEngine",
        "is_synthetic": False,  # This is a rule-based engine, not synthetic data
        "result": result["result"],
        "trace": result["trace"],
        "rules_applied": [step["rule_applied"] for step in result["trace"] if step["rule_applied"] != "Initial State"]
    }

    logger.info(f"Symbolic explanation generated: {len(result['trace'])} steps")
    return explanation_output


def main():
    """
    Main entry point for testing the symbolic explanation generator.
    Demonstrates the engine with sample problems from ASSISTments subsets.
    """
    # Sample problems representing algebra and geometry subsets
    test_cases = [
        {
            "id": "ASSIST-ALG-001",
            "expression": "2 * (3 + 4)",
            "type": "algebra",
            "description": "Distributive property example"
        },
        {
            "id": "ASSIST-ALG-002",
            "expression": "5 + 0",
            "type": "algebra",
            "description": "Identity element example"
        },
        {
            "id": "ASSIST-ALG-003",
            "expression": "(2 + 3) + 4",
            "type": "algebra",
            "description": "Associativity example"
        },
        {
            "id": "ASSIST-ALG-004",
            "expression": "3 * 5",
            "type": "algebra",
            "description": "Commutativity example"
        },
        {
            "id": "ASSIST-GEOM-001",
            "expression": "1 * (2 + 3)",
            "type": "geometry",
            "description": "Area calculation with distributive property"
        }
    ]

    output_dir = "data/symbolic"
    os.makedirs(output_dir, exist_ok=True)

    all_results = []

    for case in test_cases:
        logger.info(f"Processing: {case['description']} ({case['id']})")
        try:
            result = generate_symbolic_explanation(
                case['id'],
                case['expression'],
                case['type']
            )
            all_results.append(result)

            # Save individual trace
            trace_path = os.path.join(output_dir, f"trace_{case['id']}.json")
            with open(trace_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            logger.info(f"Saved trace to {trace_path}")

        except Exception as e:
            logger.error(f"Failed to process {case['id']}: {e}")
            all_results.append({
                "problem_id": case['id'],
                "error": str(e)
            })

    # Save aggregate report
    report_path = os.path.join(output_dir, "symbolic_explanations_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"Aggregate report saved to {report_path}")

    print(f"\nSymbolic Explanation Generation Complete.")
    print(f"Processed {len(test_cases)} problems.")
    print(f"Results saved to {output_dir}/")

    return 0


if __name__ == "__main__":
    exit(main())
