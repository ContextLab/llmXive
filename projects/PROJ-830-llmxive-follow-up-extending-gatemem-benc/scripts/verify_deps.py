"""
Dependency verification script for PROJ-830-llmxive-follow-up-extending-gatemem-benc.

This script parses requirements.txt to ensure:
1. No GPU-specific libraries (bitsandbytes, CUDA-related packages) are present.
2. CPU-only flags are validated where applicable.
3. A log file is generated at scripts/verify_deps.log documenting the verification.
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Define the project root relative to this script's location
# Script is at: projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/scripts/verify_deps.py
# Requirements is at: projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/requirements.txt
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
LOG_PATH = SCRIPT_DIR / "verify_deps.log"

# Forbidden GPU libraries
FORBIDDEN_PACKAGES = {
    "bitsandbytes",
    "cudnn",
    "cudatoolkit",
    "torch-cuda",
    "tensorflow-gpu",
    "jaxlib-cuda",
}

# Packages that might have optional GPU dependencies but are allowed if CPU-only flags are used
ALLOWED_WITH_CPU_FLAGS = {
    "torch": ["cpu"],
    "tensorflow": ["cpu"],
}

def parse_requirements(filepath: Path) -> list[dict]:
    """Parse requirements.txt and return a list of package info dicts."""
    if not filepath.exists():
        raise FileNotFoundError(f"Requirements file not found: {filepath}")

    packages = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle comments after package spec
            if "#" in line:
                line = line.split("#")[0].strip()

            # Parse package name and version specifier
            # Regex handles: pkg, pkg==1.0, pkg>=1.0, pkg[extra]==1.0
            match = re.match(r"^([a-zA-Z0-9_-]+)(\[.*?\])?(.*)$", line)
            if match:
                pkg_name = match.group(1).lower()
                extras = match.group(2) or ""
                version_spec = match.group(3) or ""
                packages.append({
                    "name": pkg_name,
                    "extras": extras,
                    "version_spec": version_spec,
                    "raw_line": line,
                    "line_num": line_num,
                })
    return packages

def verify_dependencies(packages: list[dict]) -> dict:
    """Verify dependencies against CPU-only constraints."""
    results = {
        "success": True,
        "errors": [],
        "warnings": [],
        "verified_packages": [],
        "forbidden_found": [],
    }

    for pkg in packages:
        pkg_name = pkg["name"]
        raw_line = pkg["raw_line"]

        # Check for forbidden GPU packages
        if pkg_name in FORBIDDEN_PACKAGES:
            results["success"] = False
            results["errors"].append(
                f"Line {pkg['line_num']}: Forbidden GPU package detected: {raw_line}"
            )
            results["forbidden_found"].append(pkg_name)
            continue

        # Check allowed packages with GPU potential
        if pkg_name in ALLOWED_WITH_CPU_FLAGS:
            cpu_flag = ALLOWED_WITH_CPU_FLAGS[pkg_name][0]
            # Check if CPU flag is present in version spec or extras
            has_cpu = cpu_flag in raw_line.lower() or f"[{cpu_flag}]" in raw_line.lower()

            if not has_cpu:
                # Warn but don't fail if the package is commonly used and might default to CPU
                # For torch, we expect explicit cpu flag in requirements for safety
                if pkg_name == "torch":
                    results["success"] = False
                    results["errors"].append(
                        f"Line {pkg['line_num']}: '{pkg_name}' detected without explicit CPU flag. "
                        f"Expected format: '{pkg_name}+cpu' or '{pkg_name} --index-url ...' with CPU wheel. "
                        f"Current line: {raw_line}"
                    )
                else:
                    results["warnings"].append(
                        f"Line {pkg['line_num']}: '{pkg_name}' detected without explicit CPU flag. "
                        f"Please verify this installation uses CPU-only."
                    )
            else:
                results["verified_packages"].append(pkg_name)
        else:
            results["verified_packages"].append(pkg_name)

    return results

def write_log(log_path: Path, results: dict, packages: list[dict]):
    """Write verification results to log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("DEPENDENCY VERIFICATION LOG\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Requirements file: {log_path.parent.parent / 'requirements.txt'}\n")
        f.write("=" * 60 + "\n\n")

        f.write("SUMMARY\n")
        f.write("-" * 40 + "\n")
        status = "PASSED" if results["success"] else "FAILED"
        f.write(f"Verification Status: {status}\n\n")

        if results["errors"]:
            f.write("ERRORS:\n")
            for err in results["errors"]:
                f.write(f"  ✗ {err}\n")
            f.write("\n")

        if results["warnings"]:
            f.write("WARNINGS:\n")
            for warn in results["warnings"]:
                f.write(f"  ⚠ {warn}\n")
            f.write("\n")

        if results["forbidden_found"]:
            f.write("FORBIDDEN PACKAGES FOUND:\n")
            for pkg in results["forbidden_found"]:
                f.write(f"  - {pkg}\n")
            f.write("\n")

        f.write("VERIFIED PACKAGES:\n")
        for pkg in results["verified_packages"]:
            f.write(f"  ✓ {pkg}\n")
        f.write("\n")

        f.write("FULL REQUIREMENTS LIST:\n")
        f.write("-" * 40 + "\n")
        for pkg in packages:
            f.write(f"  {pkg['raw_line']}\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("END OF LOG\n")

def main():
    """Main entry point."""
    print(f"Verifying dependencies in {REQUIREMENTS_PATH}...")

    try:
        packages = parse_requirements(REQUIREMENTS_PATH)
        if not packages:
            print("No packages found in requirements.txt")
            # Write a log indicating no packages
            write_log(LOG_PATH, {"success": True, "errors": [], "warnings": [], "verified_packages": [], "forbidden_found": []}, [])
            print(f"Log written to {LOG_PATH}")
            return 0

        results = verify_dependencies(packages)
        write_log(LOG_PATH, results, packages)

        if results["success"]:
            print("✓ Dependency verification PASSED")
            print(f"Log written to {LOG_PATH}")
            return 0
        else:
            print("✗ Dependency verification FAILED")
            print(f"Errors found: {len(results['errors'])}")
            print(f"Log written to {LOG_PATH}")
            return 1

    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        # Write error to log
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.write(f"ERROR: {e}\n")
        return 2
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            f.write(f"UNEXPECTED ERROR: {e}\n")
        return 3

if __name__ == "__main__":
    sys.exit(main())
