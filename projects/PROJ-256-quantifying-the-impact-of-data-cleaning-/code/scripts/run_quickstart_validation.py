# NOTE: This file has been moved to `scripts/run_quickstart_validation.py`.
# It is retained for backward compatibility but raises an informative error.
import sys

def _raise_migration_error():
    raise ImportError(
        "The script `run_quickstart_validation.py` has been moved to "
        "`scripts/run_quickstart_validation.py`. Please import or execute it from the new location."
    )

# Re-export entry points that simply raise the migration error.
run_script = _raise_migration_error
validate_artifacts = _raise_migration_error
main = _raise_migration_error

if __name__ == '__main__':
    _raise_migration_error()