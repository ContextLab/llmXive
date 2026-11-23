# NOTE: This file has been moved to `scripts/run_lint.py`.
# It is retained for backward compatibility but raises an informative error.
import importlib
import sys

def _raise_migration_error():
    raise ImportError(
        "The script `run_lint.py` has been moved to `scripts/run_lint.py`. "
        "Please import or execute it from the new location."
    )

# Re-export the same entry points to give a clear error if used.
run_command = _raise_migration_error
main = _raise_migration_error
format_code = _raise_migration_error

if __name__ == "__main__":
    _raise_migration_error()
