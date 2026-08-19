"""
Forward step implementation for the BES framework.
Handles LLM-based trajectory recombination with strict timeout enforcement.
"""
import torch
import time
import logging
import json
import os
import sys
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Import from project API
from bes.config import BESConfig, get_default_config
from bes.population import Individual, Population
from symbolic.planner import SymbolicPlanner, SubGoal
from dataset.verifier import PuzzleVerifier, SolutionResult
from utils.logger import setup_logging, log
from utils.seed import set_seed
from exceptions import BaseResearchException

# Configure logging
logger = logging.getLogger(__name__)

class ForwardStepError(BaseResearchException):
    """Custom exception for forward step failures."""
    pass

@dataclass
class ForwardStepResult:
    """Result of a single forward step execution."""
    success: bool
    candidate: Optional[Individual]
    reason: Optional[str] = None
    elapsed_time: float = 0.0
    timeout_triggered: bool = False
    subgoals_used: List[str] = field(default_factory=list)

class TimeoutException(Exception):
    """Raised when a timeout occurs."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutException("Generation attempt exceeded time limit")

class ForwardStep:
    """
    Implements the forward step of the BES loop.
    Uses a small CPU-tractable LLM for trajectory recombination.
    Enforces strict timeouts to prevent infinite loops.
    """

    def __init__(self, config: BESConfig, timeout_seconds: float = 5.0):
        self.config = config
        self.timeout_seconds = timeout_seconds
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self._setup_logging()

    def _setup_logging(self):
        """Initialize logging for this module."""
        setup_logging()
        logger.info(f"ForwardStep initialized with timeout={self.timeout_seconds}s")

    def load_model(self):
        """
        Load the LLM model specified in config.
        Uses optimum for CPU optimization.
        """
        if self.model is not None:
            return

        logger.info(f"Loading model: {self.config.model_name} on {self.device}")

        try:
            # Import optimum for CPU optimization
            from optimum.intel import IPEXModel
            from transformers import AutoTokenizer, AutoConfig

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                trust_remote_code=False
            )

            # Load model with CPU optimization
            # Using IPEX for Intel CPU optimization, fallback to standard if unavailable
            try:
                self.model = IPEXModel.from_pretrained(
                    self.config.model_name,
                    torchscript=False,
                    compile=False
                )
            except Exception as e:
                logger.warning(f"IPEX not available, falling back to standard transformers: {e}")
                from transformers import AutoModelForCausalLM
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.config.model_name,
                    torchscript=False,
                    low_cpu_mem_usage=True
                )

            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Model loaded successfully: {self.config.model_name}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise ForwardStepError(f"Model loading failed: {e}")

    def _generate_with_timeout(
        self,
        prompt: str,
        subgoals: List[SubGoal]
    ) -> Tuple[str, bool]:
        """
        Generate a trajectory with a strict timeout.
        Returns (generation, timeout_triggered).
        """
        generation = ""
        timeout_triggered = False

        # Set up signal-based timeout (Unix only)
        # For cross-platform compatibility, we also use a time-based check
        start_time = time.time()

        # Try signal-based timeout if available
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(self.timeout_seconds))
            try:
                generation = self._generate_trajectory(prompt, subgoals)
            except TimeoutException:
                timeout_triggered = True
                logger.warning(f"Generation timed out after {self.timeout_seconds}s")
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        else:
            # Fallback to time-based checking for Windows
            generation = self._generate_trajectory_with_time_check(prompt, subgoals)
            if time.time() - start_time > self.timeout_seconds:
                timeout_triggered = True
                logger.warning(f"Generation timed out after {self.timeout_seconds}s")

        return generation, timeout_triggered

    def _generate_trajectory_with_time_check(
        self,
        prompt: str,
        subgoals: List[SubGoal]
    ) -> str:
        """Generate trajectory with manual time checking."""
        start_time = time.time()
        # Simplified generation for timeout safety
        # In a real implementation, this would generate token by token
        # and check elapsed time at each step
        if time.time() - start_time > self.timeout_seconds:
            raise TimeoutException("Timeout during generation")
        
        # Placeholder for actual generation logic
        # This would normally call model.generate() with time checks
        return f"Generated trajectory for prompt: {prompt[:50]}..."

    def _generate_trajectory(
        self,
        prompt: str,
        subgoals: List[SubGoal]
    ) -> str:
        """
        Generate a trajectory using the LLM.
        This is the core generation logic.
        """
        if self.model is None:
            self.load_model()

        # Prepare input
        subgoal_text = "\n".join([f"- {sg.description}" for sg in subgoals])
        full_prompt = f"{prompt}\n\nSubgoals to satisfy:\n{subgoal_text}"

        inputs = self.tokenizer(
            full_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_input_length
        ).to(self.device)

        # Generate with timeout safety
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.max_new_tokens,
                temperature=self.config.temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                use_cache=True
            )

        # Decode output
        generation = self.tokenizer.decode(
            outputs[0, inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )

        return generation

    def recombine_trajectory(
        self,
        puzzle: Dict[str, Any],
        subgoals: List[SubGoal],
        parent: Optional[Individual] = None
    ) -> ForwardStepResult:
        """
        Recombine a trajectory guided by symbolic subgoals.
        Enforces strict timeout per generation attempt.
        """
        start_time = time.time()
        set_seed(self.config.seed)

        try:
            # Prepare prompt from puzzle
            prompt = self._prepare_prompt(puzzle, parent)

            # Generate with timeout enforcement
            generation, timeout_triggered = self._generate_with_timeout(
                prompt,
                subgoals
            )

            elapsed_time = time.time() - start_time

            if timeout_triggered:
                logger.warning(
                    f"Generation timed out after {elapsed_time:.2f}s. "
                    f"Discarding candidate."
                )
                return ForwardStepResult(
                    success=False,
                    candidate=None,
                    reason="TIMEOUT",
                    elapsed_time=elapsed_time,
                    timeout_triggered=True,
                    subgoals_used=[sg.id for sg in subgoals]
                )

            # Parse and validate generation
            candidate = self._parse_and_validate(generation, puzzle)

            elapsed_time = time.time() - start_time

            if candidate is None:
                return ForwardStepResult(
                    success=False,
                    candidate=None,
                    reason="VALIDATION_FAILED",
                    elapsed_time=elapsed_time,
                    subgoals_used=[sg.id for sg in subgoals]
                )

            return ForwardStepResult(
                success=True,
                candidate=candidate,
                elapsed_time=elapsed_time,
                subgoals_used=[sg.id for sg in subgoals]
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Forward step failed: {e}")
            return ForwardStepResult(
                success=False,
                candidate=None,
                reason=f"ERROR: {str(e)}",
                elapsed_time=elapsed_time
            )

    def _prepare_prompt(
        self,
        puzzle: Dict[str, Any],
        parent: Optional[Individual] = None
    ) -> str:
        """Prepare the input prompt for the LLM."""
        puzzle_str = json.dumps(puzzle, indent=2)
        
        if parent:
            parent_str = json.dumps(parent.data, indent=2)
            return f"""
            Puzzle:
            {puzzle_str}
            
            Parent trajectory (to improve):
            {parent_str}
            
            Generate an improved trajectory that satisfies the puzzle constraints.
            """
        else:
            return f"""
            Puzzle:
            {puzzle_str}
            
            Generate a valid trajectory that satisfies the puzzle constraints.
            """

    def _parse_and_validate(
        self,
        generation: str,
        puzzle: Dict[str, Any]
    ) -> Optional[Individual]:
        """Parse the generation and validate it against the puzzle."""
        try:
            # Attempt to parse as JSON
            try:
                parsed = json.loads(generation)
            except json.JSONDecodeError:
                # Try to extract JSON from text
                import re
                match = re.search(r'\{.*\}', generation, re.DOTALL)
                if match:
                    parsed = json.loads(match.group())
                else:
                    logger.warning("Could not parse generation as JSON")
                    return None

            # Validate against puzzle
            verifier = PuzzleVerifier()
            result = verifier.verify_solution(puzzle, parsed)

            if result.is_valid:
                return Individual(
                    data=parsed,
                    fitness=1.0,
                    generation=0
                )
            else:
                logger.debug(f"Validation failed: {result.error_codes}")
                return None

        except Exception as e:
            logger.warning(f"Parse/validation error: {e}")
            return None

    def run(
        self,
        population: Population,
        puzzles: List[Dict[str, Any]],
        planner: SymbolicPlanner
    ) -> Population:
        """
        Execute the forward step on the entire population.
        Applies timeout to each generation attempt.
        """
        new_population = Population()
        total_timeout = 0

        for puzzle in puzzles:
            # Get subgoals from symbolic planner
            decomposition = planner.decompose(puzzle)
            subgoals = decomposition.subgoals

            # Try to recombine for each individual in population
            for individual in population.individuals:
                result = self.recombine_trajectory(
                    puzzle=puzzle,
                    subgoals=subgoals,
                    parent=individual
                )

                if result.success:
                    new_population.add(result.candidate)
                elif result.timeout_triggered:
                    total_timeout += 1
                    logger.info(
                        f"Timeout encountered for puzzle {puzzle.get('id', 'unknown')}. "
                        f"Discarding candidate."
                    )

        logger.info(
            f"Forward step complete. "
            f"Generated {len(new_population.individuals)} candidates. "
            f"Timeouts: {total_timeout}"
        )

        return new_population

def main():
    """Main entry point for testing the forward step."""
    # Load config
    config = get_default_config()
    config.model_name = "distilbert-tiny"  # Use a small model for testing
    
    # Initialize forward step with 5 second timeout
    forward_step = ForwardStep(config, timeout_seconds=5.0)
    
    # Create a test puzzle
    test_puzzle = {
        "id": "test_001",
        "type": "pathfinding",
        "initial_state": {"x": 0, "y": 0},
        "target_state": {"x": 5, "y": 5},
        "constraints": ["no_diagonal", "avoid_obstacles"]
    }
    
    # Create a mock planner
    from symbolic.planner import SymbolicPlanner, SubGoal
    planner = SymbolicPlanner()
    
    # Create a mock population
    from bes.population import Population, Individual
    population = Population()
    population.add(Individual(data={"path": [{"x": 0, "y": 0}]}, fitness=0.5, generation=0))
    
    # Run forward step
    try:
        result_population = forward_step.run(population, [test_puzzle], planner)
        print(f"Generated {len(result_population.individuals)} candidates")
        for ind in result_population.individuals:
            print(f"  Fitness: {ind.fitness}, Data: {ind.data}")
    except Exception as e:
        print(f"Error during forward step: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()