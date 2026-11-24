"""
Dummy logging script to ensure that the experiment log CSV file is created.
This script writes a single dummy row using the logging configuration defined
in `code/logging_config.py`. It is intended to be run as part of the Quickstart
after the logging configuration has been verified.
"""
from code.logging_config import log_experiment_entry, LOG_COLUMNS

def main() -> None:
    """Write a single dummy log entry to the experiment CSV."""
    dummy_entry = {col: "test" for col in LOG_COLUMNS}
    log_experiment_entry(dummy_entry)

if __name__ == "__main__":
    main()
