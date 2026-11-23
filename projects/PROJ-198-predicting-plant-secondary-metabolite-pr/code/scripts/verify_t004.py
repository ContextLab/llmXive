"""
T004 verification script.

1. Loads the configuration (``config.yaml`` / ``spec.yaml`` or defaults)
   and applies the global seed.
2. Verifies that the seed is reproducible across two independent
    re-seeding runs (same random draws).
3. Writes INFO-level messages to ``logs/run.log`` via the project
    logging utility (console + file handlers).
"""

import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import load_config, reset_config, set_global_seed
from utils.logging import get_logger, setup_logging


def main() -> int:
    setup_logging("t004_verification", level=20)  # logging.INFO
    logger = get_logger("t004_verification")

    logger.info("T004 verification started")

    # Load configuration twice (fresh singletons) and compare seeds.
    reset_config()
    cfg1 = load_config()
    seed1 = cfg1.seed

    reset_config()
    cfg2 = load_config()
    seed2 = cfg2.seed

    logger.info("First load seed=%d, second load seed=%d", seed1, seed2)
    if seed1 != seed2:
        logger.error("Seed is NOT reproducible across runs: %d != %d", seed1, seed2)
        return 1

    # Reproducibility of the RNG itself.
    draws_a = [random.random() for _ in range(5)]
    set_global_seed(seed1)
    draws_b = [random.random() for _ in range(5)]
    if draws_a != draws_b:
        logger.error("Random draws are not reproducible after re-seeding")
        return 1
    logger.info("Random draws reproducible after re-seeding with seed=%d", seed1)

    # Confirm logs/run.log exists and contains INFO messages.
    log_file = PROJECT_ROOT / "logs" / "run.log"
    if not log_file.exists():
        logger.error("Expected log file %s was not created", log_file)
        return 1
    content = log_file.read_text(encoding="utf-8")
    if "INFO" not in content:
        logger.error("Log file %s contains no INFO-level messages", log_file)
        return 1

    logger.info("T004 verification PASSED (seed=%d, log=%s)", seed1, log_file)
    print(f"T004 OK: seed={seed1}, log file={log_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())