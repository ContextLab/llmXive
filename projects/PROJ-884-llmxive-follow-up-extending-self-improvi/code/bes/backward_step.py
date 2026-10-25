"""
Backward‑step implementation for Bidirectional Evolutionary Search (BES).

The backward step replaces the learned neural verifier with a deterministic,
rule‑based symbolic planner.  It receives a puzzle definition, asks the
``SymbolicPlanner`` to decompose the constraints into sub‑goals and returns
those sub‑goals together with execution metadata.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.bes.config import BESConfig
from code.symbolic.planner import SymbolicPlanner, ParseFailure, ContradictionDetected

logger = logging.getLogger(__name__)

@dataclass
class BackwardStepResult:
    """Result container for the backward step."""
    success: bool
    sub_goals: List[Dict[str, Any]]
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    execution_time: float = 0.0

class BackwardStepError(Exception):
    """Custom exception for backward‑step failures."""
    def __init__(self, message: str, code: str = "BACKWARD_STEP_ERROR"):
        super().__init__(message)
        self.code = code

class BackwardStep:
    """
    Backward‑step driver.

    It loads the configuration (mainly to expose the ``seed`` for reproducibility)
    and forwards the puzzle definition to the symbolic planner.  If the planner
    raises ``ParseFailure`` or ``ContradictionDetected`` the error is captured
    and reported in the ``BackwardStepResult``.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialise the backward step.

        Parameters
        ----------
        config_path: Optional[Path]
            Path to a BES configuration file.  If omitted the default
            configuration from ``code/config.py`` is used.
        """
        self.config_path = config_path or Path("code/bes/bes_config.yaml")
        try:
            self.config: BESConfig = BESConfig.load(self.config_path)
        except Exception as exc:
            logger.warning(
                f"Could not load BES config from {self.config_path}: {exc}. "
                "Falling back to defaults."
            )
            self.config = BESConfig()

        self.planner = SymbolicPlanner()

    def execute(self, puzzle_instance: Dict[str, Any]) -> BackwardStepResult:
        """
        Run the symbolic planner on ``puzzle_instance``.

        Returns
        -------
        BackwardStepResult
            ``success`` is ``True`` when sub‑goals were produced.
        """
        start = time.time()
        try:
            sub_goals = self.planner.plan(puzzle_instance)
            elapsed = time.time() - start
            return BackwardStepResult(
                success=True,
                sub_goals=sub_goals,
                execution_time=elapsed,
            )
        except (ParseFailure, ContradictionDetected) as exc:
            elapsed = time.time() - start
            logger.error(f"Symbolic planner failed: {exc}")
            return BackwardStepResult(
                success=False,
                sub_goals=[],
                error_message=str(exc),
                error_code=type(exc).__name__,
                execution_time=elapsed,
            )
        except Exception as exc:
            elapsed = time.time() - start
            logger.exception("Unexpected error in backward step")
            raise BackwardStepError(str(exc)) from exc

def main() -> None:
    """Simple CLI for manual testing."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Test BackwardStep")
    parser.add_argument(
        "--config",
        type=str,
        default="code/bes/bes_config.yaml",
        help="Path to BES config YAML",
    )
    parser.add_argument(
        "--puzzle",
        type=str,
        required=True,
        help="Path to a JSON file containing a single puzzle instance",
    )
    args = parser.parse_args()

    with open(args.puzzle, "r", encoding="utf-8") as f:
        puzzle = json.load(f)

    step = BackwardStep(Path(args.config))
    result = step.execute(puzzle)

    if result.success:
        print("Sub‑goals generated:")
        for i, g in enumerate(result.sub_goals, 1):
            print(f"{i}. {g}")
    else:
        print(f"Planner failed ({result.error_code}): {result.error_message}")

if __name__ == "__main__":
    main()
