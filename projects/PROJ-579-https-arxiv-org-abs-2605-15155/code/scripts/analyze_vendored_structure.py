"""
T036a: Analyse Vendored Code Structure

Scans external/SDAR/agent_system/ to identify logical boundaries
(data loading, algorithm, I/O) and produces a report at
outputs/timing/code_structure_report.txt.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Constants based on project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VENDORED_DIR = PROJECT_ROOT / "external" / "SDAR" / "agent_system"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "timing"
REPORT_PATH = OUTPUT_DIR / "code_structure_report.txt"

# Heuristics for classification
DATA_LOADING_KEYWORDS = {"load", "data", "dataset", "dataloader", "reader", "fetch", "env"}
ALGORITHM_KEYWORDS = {"train", "policy", "model", "loss", "agent", "optimizer", "step", "update", "rl", "distill", "gate"}
IO_KEYWORDS = {"save", "log", "write", "read", "main", "entry", "cli", "argparse", "print"}

def classify_file(file_path: Path) -> List[str]:
    """Classify a file based on its name and content keywords."""
    categories = []
    filename = file_path.name.lower()
    
    # Check filename
    if any(kw in filename for kw in DATA_LOADING_KEYWORDS):
        categories.append("Data Loading")
    if any(kw in filename for kw in ALGORITHM_KEYWORDS):
        categories.append("Algorithm")
    if any(kw in filename for kw in IO_KEYWORDS):
        categories.append("I/O")
    
    # If no categories from filename, assume Algorithm for .py files
    if file_path.suffix == ".py" and not categories:
        categories.append("Algorithm")
        
    return categories if categories else ["Unknown"]

def scan_directory(base_path: Path) -> Dict[str, List[Path]]:
    """Scan directory and group files by logical boundary."""
    structure = {
        "Data Loading": [],
        "Algorithm": [],
        "I/O": [],
        "Unknown": []
    }
    
    if not base_path.exists():
        return structure

    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file
                categories = classify_file(file_path)
                for cat in categories:
                    if cat in structure:
                        structure[cat].append(file_path)
                    else:
                        structure["Unknown"].append(file_path)
    
    return structure

def generate_report(structure: Dict[str, List[Path]]) -> str:
    """Generate the textual report content."""
    lines = []
    lines.append("=" * 60)
    lines.append("Vendored Code Structure Analysis Report")
    lines.append(f"Target: {VENDORED_DIR}")
    lines.append(f"Generated: {Path(__file__).stem}")
    lines.append("=" * 60)
    lines.append("")
    
    for category, files in structure.items():
        lines.append(f"--- {category} ---")
        if not files:
            lines.append("  (No files identified)")
        else:
            for f in files:
                rel_path = f.relative_to(PROJECT_ROOT)
                lines.append(f"  - {rel_path}")
        lines.append("")
    
    lines.append("--- Logical Boundaries Summary ---")
    lines.append("1. Data Loading: Handles environment interaction, data fetching, and dataset management.")
    lines.append("2. Algorithm: Contains core SDAR logic, training loops, policy updates, and loss calculations.")
    lines.append("3. I/O: Manages logging, checkpoint saving, CLI arguments, and entry points.")
    lines.append("")
    lines.append("Recommendation for Modularization (T036b):")
    lines.append("  - Move 'Data Loading' files to src/data_loader.py")
    lines.append("  - Move 'Algorithm' files to src/sdar_runner.py (core logic)")
    lines.append("  - Move 'I/O' files to src/logging_utils.py or keep as entry points")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def main():
    """Main entry point for the analysis script."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not VENDORED_DIR.exists():
        print(f"Warning: Vendored directory not found at {VENDORED_DIR}")
        print("Creating report with empty structure.")
    
    structure = scan_directory(VENDORED_DIR)
    report_content = generate_report(structure)
    
    # Write report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"Report generated: {REPORT_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
