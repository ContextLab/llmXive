import os
from pathlib import Path
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def main():
    contracts_dir = Path("specs/001-llmxive-follow-up-extending-omniretrieva/contracts")
    if not contracts_dir.exists():
        log.warning("Contracts directory %s does not exist. Skipping cleanup.", contracts_dir)
        return

    # Comprehensive list of files to remove as per T002 and verifier feedback
    forbidden = [
        "analysis_result.schema.yaml",
        "gam_results.schema.yaml",
        "execution_log.schema.yaml_",
        "execution_metrics.schema.yaml",
        "execution-log.schema.yaml",
        "query_result.schema.yaml",
    ]

    for fname in forbidden:
        path = contracts_dir / fname
        if path.exists():
            log.info("Deleting deprecated schema: %s", path)
            path.unlink()

    log.info("Cleanup of contracts directory completed.")

if __name__ == "__main__":
    main()
