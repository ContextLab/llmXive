"""
T1201b: Generate migration plan for identified t0*.py files.

This script scans the code/ directory for all files matching 't0*.py',
analyzes their imports and logic, and generates a migration plan JSON
file mapping each script to its target canonical module.

Verification: T1201b confirms plan covers all identified files.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import local utilities if available, otherwise fallback to standard library
try:
    from utils import setup_logging
except ImportError:
    # Fallback for standalone execution if utils.py is not in path
    import logging
    def setup_logging(level: str = "INFO"):
        logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))
        return logging.getLogger(__name__)

logger = setup_logging("INFO")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "migration_plan.json"

# Mapping of known t0* scripts to their target modules based on task descriptions
# This is a heuristic map; the script also dynamically detects imports to refine this.
KNOWN_MAPPINGS = {
    # US1: Baseline Analysis
    "t012_run_baseline_analysis.py": "analysis",
    "t013_record_baseline_metrics.py": "analysis",
    "t023_reanalyze_cleaned_variants.py": "analysis",
    
    # US2: Cleaning Strategies
    "t017_apply_iqr.py": "cleaning",
    "t018_apply_mean_imputation.py": "cleaning",
    "t019_apply_median_imputation.py": "cleaning",
    "t020_apply_knn_imputation.py": "cleaning",
    "t021_apply_categorical_recoding.py": "cleaning",
    "t022_save_cleaned_datasets.py": "cleaning",
    
    # US3: Reporting & Comparison
    "t027_run_comparison.py": "reporting",
    "t028_claim_verification.py": "reporting",
    "t029_missingness_binning.py": "sensitivity",
    "t030_dataset_size_sensitivity.py": "sensitivity",
    "t031_bootstrap_variance.py": "sensitivity",
    "t033_outlier_threshold_sweep.py": "sensitivity",
    "t034_generate_forest_plot.py": "reporting",
    "t035_generate_ci_heatmap.py": "reporting",
    "t036_pvalue_shift_reporting.py": "reporting",
    "t037_ci_width_reporting.py": "reporting",
    "t038_effect_size_reporting.py": "reporting",
    "t039_log_excluded_datasets.py": "reporting",
    "t040_create_comparison_report.py": "reporting",
    "t041_generate_final_report.py": "reporting",
    
    # FPR & Null
    "t032_permutation_null_fpr.py": "analysis",
    
    # Utils & Config
    "t044_runtime_profiling.py": "utils",
    "t045_conditional_bootstrap_reduction.py": "utils",
    "t048_verify_checksums_and_state.py": "utils",
    
    # Hygiene & Maintenance
    "t050_reconcile_runbook.py": "scripts", # Likely moves to scripts/
}

def analyze_file_imports(filepath: Path) -> Dict[str, Any]:
    """
    Scans a Python file for imports and main logic to suggest a target module.
    """
    imports = []
    functions = []
    classes = []
    main_entry = False

    try:
        content = filepath.read_text(encoding="utf-8")
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                imports.append(stripped)
            if stripped.startswith('def '):
                func_name = stripped.split('(')[0].replace('def ', '')
                functions.append(func_name)
            if stripped.startswith('class '):
                class_name = stripped.split('(')[0].replace('class ', '')
                classes.append(class_name)
            if 'if __name__ == "__main__":' in stripped:
                main_entry = True
    except Exception as e:
        logger.warning(f"Could not analyze {filepath}: {e}")

    return {
        "imports": imports,
        "functions": functions,
        "classes": classes,
        "has_main": main_entry
    }

def determine_target_module(filename: str, analysis: Dict[str, Any]) -> str:
    """
    Determines the target canonical module for a given t0* script.
    """
    # 1. Check known mappings first
    if filename in KNOWN_MAPPINGS:
        return KNOWN_MAPPINGS[filename]

    # 2. Heuristic based on filename content
    if "clean" in filename.lower() or "imput" in filename.lower() or "iqr" in filename.lower():
        return "cleaning"
    if "baseline" in filename.lower() or "analysis" in filename.lower() or "test" in filename.lower():
        return "analysis"
    if "report" in filename.lower() or "plot" in filename.lower() or "compare" in filename.lower():
        return "reporting"
    if "sensitivity" in filename.lower() or "binning" in filename.lower() or "sweep" in filename.lower():
        return "sensitivity"
    if "null" in filename.lower() or "fpr" in filename.lower() or "permutation" in filename.lower():
        return "analysis" # FPR is part of analysis logic
    if "utils" in filename.lower() or "profiling" in filename.lower() or "checksum" in filename.lower():
        return "utils"
    
    # 3. Fallback based on imports
    if "cleaning" in str(analysis["imports"]):
        return "cleaning"
    if "analysis" in str(analysis["imports"]):
        return "analysis"
    if "reporting" in str(analysis["imports"]):
        return "reporting"

    return "unknown"

def scan_t0_scripts() -> List[Dict[str, Any]]:
    """
    Scans the code/ directory for all t0*.py files and generates a migration plan.
    """
    migration_plan = []
    t0_files = list(CODE_DIR.glob("t0*.py"))
    
    if not t0_files:
        logger.info("No t0*.py files found in code/ directory.")
        return migration_plan

    logger.info(f"Found {len(t0_files)} t0*.py files to migrate.")

    for file_path in t0_files:
        filename = file_path.name
        analysis = analyze_file_imports(file_path)
        target = determine_target_module(filename, analysis)
        
        entry = {
            "source_file": filename,
            "source_path": str(file_path.relative_to(PROJECT_ROOT)),
            "target_module": target,
            "target_path": f"code/{target}.py" if target != "scripts" else f"scripts/{filename}",
            "functions_to_migrate": [f for f in analysis["functions"] if f != "main"],
            "imports_used": analysis["imports"],
            "status": "pending_migration",
            "notes": "Logic migration required. Verify function signatures match target module."
        }
        migration_plan.append(entry)

    return migration_plan

def save_plan(plan: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the migration plan to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2)
    logger.info(f"Migration plan saved to: {output_path}")

def main():
    logger.info("Starting T1201b: Generate migration plan for t0*.py files")
    plan = scan_t0_scripts()
    save_plan(plan, OUTPUT_PATH)
    
    # Verification: Ensure plan covers all identified files
    t0_files_count = len(list(CODE_DIR.glob("t0*.py")))
    if len(plan) == t0_files_count:
        logger.info(f"Verification PASSED: Plan covers all {t0_files_count} identified files.")
    else:
        logger.error(f"Verification FAILED: Plan has {len(plan)} entries but {t0_files_count} files found.")
        raise RuntimeError("Migration plan incomplete.")

if __name__ == "__main__":
    main()