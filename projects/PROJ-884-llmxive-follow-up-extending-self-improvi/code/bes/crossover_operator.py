"""
Crossover Operator for Bidirectional Evolutionary Search.

This module implements the crossover operation which recombines candidate solutions
using the LLM (via the forward_step module) guided by symbolic sub-goals.
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from bes.forward_step import ForwardStep, ForwardStepResult, ForwardStepError

logger = logging.getLogger(__name__)


@dataclass
class CrossoverResult:
    """Result of a crossover operation."""
    parent_1_id: str
    parent_2_id: str
    offspring_ids: List[str]
    success: bool
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    llm_calls: int = 0


class CrossoverOperator:
    """
    Performs crossover between candidate solutions using LLM guidance.

    The crossover operator takes two parent solutions and attempts to recombine
    them into new offspring solutions. This recombination is guided by the
    forward_step module (LLM) and symbolic sub-goals.
    """

    def __init__(self, forward_step: ForwardStep, crossover_rate: float = 0.8):
        """
        Initialize the crossover operator.

        Args:
            forward_step: The ForwardStep instance to use for LLM-guided recombination.
            crossover_rate: Probability of performing crossover instead of copying.
        """
        self.forward_step = forward_step
        self.crossover_rate = crossover_rate
        self._call_count = 0

    def crossover(
        self,
        parent_1: Dict[str, Any],
        parent_2: Dict[str, Any],
        puzzle_constraints: Optional[List[str]] = None,
        sub_goals: Optional[List[str]] = None
    ) -> CrossoverResult:
        """
        Perform crossover between two parent solutions.

        This method attempts to recombine the two parent solutions into offspring
        solutions using the LLM (via forward_step) guided by symbolic sub-goals.

        Args:
            parent_1: First parent solution dictionary with at least 'id' and 'solution'.
            parent_2: Second parent solution dictionary with at least 'id' and 'solution'.
            puzzle_constraints: Optional list of puzzle constraints to guide recombination.
            sub_goals: Optional list of symbolic sub-goals to guide recombination.

        Returns:
            CrossoverResult containing the offspring IDs and operation metadata.
        """
        start_time = time.time()
        self._call_count += 1

        parent_1_id = parent_1.get('id', 'unknown_1')
        parent_2_id = parent_2.get('id', 'unknown_2')

        try:
            # Determine if we should perform crossover or just copy parents
            if random.random() > self.crossover_rate:
                logger.debug(f"Skipping crossover for {parent_1_id} and {parent_2_id}, copying parents")
                # Return parents as offspring (no crossover performed)
                offspring_ids = [parent_1_id, parent_2_id]
                duration = time.time() - start_time
                return CrossoverResult(
                    parent_1_id=parent_1_id,
                    parent_2_id=parent_2_id,
                    offspring_ids=offspring_ids,
                    success=True,
                    duration_seconds=duration,
                    llm_calls=0
                )

            # Prepare context for LLM-guided recombination
            context = {
                'parent_1': parent_1,
                'parent_2': parent_2,
                'constraints': puzzle_constraints or [],
                'sub_goals': sub_goals or []
            }

            # Use forward_step to guide recombination
            # The forward_step module is designed to generate new solutions based on
            # constraints and sub-goals. We'll use it to generate offspring by
            # combining information from both parents.
            recombination_prompt = self._build_recombination_prompt(context)

            logger.info(f"Performing crossover between {parent_1_id} and {parent_2_id}")

            # Call forward_step with the recombination prompt
            # Note: forward_step expects a puzzle instance and optional sub-goals
            # We'll create a synthetic puzzle instance that represents the recombination task
            synthetic_puzzle = {
                'id': f"crossover_{parent_1_id}_{parent_2_id}_{int(time.time())}",
                'constraints': puzzle_constraints or [],
                'initial_state': {
                    'parent_1_solution': parent_1.get('solution', ''),
                    'parent_2_solution': parent_2.get('solution', '')
                },
                'target_state': {},
                'metadata': {
                    'source': 'crossover',
                    'parent_1_id': parent_1_id,
                    'parent_2_id': parent_2_id
                }
            }

            # Use forward_step to generate offspring
            forward_result = self.forward_step.step(
                puzzle_instance=synthetic_puzzle,
                sub_goals=sub_goals,
                temperature=0.7,  # Higher temperature for creativity in crossover
                max_tokens=500
            )

            if not forward_result.success:
                raise ForwardStepError(f"Forward step failed: {forward_result.error_message}")

            # Extract offspring from forward step result
            offspring_solutions = forward_result.generated_solutions

            if not offspring_solutions:
                # If no solutions generated, fall back to simple crossover
                logger.warning(f"No offspring generated by LLM, using simple crossover")
                offspring_solutions = self._simple_crossover(parent_1, parent_2)

            # Create offspring records
            offspring_ids = []
            for i, solution in enumerate(offspring_solutions):
                offspring_id = f"offspring_{parent_1_id}_{parent_2_id}_{i}_{int(time.time()*1000)}"
                offspring_record = {
                    'id': offspring_id,
                    'solution': solution,
                    'parents': [parent_1_id, parent_2_id],
                    'generation': parent_1.get('generation', 0) + 1,
                    'metadata': {
                        'created_by': 'crossover',
                        'parent_1_id': parent_1_id,
                        'parent_2_id': parent_2_id,
                        'timestamp': time.time()
                    }
                }
                offspring_ids.append(offspring_id)

                # Store offspring in a way that the evolutionary loop can access
                # (This would typically be handled by the population manager)
                logger.debug(f"Created offspring {offspring_id} from crossover")

            duration = time.time() - start_time
            return CrossoverResult(
                parent_1_id=parent_1_id,
                parent_2_id=parent_2_id,
                offspring_ids=offspring_ids,
                success=True,
                duration_seconds=duration,
                llm_calls=1
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Crossover failed between {parent_1_id} and {parent_2_id}: {str(e)}")
            return CrossoverResult(
                parent_1_id=parent_1_id,
                parent_2_id=parent_2_id,
                offspring_ids=[],
                success=False,
                error_message=str(e),
                duration_seconds=duration,
                llm_calls=0
            )

    def _build_recombination_prompt(self, context: Dict[str, Any]) -> str:
        """
        Build a prompt for the LLM to guide recombination.

        Args:
            context: Dictionary containing parent solutions and constraints.

        Returns:
            A prompt string for the LLM.
        """
        prompt_parts = [
            "You are helping to recombine two solutions to create new, improved solutions.",
            "",
            "Parent 1 Solution:",
            context['parent_1'].get('solution', 'No solution provided'),
            "",
            "Parent 2 Solution:",
            context['parent_2'].get('solution', 'No solution provided'),
            "",
            "Constraints to satisfy:",
            "\n".join(f"- {c}" for c in context.get('constraints', [])) or "None specified",
            "",
            "Sub-goals to consider:",
            "\n".join(f"- {g}" for g in context.get('sub_goals', [])) or "None specified",
            "",
            "Task: Generate 1-3 new solutions that combine the strengths of both parents",
            "while satisfying the constraints and working towards the sub-goals.",
            "Each new solution should be a complete, valid solution.",
            "",
            "Output format: Provide each solution on a separate line, prefixed with 'Solution N:'"
        ]

        return "\n".join(prompt_parts)

    def _simple_crossover(
        self,
        parent_1: Dict[str, Any],
        parent_2: Dict[str, Any]
    ) -> List[str]:
        """
        Perform simple string-based crossover if LLM fails.

        Args:
            parent_1: First parent solution.
            parent_2: Second parent solution.

        Returns:
            List of offspring solution strings.
        """
        sol1 = parent_1.get('solution', '')
        sol2 = parent_2.get('solution', '')

        if not sol1 or not sol2:
            return [sol1 or sol2]

        # Simple single-point crossover
        split_point = len(sol1) // 2
        offspring1 = sol1[:split_point] + sol2[split_point:]
        offspring2 = sol2[:split_point] + sol1[split_point:]

        return [offspring1, offspring2]

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about crossover operations."""
        return {
            'total_crossover_attempts': self._call_count,
            'crossover_rate': self.crossover_rate
        }


def main():
    """
    Main function for testing the crossover operator.
    """
    import json
    from bes.forward_step import ForwardStep

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create a mock forward step for testing
    # In production, this would be a real ForwardStep instance
    class MockForwardStep(ForwardStep):
        def __init__(self):
            pass

        def step(self, puzzle_instance, sub_goals=None, temperature=0.7, max_tokens=500):
            # Mock implementation that returns a simple solution
            return ForwardStepResult(
                success=True,
                generated_solutions=[
                    f"Mock solution combining {puzzle_instance.get('initial_state', {}).get('parent_1_solution', '')}",
                    f"Mock solution combining {puzzle_instance.get('initial_state', {}).get('parent_2_solution', '')}"
                ],
                error_message=None,
                duration_seconds=0.1,
                tokens_used=50
            )

    # Create test parents
    parent_1 = {
        'id': 'parent_1',
        'solution': 'Solution A: Step 1, Step 2, Step 3',
        'generation': 0
    }

    parent_2 = {
        'id': 'parent_2',
        'solution': 'Solution B: Step X, Step Y, Step Z',
        'generation': 0
    }

    # Initialize crossover operator
    forward_step = MockForwardStep()
    crossover_op = CrossoverOperator(forward_step, crossover_rate=1.0)

    # Perform crossover
    result = crossover_op.crossover(
        parent_1,
        parent_2,
        puzzle_constraints=['Constraint 1', 'Constraint 2'],
        sub_goals=['Sub-goal A', 'Sub-goal B']
    )

    # Print results
    print(json.dumps({
        'success': result.success,
        'parent_1_id': result.parent_1_id,
        'parent_2_id': result.parent_2_id,
        'offspring_ids': result.offspring_ids,
        'error_message': result.error_message,
        'duration_seconds': result.duration_seconds,
        'llm_calls': result.llm_calls
    }, indent=2))


if __name__ == '__main__':
    main()