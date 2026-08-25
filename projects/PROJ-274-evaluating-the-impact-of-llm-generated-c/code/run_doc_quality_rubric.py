"""
Runner script for Task T021c: Documentation Quality Rubric.
Executes the validation logic and writes the output artifact.
"""
import sys
import os

# Ensure the project root is in the path so we can import code modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from validation import main

if __name__ == "__main__":
    print("Running Documentation Quality Rubric (T021c)...")
    main()
    print("Done. Output written to data/raw/doc_quality_scores.json")
