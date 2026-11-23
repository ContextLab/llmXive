"""
Validates that linting and formatting configurations are correctly set up.
This script ensures .ruff.toml and pyproject.toml exist and contain pinned versions.
"""
import os
import sys
import toml
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    ruff_config = project_root / ".ruff.toml"
    pyproject = project_root / "pyproject.toml"
    requirements = project_root / "code" / "requirements.txt"

    errors = []

    # Check .ruff.toml exists
    if not ruff_config.exists():
        errors.append(f"Missing file: {ruff_config}")
    else:
        print(f"✓ Found .ruff.toml at {ruff_config}")

    # Check pyproject.toml exists and has pinned versions
    if not pyproject.exists():
        errors.append(f"Missing file: {pyproject}")
    else:
        print(f"✓ Found pyproject.toml at {pyproject}")
        try:
            with open(pyproject, "r") as f:
                config = toml.load(f)
            deps = config.get("project", {}).get("dependencies", [])
            if not deps:
                errors.append("No dependencies found in pyproject.toml")
            else:
                for dep in deps:
                    if ">=" in dep or "<=" in dep or "~=" in dep:
                        errors.append(f"Version range found in pyproject.toml: {dep}")
                        print(f"✗ Version range found: {dep}")
                    else:
                        print(f"✓ Pinned version: {dep}")
        except Exception as e:
            errors.append(f"Error parsing pyproject.toml: {e}")

    # Check requirements.txt exists and has pinned versions
    if not requirements.exists():
        errors.append(f"Missing file: {requirements}")
    else:
        print(f"✓ Found requirements.txt at {requirements}")
        with open(requirements, "r") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ">=" in line or "<=" in line or "~=" in line:
                errors.append(f"Version range found in requirements.txt: {line}")
                print(f"✗ Version range found: {line}")
            else:
                print(f"✓ Pinned version: {line}")

    if errors:
        print("\n❌ Validation failed with the following errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\n✅ All linting and formatting configurations are valid.")
        sys.exit(0)

if __name__ == "__main__":
    main()