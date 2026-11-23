"""
Mutation Operator for Bidirectional Evolutionary Search.

Applies mutations to candidate solutions based on symbolic sub-goals
while ensuring syntactic validity according to the defined grammar.
"""
import logging
import random
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

# Import from local project structure relative to code/ root
# The API surface indicates imports from 'code.dataset.grammar'
# We will use relative imports to ensure it works when run as a module in 'code'
try:
    from code.dataset.grammar import GrammarValidator, ConstraintType
except ImportError:
    # Fallback for direct script execution context if needed, though standard is module import
    from dataset.grammar import GrammarValidator, ConstraintType

logger = logging.getLogger(__name__)


@dataclass
class MutationResult:
    """Result of a mutation operation."""
    original_solution: str
    mutated_solution: str
    is_valid: bool
    mutation_type: str
    sub_goal_applied: Optional[str] = None
    error_message: Optional[str] = None
    grammar_validation_passed: bool = False


class MutationOperator:
    """
    Applies mutations to candidate solutions.

    Constraints:
    1. Mutations must be syntactically valid according to the grammar (T011a-curate).
    2. Mutations should be guided by symbolic sub-goals when available.
    """

    def __init__(self, grammar_validator: GrammarValidator, mutation_rate: float = 0.1):
        """
        Initialize the mutation operator.

        Args:
            grammar_validator: Validator instance to check syntactic correctness.
            mutation_rate: Probability of applying a mutation to a candidate.
        """
        self.grammar_validator = grammar_validator
        self.mutation_rate = mutation_rate
        self.logger = logging.getLogger(__name__)

    def apply_mutation(
        self,
        candidate_solution: str,
        sub_goals: Optional[List[str]] = None,
        seed: Optional[int] = None
    ) -> MutationResult:
        """
        Apply a mutation to a candidate solution.

        Args:
            candidate_solution: The original solution string.
            sub_goals: Optional list of symbolic sub-goals to guide mutation.
            seed: Optional random seed for reproducibility.

        Returns:
            MutationResult containing the mutated solution and validation status.
        """
        if seed is not None:
            random.seed(seed)

        # Check if we should mutate based on rate
        if random.random() > self.mutation_rate:
            return MutationResult(
                original_solution=candidate_solution,
                mutated_solution=candidate_solution,
                is_valid=True,
                mutation_type="NO_MUTATION",
                grammar_validation_passed=True
            )

        # Determine mutation strategy
        if sub_goals and len(sub_goals) > 0:
            mutation_type = "GOAL_GUIDED"
            # Prioritize mutations that address the first unmet sub-goal
            target_sub_goal = sub_goals[0]
        else:
            mutation_type = "RANDOM"
            target_sub_goal = None

        try:
            mutated_solution = self._perform_mutation(
                candidate_solution,
                mutation_type,
                target_sub_goal
            )
        except Exception as e:
            self.logger.error(f"Mutation failed: {e}")
            return MutationResult(
                original_solution=candidate_solution,
                mutated_solution=candidate_solution,
                is_valid=False,
                mutation_type=mutation_type,
                error_message=str(e),
                grammar_validation_passed=False
            )

        # Validate syntax against grammar
        is_valid, validation_msg = self.grammar_validator.validate(mutated_solution)

        if not is_valid:
            self.logger.warning(f"Mutation produced invalid syntax: {validation_msg}")
            # Attempt to recover or return original if invalid
            # For now, we return the invalid result to let the fitness evaluator reject it
            # or the loop handle the exclusion.
            return MutationResult(
                original_solution=candidate_solution,
                mutated_solution=mutated_solution,
                is_valid=False,
                mutation_type=mutation_type,
                sub_goal_applied=target_sub_goal,
                error_message=validation_msg,
                grammar_validation_passed=False
            )

        self.logger.debug(f"Mutation successful: {mutation_type}")
        return MutationResult(
            original_solution=candidate_solution,
            mutated_solution=mutated_solution,
            is_valid=True,
            mutation_type=mutation_type,
            sub_goal_applied=target_sub_goal,
            grammar_validation_passed=True
        )

    def _perform_mutation(
        self,
        solution: str,
        mutation_type: str,
        target_sub_goal: Optional[str]
    ) -> str:
        """
        Internal logic to perform the actual string mutation.

        Args:
            solution: The solution string to mutate.
            mutation_type: Type of mutation ('GOAL_GUIDED' or 'RANDOM').
            target_sub_goal: The sub-goal to address if guided.

        Returns:
            The mutated solution string.
        """
        # Basic strategy: identify tokens/segments and modify one.
        # Since the grammar defines the structure, we assume the solution
        # is a sequence of constraints or logical statements.
        # We will perform a simple token-level mutation for demonstration
        # that respects the grammar structure if the grammar validator
        # accepts the result.

        # Split into lines or tokens (assuming line-based constraints for now)
        lines = solution.strip().split('\n')
        if not lines:
            return solution

        # Select a line to mutate
        line_idx = random.randint(0, len(lines) - 1)
        original_line = lines[line_idx]

        # Generate mutation
        if mutation_type == "GOAL_GUIDED" and target_sub_goal:
            # Attempt to modify the line to better align with the sub-goal
            # This is a heuristic: we might append a constraint or modify an operator
            # Example: if sub_goal is "x > 5", and line is "x > 3", change to "x > 5"
            # For a generic implementation, we simulate a targeted edit.
            mutated_line = self._apply_goal_based_edit(original_line, target_sub_goal)
        else:
            # Random mutation: swap operators, change values, etc.
            mutated_line = self._apply_random_edit(original_line)

        lines[line_idx] = mutated_line
        return '\n'.join(lines)

    def _apply_random_edit(self, line: str) -> str:
        """Apply a random edit to a constraint line."""
        # Simple heuristic: replace a number with a nearby number
        # or swap a comparison operator.
        # This assumes the line contains numbers and operators.
        import re

        # Find numbers
        numbers = re.findall(r'\d+', line)
        if numbers:
            # Pick a random number and increment/decrement
            target_num = random.choice(numbers)
            idx = line.find(target_num)
            if idx != -1:
                # Try to modify the number
                try:
                    val = int(target_num)
                    # Bias towards small changes
                    delta = random.choice([-1, 1, -2, 2])
                    new_val = max(0, val + delta)
                    new_num = str(new_val)
                    # Replace only the first occurrence to avoid messing up multiple numbers
                    return line.replace(target_num, new_num, 1)
                except ValueError:
                    pass

        # If no numbers, try to swap operators (e.g., > to <)
        operators = ['>', '<', '>=', '<=', '==', '!=']
        for op in operators:
            if op in line:
                # Swap with a random other operator
                others = [o for o in operators if o != op]
                if others:
                    new_op = random.choice(others)
                    return line.replace(op, new_op, 1)

        # Fallback: append a random valid-looking token if grammar allows
        # This is risky without full grammar knowledge, so we just return original
        # if we can't find a safe edit.
        return line

    def _apply_goal_based_edit(self, line: str, sub_goal: str) -> str:
        """
        Attempt to edit a line to satisfy a sub-goal.

        This is a heuristic implementation. In a real system, this would
        parse the sub-goal and the line to perform a semantic edit.
        Here, we simulate by checking if the sub_goal string is "related"
        and attempting a simple substitution.
        """
        # Simple heuristic: if the sub_goal contains a number, try to match it
        import re
        goal_nums = re.findall(r'\d+', sub_goal)
        line_nums = re.findall(r'\d+', line)

        if goal_nums and line_nums:
            # Try to replace the last number in the line with the first number in the goal
            target_val = goal_nums[0]
            # Find the last number in the line
            last_num_match = re.finditer(r'\d+', line)
            last_num = None
            last_start = -1
            for m in last_num_match:
                last_num = m.group()
                last_start = m.start()

            if last_num and last_start != -1:
                # Replace only if it makes sense (e.g. not part of a variable name)
                # Simple check: ensure it's not immediately followed by a letter
                if last_start + len(last_num) >= len(line) or not line[last_start + len(last_num)].isalpha():
                    return line[:last_start] + target_val + line[last_start + len(last_num):]

        return line

    def main():
        """CLI entry point for testing the mutation operator."""
        import argparse
        import json

        parser = argparse.ArgumentParser(description="Test Mutation Operator")
        parser.add_argument("--input", type=str, required=True, help="Input solution string")
        parser.add_argument("--sub-goals", type=str, nargs="*", default=[], help="List of sub-goals")
        parser.add_argument("--seed", type=int, default=None, help="Random seed")
        args = parser.parse_args()

        # Initialize validator (using default rules)
        validator = GrammarValidator()
        operator = MutationOperator(validator, mutation_rate=1.0)  # Force mutation for testing

        result = operator.apply_mutation(
            args.input,
            sub_goals=args.sub_goals,
            seed=args.seed
        )

        print(json.dumps({
            "original": result.original_solution,
            "mutated": result.mutated_solution,
            "is_valid": result.is_valid,
            "mutation_type": result.mutation_type,
            "grammar_valid": result.grammar_validation_passed,
            "error": result.error_message
        }, indent=2))


if __name__ == "__main__":
    main()