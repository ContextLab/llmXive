"""
Minimal validator that checks the quick‑start script can be imported and that the
required artefacts exist.  The original implementation attempted to call
``get_logger('quickstart_validator')`` which failed because ``get_logger`` did not
accept a name argument.  The updated ``reproducibility.logs`` module now provides
a compatible signature, so this validator works again.
"""

import json
import os
import subprocess
from pathlib import Path

from reproducibility.logs import get_logger


class QuickstartValidator:
    """Runs the quick‑start script and verifies expected outputs."""

    REQUIRED_FILES = [
        "data/plots/complexity_visualization_examples.png",
        "data/plots/crossing_vs_braid.png",
        "data/processed/knots_cleaned.csv",
        "data/raw/knot_atlas_raw.json",
    ]

    def __init__(self):
        self.logger = get_logger("quickstart_validator")

    def run(self) -> bool:
        """Execute ``python quickstart.md``‑style steps and confirm artefacts."""
        try:
            self.logger.log("quickstart_validation_start")
            # The quick‑start script is effectively the ``main`` function of the
            # complexity visualisation module.
            subprocess.check_call(
                ["python", "-c", "import code.analysis.complexity_visualization as cv; cv.main()"]
            )
            missing = [p for p in self.REQUIRED_FILES if not Path(p).exists()]
            if missing:
                self.logger.log(
                    "quickstart_validation_failed",
                    status="failed",
                    parameters={"missing": missing},
                )
                return False
            self.logger.log("quickstart_validation_success")
            return True
        except subprocess.CalledProcessError as exc:
            self.logger.log(
                "quickstart_validation_error",
                status="failed",
                parameters={"returncode": exc.returncode},
            )
            return False


def main() -> None:  # pragma: no cover
    validator = QuickstartValidator()
    success = validator.run()
    print("Quick‑start validation:", "PASS" if success else "FAIL")