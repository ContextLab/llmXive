"""
Script to initialize the llmXive project directory structure.
Creates all required directories for features, modeling, data, and tests.
"""
import os
from pathlib import Path

# Define the directory structure relative to the project root
# Based on T001: mkdir -p src/features src/modeling src/intervention src/eval src/utils data/raw data/processed data/results data/models tests/unit tests/integration tests/contract
# Note: The task description mentions 'src/' but the project plan context implies 'code/' or root.
# Given the constraint "Stay inside the project tree... under code/, data/, tests/",
# and the task description explicitly says "src/", we will create 'code/src' to align with
# the project's path convention (code/) while respecting the task's structural intent (src/).
# However, looking at T001 text: "Create project structure: mkdir -p src/features..."
# And constraint 4: "All artifact paths are relative to the project root and MUST live under code/, data/, tests/..."
# We will map 'src' -> 'code/src' to satisfy both the task's structural requirement and the project's path convention.

# Re-reading T001 carefully: "Create project structure: mkdir -p src/features..."
# If the project root is the repo root, and the task says 'src', but the system prompt says 'code/',
# I will create the directories under 'code/' to strictly follow the system prompt's path convention
# while maintaining the internal structure requested (features, modeling, etc).
# Actually, the task says "src/features". The system prompt says "under code/, data/, tests/".
# To be safe and compliant with the system prompt's explicit path constraints, I will create:
# code/features, code/modeling, etc.
# Wait, the task description is the source of truth for *what* to build. The system prompt is the constraint for *where*.
# If the task says "src/features", and the system says "must live under code/", I will create "code/src/features"?
# No, "src" usually implies the source code root. If the system prompt enforces "code/" as the root for code,
# then "code/features" is the equivalent of "src/features" in a standard repo.
# Let's look at the task again: "mkdir -p src/features src/modeling..."
# I will create these directories relative to the current working directory (project root).
# To comply with "MUST live under code/", I will create them under 'code/'.

# Let's refine: The task asks for 'src/features'. The system says 'code/'.
# I will create 'code/features', 'code/modeling', etc. This preserves the internal structure
# (features, modeling, etc) while adhering to the system's path constraint.

base_dirs = [
    # Source Code Structure (mapped from src/ to code/)
    "code/features",
    "code/modeling",
    "code/intervention",
    "code/eval",
    "code/utils",
    
    # Data Structure
    "data/raw",
    "data/processed",
    "data/results",
    "data/models",
    
    # Tests Structure
    "tests/unit",
    "tests/integration",
    "tests/contract"
]

def main():
    project_root = Path(".")
    created_count = 0
    
    print(f"Initializing project structure at: {project_root.absolute()}")
    
    for dir_path in base_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
    
    print(f"Project structure initialization complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()