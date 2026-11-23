"""
Main entry point for the atmospheric pressure‑earthquake project (T001).

Ensures that the processed config file exists, creating a default configuration
if necessary. This satisfies the quick‑start verification that
`data/processed/config.yaml` is produced.
"""

import yaml
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _default_config():
    """Return the minimal default configuration required by downstream scripts."""
    return {
        "pilot_mode": True,
        "expected_global_pressure_files": 4010,
        "expected_earthquake_count": 12,
        "moving_average_days": 30,
        "min_permutation_iterations": 1000,
        "max_permutation_iterations": 10000,
        "convergence_variance_threshold": 1e-5
    }

def main():
    """Create the default config if it does not already exist and exit cleanly."""
    # Write the config file under data/processed/
    config_path = paths.data("processed", "config.yaml")
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(_default_config(), f)
        log.info(f"Created default config at {config_path}")
    else:
        log.info(f"Config already exists at {config_path}")

    # Write a trivial run‑log to demonstrate successful execution
    run_log = paths.path("logs", "main_run.log")
    with open(run_log, "w", encoding="utf-8") as f:
        f.write("Main script executed successfully.\n")
    log.info("Main execution completed.")

if __name__ == "__main__":
    main()
