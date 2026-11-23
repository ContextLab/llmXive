# (unchanged – this script simply checks that required packages are installed)
import importlib
import sys

REQUIRED = [
    "datasets",
    "pandas",
    "pyarrow",
]

missing = [pkg for pkg in REQUIRED if importlib.util.find_spec(pkg) is None]

if missing:
    sys.stderr.write(f"Missing required packages: {', '.join(missing)}\\n")
    sys.exit(1)
else:
    print("All required packages are installed.")