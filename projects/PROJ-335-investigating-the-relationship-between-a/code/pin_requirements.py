"""T002: Initialize Python project with pinned dependencies.

Ensures the required scientific packages (mne, numpy, scipy, pandas,
scikit-learn, statsmodels, pyyaml) are installed, then writes
code/requirements.txt with EXACT version pins (`==`) obtained from the
environment via importlib.metadata (equivalent to a filtered `pip freeze`).
"""
import subprocess
import sys
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

# Canonical PyPI names, mapped to their import-time aliases where needed.
REQUIRED_PACKAGES = [
    "mne",
    "numpy",
    "scipy",
    "pandas",
    "scikit-learn",
    "statsmodels",
    "pyyaml",
]

# importlib.metadata uses canonicalized names, so this lookup is direct.
def get_pinned_version(pkg: str) -> str:
    try:
        return version(pkg)
    except PackageNotFoundError:
        return None

def main() -> None:
    pins = {}
    missing = []
    for pkg in REQUIRED_PACKAGES:
        ver = get_pinned_version(pkg)
        if ver is None:
            missing.append(pkg)
        else:
            pins[pkg] = ver

    # Install anything missing (no silent fallback: failure raises).
    if missing:
        print(f"Installing missing packages: {missing}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", *missing],
            check=True,
        )
        for pkg in missing:
            ver = get_pinned_version(pkg)
            if ver is None:
                raise RuntimeError(
                    f"Package {pkg} still not importable after install; "
                    "cannot pin its version."
                )
            pins[pkg] = ver

    # Write requirements.txt with exact pins, in the declared order.
    out_path = Path(__file__).parent / "requirements.txt"
    lines = [f"{pkg}=={pins[pkg]}" for pkg in REQUIRED_PACKAGES]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote pinned requirements to {out_path}:")
    for line in lines:
        print(f"  {line}")

if __name__ == "__main__":
    main()