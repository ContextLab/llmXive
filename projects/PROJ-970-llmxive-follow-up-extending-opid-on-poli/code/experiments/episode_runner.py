"""
Minimal placeholder for the EpisodeRunner used by the ExperimentRunner.

The real implementation is expected to provide a ``run`` method returning an
object with the attributes accessed in ``ExperimentRunner._run_single_episode``.
For the purposes of the profiling task and unit tests, a lightweight stub
implementation is sufficient.
"""

from dataclasses import dataclass
from typing import Any

@dataclass
class EpisodeRunnerConfig:
    state_graph: Any
    router: Any
    policy: Any
    max_steps: int = 1000

class EpisodeResult:
    """Simple container for episode outcome metrics."""
    def __init__(self, success: bool, steps: int, action_entropy_sum: float,
                 log_prob_shift_sum: float, injection_count: int):
        self.success = success
        self.steps = steps
        self.action_entropy_sum = action_entropy_sum
        self.log_prob_shift_sum = log_prob_shift_sum
        self.injection_count = injection_count

class EpisodeRunner:
    """
    Executes a single episode given the environment graph, router, and policy.
    This stub performs a deterministic walk using the policy's ``select_action``
    method and applies the router's injection logic at each step.
    """

    def __init__(self, config: EpisodeRunnerConfig):
        self.graph = config.state_graph
        self.router = config.router
        self.policy = config.policy
        self.max_steps = config.max_steps

    def run(self) -> EpisodeResult:
        # Very basic deterministic loop – sufficient for profiling and tests.
        current_node = self.graph.start
        steps = 0
        entropy_sum = 0.0
        log_prob_shift_sum = 0.0
        injection_count = 0

        while steps < self.max_steps and current_node != self.graph.goal:
            action, log_prob = self.policy.select_action(
                self.graph.nodes[current_node], self.graph
            )
            # If no action is possible, break.
            if action is None:
                break

            # Router may inject a skill signal, altering log probability.
            if self.router.should_inject():
                log_prob_shift_sum += self.router.inject_skill_signal(log_prob)
                injection_count += 1

            entropy_sum += -log_prob if log_prob is not None else 0.0

            # Move to the next node.
            current_node = action
            steps += 1

        success = current_node == self.graph.goal
        return EpisodeResult(
            success=success,
            steps=steps,
            action_entropy_sum=entropy_sum,
            log_prob_shift_sum=log_prob_shift_sum,
            injection_count=injection_count,
        )
