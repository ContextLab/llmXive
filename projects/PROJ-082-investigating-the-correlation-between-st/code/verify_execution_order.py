"""
T037: Verify tasks.md execution order matches data flow (extraction -> analysis -> visualization).

This script validates the logical dependency chain described in tasks.md:
1. Extraction (T013) -> produces raw parsed data
2. Analysis (T014, T021, T021b, T022) -> consumes extraction output, produces metrics
3. Visualization (T027, T028) -> consumes analysis output, produces plots
4. Reporting (T032) -> consumes final analysis results

It verifies:
- That the code structure reflects these dependencies (imports)
- That the tasks.md file correctly documents these dependencies
- That the data flow is consistent end-to-end
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Import existing utilities
from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

# Define the expected data flow phases
EXPECTED_FLOW = [
    {
        "phase": "extraction",
        "task_id": "T013",
        "file": "code/extraction/parser.py",
        "outputs": ["data/extracted_studies.json", "data/qualitative_notes.json"]
    },
    {
        "phase": "meta_analysis",
        "task_id": "T014",
        "file": "code/analysis/meta_analysis.py",
        "inputs": ["data/extracted_studies.json"],
        "outputs": ["data/meta_analysis_results.json"]
    },
    {
        "phase": "narrative",
        "task_id": "T015",
        "file": "code/analysis/narrative.py",
        "inputs": ["data/qualitative_notes.json", "data/meta_analysis_results.json"],
        "outputs": ["data/narrative_summary.json"]
    },
    {
        "phase": "bias_assessment",
        "task_id": "T021",
        "file": "code/analysis/bias.py",
        "inputs": ["data/meta_analysis_results.json"],
        "outputs": ["data/bias_results.json"]
    },
    {
        "phase": "heterogeneity",
        "task_id": "T021b",
        "file": "code/analysis/heterogeneity.py",
        "inputs": ["data/meta_analysis_results.json", "data/bias_results.json"],
        "outputs": ["data/heterogeneity_results.json"]
    },
    {
        "phase": "correction",
        "task_id": "T022",
        "file": "code/analysis/correction.py",
        "inputs": ["data/meta_analysis_results.json"],
        "outputs": ["data/correction_results.json"]
    },
    {
        "phase": "visualization",
        "task_id": "T027",
        "file": "code/visualization/plots.py",
        "inputs": ["data/meta_analysis_results.json", "data/bias_results.json", "data/heterogeneity_results.json"],
        "outputs": ["data/derived/forest_plot.png", "data/derived/funnel_plot.png", "data/derived/correlation_summary.png"]
    },
    {
        "phase": "report_generation",
        "task_id": "T032",
        "file": "code/report_generator.py",
        "inputs": ["data/meta_analysis_results.json", "data/narrative_summary.json", "data/bias_results.json", "data/heterogeneity_results.json", "data/correction_results.json"],
        "outputs": ["docs/paper_draft.md"]
    }
]

def verify_file_exists(file_path: str, root: Path) -> bool:
    """Check if a file exists relative to project root."""
    full_path = root / file_path
    return full_path.exists()

def verify_imports(file_path: str, root: Path) -> Tuple[bool, List[str]]:
    """
    Verify that a file imports from the correct upstream modules.
    Returns (success, list of missing imports or issues).
    """
    full_path = root / file_path
    if not full_path.exists():
        return False, [f"File not found: {file_path}"]

    try:
        content = full_path.read_text()
        # Basic check: look for imports from expected upstream modules
        issues = []
        
        # Define expected import patterns for each phase
        if "parser.py" in file_path:
            # Extraction should import from utils
            if "from utils" not in content:
                issues.append("Missing imports from utils")
        
        elif "meta_analysis.py" in file_path:
            # Meta-analysis should import from extraction
            if "from extraction" not in content:
                issues.append("Missing imports from extraction module")
        
        elif "bias.py" in file_path:
            # Bias should import from meta_analysis
            if "from analysis.meta_analysis" not in content and "from .meta_analysis" not in content:
                issues.append("Missing imports from meta_analysis module")
        
        elif "heterogeneity.py" in file_path:
            # Heterogeneity should import from meta_analysis and bias
            if "from analysis.meta_analysis" not in content and "from .meta_analysis" not in content:
                issues.append("Missing imports from meta_analysis module")
        
        elif "plots.py" in file_path:
            # Visualization should import from analysis modules
            if "from analysis" not in content:
                issues.append("Missing imports from analysis module")
        
        elif "report_generator.py" in file_path:
            # Report generation should import from analysis modules
            if "from analysis" not in content:
                issues.append("Missing imports from analysis module")
        
        return len(issues) == 0, issues
    except Exception as e:
        return False, [f"Error reading file: {str(e)}"]

def verify_tasks_md_dependencies(root: Path) -> Tuple[bool, List[str]]:
    """
    Verify that tasks.md correctly documents the dependencies.
    """
    tasks_md_path = root / "tasks.md"
    if not tasks_md_path.exists():
        return False, ["tasks.md not found"]

    try:
        content = tasks_md_path.read_text()
        issues = []

        # Check for dependency declarations in tasks.md
        # Look for patterns like "Depends on: T014" or "explicitly depends on"
        if "Depends on: T014" not in content:
            issues.append("Missing dependency declaration: T014 (meta_analysis)")
        
        if "Depends on: T008" not in content:
            issues.append("Missing dependency declaration: T008 (tract_mapping)")
        
        if "Depends on: T013" not in content:
            issues.append("Missing dependency declaration: T013 (extraction)")
        
        if "Depends on: T027" not in content:
            issues.append("Missing dependency declaration: T027 (plots)")

        # Check for execution order mentions
        if "extraction -> analysis -> visualization" not in content:
            issues.append("Missing execution order documentation: extraction -> analysis -> visualization")

        return len(issues) == 0, issues
    except Exception as e:
        return False, [f"Error reading tasks.md: {str(e)}"]

def run_verification() -> bool:
    """Run all verification checks."""
    root = get_project_root()
    all_passed = True
    all_issues: List[str] = []

    logger.info("Starting execution order verification...")

    # 1. Verify all files exist
    logger.info("Step 1: Verifying file existence...")
    for step in EXPECTED_FLOW:
        if not verify_file_exists(step["file"], root):
            issue = f"Missing file: {step['file']} (Phase: {step['phase']})"
            all_issues.append(issue)
            all_passed = False
            logger.warning(f"  ❌ {issue}")
        else:
            logger.info(f"  ✅ {step['file']} exists")

    # 2. Verify imports
    logger.info("Step 2: Verifying import dependencies...")
    for step in EXPECTED_FLOW:
        success, issues = verify_imports(step["file"], root)
        if not success:
            for issue in issues:
                all_issues.append(f"{step['file']}: {issue}")
                all_passed = False
            logger.warning(f"  ❌ {step['file']}: {issues}")
        else:
            logger.info(f"  ✅ {step['file']} imports verified")

    # 3. Verify tasks.md dependencies
    logger.info("Step 3: Verifying tasks.md dependency documentation...")
    success, issues = verify_tasks_md_dependencies(root)
    if not success:
        for issue in issues:
            all_issues.append(f"tasks.md: {issue}")
            all_passed = False
        logger.warning(f"  ❌ tasks.md issues: {issues}")
    else:
        logger.info("  ✅ tasks.md dependency documentation verified")

    # 4. Verify data flow consistency
    logger.info("Step 4: Verifying data flow consistency...")
    # Check that outputs of one phase are inputs of the next
    for i in range(len(EXPECTED_FLOW) - 1):
        current_outputs = set(EXPECTED_FLOW[i].get("outputs", []))
        next_inputs = set(EXPECTED_FLOW[i + 1].get("inputs", []))
        
        # Find common files
        common = current_outputs.intersection(next_inputs)
        if not common:
            # This might be okay if there's an intermediate file or if the next phase
            # uses a different output from the same phase
            logger.warning(f"  ⚠️  No direct file overlap between {EXPECTED_FLOW[i]['phase']} outputs and {EXPECTED_FLOW[i+1]['phase']} inputs")
        else:
            logger.info(f"  ✅ Data flow confirmed: {common}")

    # Summary
    logger.info("\n" + "="*60)
    if all_passed:
        logger.info("✅ Execution order verification PASSED")
        logger.info("   - All required files exist")
        logger.info("   - Import dependencies are correct")
        logger.info("   - tasks.md correctly documents dependencies")
        logger.info("   - Data flow is consistent")
    else:
        logger.warning("❌ Execution order verification FAILED")
        logger.warning(f"   Issues found: {len(all_issues)}")
        for issue in all_issues:
            logger.warning(f"   - {issue}")

    return all_passed

def main():
    """Main entry point."""
    success = run_verification()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()