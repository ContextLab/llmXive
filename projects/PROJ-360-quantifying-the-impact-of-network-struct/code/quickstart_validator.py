import os
import sys
import logging
import importlib.util
import subprocess
from pathlib import Path
import json
import time

def setup_logger():
    logger = logging.getLogger("quickstart_validator")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def check_dependencies(logger):
    logger.info("Checking pinned dependencies in requirements.txt...")
    req_path = Path("requirements.txt")
    if not req_path.exists():
        logger.error("requirements.txt not found.")
        return False
    
    required_packages = ["pymatgen", "networkx", "scikit-learn", "pandas", "requests", "numpy", "statsmodels"]
    try:
        import importlib.metadata
        for pkg in required_packages:
            try:
                importlib.metadata.version(pkg)
                logger.info(f"  Found: {pkg}")
            except importlib.metadata.PackageNotFoundError:
                logger.error(f"  Missing: {pkg}")
                return False
        logger.info("All dependencies present.")
        return True
    except Exception as e:
        logger.error(f"Dependency check failed: {e}")
        return False

def check_directories(logger):
    logger.info("Checking required directories...")
    dirs = [
        "data/raw/cif",
        "data/processed/networks",
        "data/processed",
        "models",
        "results"
    ]
    for d in dirs:
        if not Path(d).exists():
            logger.error(f"Directory missing: {d}")
            return False
    logger.info("All required directories exist.")
    return True

def check_artifacts(logger):
    logger.info("Checking required output artifacts...")
    artifacts = {
        "data/processed/network_manifest.json": "JSON",
        "data/processed/metrics.csv": "CSV",
        "results/correlations.json": "JSON",
        "models/thermal_predictor.pkl": "Binary",
        "results/model_performance.json": "JSON",
        "results/final_report.md": "Text",
        "results/runtime.log": "Text"
    }
    
    all_present = True
    for path, type_name in artifacts.items():
        p = Path(path)
        if not p.exists():
            logger.error(f"Artifact missing: {path} ({type_name})")
            all_present = False
        else:
            if p.stat().st_size == 0:
                logger.warning(f"Artifact empty: {path} ({type_name})")
            else:
                logger.info(f"  Present: {path} ({type_name}, size={p.stat().st_size})")
    
    return all_present

def verify_seed_determinism(logger):
    logger.info("Verifying seed determinism (checking config)...")
    config_path = Path("code/config.py")
    if not config_path.exists():
        logger.error("config.py missing, cannot verify seed pinning.")
        return False
    
    # Check if config.py contains seed pinning logic
    content = config_path.read_text()
    if "random.seed" in content or "np.random.seed" in content:
        logger.info("Seed pinning logic detected in config.py.")
        return True
    else:
        logger.warning("No explicit seed pinning found in config.py.")
        return False

def verify_module_imports(logger):
    logger.info("Verifying module imports...")
    modules_to_check = [
        "code.download",
        "code.construct_network",
        "code.compute_metrics",
        "code.analyze",
        "code.report",
        "code.quickstart"
    ]
    
    all_ok = True
    for mod in modules_to_check:
        try:
            # Remove 'code.' prefix for import if present in path
            import_path = mod.replace("code.", "")
            spec = importlib.util.find_spec(import_path)
            if spec is None:
                logger.error(f"Module not found: {mod}")
                all_ok = False
            else:
                logger.info(f"  Module importable: {mod}")
        except Exception as e:
            logger.error(f"Error importing {mod}: {e}")
            all_ok = False
    
    return all_ok

def run_quickstart_validation(logger):
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation (T030)")
    logger.info("=" * 60)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Directories", check_directories),
        ("Artifacts", check_artifacts),
        ("Seed Determinism", verify_seed_determinism),
        ("Module Imports", verify_module_imports)
    ]
    
    results = {}
    for name, func in checks:
        logger.info(f"\n--- Running: {name} ---")
        results[name] = func(logger)
    
    logger.info("\n" + "=" * 60)
    logger.info("Validation Summary")
    logger.info("=" * 60)
    
    all_passed = all(results.values())
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{name}: {status}")
    
    log_path = Path("results/quickstart_validation.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write(f"Validation Run: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        for name, passed in results.items():
            f.write(f"{name}: {'PASSED' if passed else 'FAILED'}\n")
        f.write(f"Overall: {'PASSED' if all_passed else 'FAILED'}\n")
    
    logger.info(f"Log written to: {log_path}")
    
    return all_passed

def main():
    logger = setup_logger()
    success = run_quickstart_validation(logger)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
