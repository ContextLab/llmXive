"""
Utility to remove duplicate or deprecated schema files from the contracts directory.
"""
import pathlib
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    contracts_dir = paths.path("specs", "001-structural-mismatch-cost", "contracts")
    deprecated = [
        "analysis_result.schema.yaml",
        "gam_results.schema.yaml",
        "execution_log.schema.yaml_",
        "execution_metrics.schema.yaml",
        "execution-log.schema.yaml",
        "query_result.schema.yaml",
        "statistics-result.schema.yaml",
    ]
    for fname in deprecated:
        path = contracts_dir / fname
        if path.exists():
            log.info("Removing deprecated schema: %s", path)
            path.unlink()

if __name__ == "__main__":
    main()
