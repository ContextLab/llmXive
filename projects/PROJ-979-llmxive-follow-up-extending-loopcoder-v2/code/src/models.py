"""
Data models for the LoopCoder-v2 follow-up analysis.

Defines core data structures for input problems and convergence trajectories
used throughout the entropy and inference pipelines.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ConvergenceStatus(Enum):
    """Enumeration of possible convergence outcomes."""
    CONVERGED = "converged"
    NOT_CONVERGED = "not_converged"
    MAX_LOOPS_REACHED = "max_loops_reached"
    ERROR = "error"


@dataclass
class InputProblem:
    """
    Represents a single coding problem input.

    Attributes:
        problem_id: Unique identifier for the problem (e.g., HumanEval task_id).
        prompt: The natural language prompt or problem description.
        canonical_solution: The reference solution code (if available).
        test_code: The test cases code to validate solutions.
        difficulty: Optional difficulty label (e.g., 'easy', 'medium', 'hard').
        strata_bin: The stratification bin this problem belongs to (from T004).
        metadata: Additional metadata dictionary.
    """
    problem_id: str
    prompt: str
    test_code: str
    canonical_solution: Optional[str] = None
    difficulty: Optional[str] = None
    strata_bin: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "problem_id": self.problem_id,
            "prompt": self.prompt,
            "canonical_solution": self.canonical_solution,
            "test_code": self.test_code,
            "difficulty": self.difficulty,
            "strata_bin": self.strata_bin,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InputProblem":
        """Create an InputProblem instance from a dictionary."""
        return cls(
            problem_id=data["problem_id"],
            prompt=data["prompt"],
            test_code=data["test_code"],
            canonical_solution=data.get("canonical_solution"),
            difficulty=data.get("difficulty"),
            strata_bin=data.get("strata_bin"),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConvergenceTrajectory:
    """
    Represents the convergence trajectory for a single problem across k loops.

    Attributes:
        problem_id: Reference to the InputProblem problem_id.
        k_values: List of loop counts attempted (e.g., [1, 2, 3]).
        generated_solutions: List of lists, where inner list contains solutions for a specific k.
            generated_solutions[k_idx] corresponds to k_values[k_idx].
        execution_results: List of execution results (pass/fail/error) for each k.
        converged_at_k: The first k value where a correct solution was found, or None.
        status: Final convergence status (Enum).
        final_solution: The code of the first correct solution found, or None.
        entropy_proxy: Optional semantic entropy value associated with this problem (from T012).
        metadata: Additional metadata (e.g., runtime, token counts).
    """
    problem_id: str
    k_values: List[int]
    generated_solutions: List[List[str]] = field(default_factory=list)
    execution_results: List[List[bool]] = field(default_factory=list)
    converged_at_k: Optional[int] = None
    status: ConvergenceStatus = ConvergenceStatus.NOT_CONVERGED
    final_solution: Optional[str] = None
    entropy_proxy: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(self, k: int, solutions: List[str], results: List[bool]) -> None:
        """
        Add a step to the trajectory for a specific k.

        Args:
            k: The loop count.
            solutions: List of generated code strings for this k.
            results: List of boolean pass/fail results for each solution.
        """
        self.k_values.append(k)
        self.generated_solutions.append(solutions)
        self.execution_results.append(results)

        # Check for convergence
        if any(results):
            if self.converged_at_k is None:
                self.converged_at_k = k
                self.final_solution = solutions[results.index(True)]
                self.status = ConvergenceStatus.CONVERGED

    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for serialization."""
        return {
            "problem_id": self.problem_id,
            "k_values": self.k_values,
            "generated_solutions": self.generated_solutions,
            "execution_results": self.execution_results,
            "converged_at_k": self.converged_at_k,
            "status": self.status.value,
            "final_solution": self.final_solution,
            "entropy_proxy": self.entropy_proxy,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConvergenceTrajectory":
        """Create a ConvergenceTrajectory instance from a dictionary."""
        # Reconstruct status enum
        status_str = data.get("status", "not_converged")
        status = ConvergenceStatus(status_str) if status_str in [s.value for s in ConvergenceStatus] else ConvergenceStatus.NOT_CONVERGED

        trajectory = cls(
            problem_id=data["problem_id"],
            k_values=data["k_values"],
            generated_solutions=data.get("generated_solutions", []),
            execution_results=data.get("execution_results", []),
            converged_at_k=data.get("converged_at_k"),
            status=status,
            final_solution=data.get("final_solution"),
            entropy_proxy=data.get("entropy_proxy"),
            metadata=data.get("metadata", {})
        )
        return trajectory