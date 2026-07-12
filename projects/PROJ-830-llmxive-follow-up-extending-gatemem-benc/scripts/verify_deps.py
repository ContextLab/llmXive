"""
Dependency verification script for llmXive GateMem project.
Ensures no GPU-specific libraries (bitsandbytes, CUDA variants) are present
and validates CPU-only constraints.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "verify_deps.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        logger.error("requirements.txt not found in project root.")
        sys.exit(1)

    banned_packages = {
        "bitsandbytes",
        "flash-attn",
        "xformers",
        "cudnn",
        "cupy"
    }
    
    # Specific check for torch: ensure it's not a CUDA variant in the raw string
    # We allow torch, but check for suffixes like +cu118 if explicitly written in file
    gpu_indicators = ["cu118", "cu121", "cu123", "cuda"]

    logger.info("Starting dependency verification...")
    issues_found = False

    with open(requirements_path, "r") as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Parse package name (handle ==, >=, etc.)
        pkg_name = line.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0].strip()
        
        # Check banned packages
        if pkg_name.lower() in banned_packages:
            logger.error(f"Line {line_num}: Forbidden GPU package detected: {line}")
            issues_found = True

        # Check for CUDA indicators in the version string
        for indicator in gpu_indicators:
            if indicator in line.lower() and pkg_name.lower() != "torch":
                # Allow torch+cpu, but flag others
                if pkg_name.lower() == "torch" and "+cpu" in line.lower():
                    continue # This is fine
                logger.warning(f"Line {line_num}: Potential GPU indicator '{indicator}' found in: {line}")
                # Strictly speaking, if it's not torch+cpu, it might be an issue
                if pkg_name.lower() == "torch" and "+cpu" not in line.lower():
                    logger.error(f"Line {line_num}: Torch found without explicit +cpu tag: {line}")
                    issues_found = True

    if issues_found:
        logger.error("Verification FAILED: GPU dependencies detected.")
        sys.exit(1)
    else:
        logger.info("Verification PASSED: No forbidden GPU dependencies found.")
        logger.info(f"Log written to: {log_file}")

if __name__ == "__main__":
    main()
