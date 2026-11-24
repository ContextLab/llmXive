"""
Helper script to run the ingestion validation step.

This thin wrapper simply invokes ``code.ingestion.validate.main`` and
ensures that the expected output files are created:

  * ``data/logs/ingestion.log`` – populated by the project's logger.
  * ``data/processed/valid_record_count.txt`` – integer count of valid rows.
  * ``data/processed/validated.csv`` – CSV containing only the valid rows.
"""

from ingestion.validate import main as validate_main

if __name__ == "__main__":
    validate_main()