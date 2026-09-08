"""
Wrapper script to execute the target consistency check pipeline.

Running this module as a script will invoke the ``main`` function from
``code/data/target_consistency_check.py`` which:
  1. Loads the available raw data (Materials Project and NIST overlap).
  2. Calculates the Pearson correlation between candidate targets.
  3. Determines which property should be used as the predictive target.
  4. Writes the decision to ``data/results/target_decision.json`` conforming
     to ``contracts/target_decision.schema.yaml``.
"""

import logging
from data.target_consistency_check import main as run_target_check

# Configure a simple logger for this entry‑point.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def _run():
    """Execute the target consistency check."""
    logger.info("Starting target consistency check...")
    try:
        run_target_check()
        logger.info("Target decision JSON successfully created.")
    except Exception as exc:
        logger.exception("Target consistency check failed: %s", exc)
        raise

if __name__ == "__main__":
    _run()
