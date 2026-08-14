"""
Script to create the specifications directory structure for the project.
This fulfills task T001e: Create `projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/specs/001-multi-property-trade-offs/` directory structure.
"""
import os
from pathlib import Path

def create_specs_directories():
    """Create the specs directory structure."""
    # Determine the project root relative to this script
    # Assuming the script is in code/ and the project root is the parent of code/
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the target directory path
    specs_dir = project_root / "specs" / "001-multi-property-trade-offs"
    
    # Create the directory structure
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a README.md to document the purpose of this directory
    readme_content = """# Specifications: Multi-Property Trade-Offs in Alloy Design

This directory contains the design documents and specifications for the multi-property trade-offs research project.

## Contents

- `spec.md`: Main project specification
- `plan.md`: Implementation plan
- `research.md`: Research notes and methodology
- `data-model.md`: Data model definitions
- `contracts/`: API and data contracts

## Purpose

This directory serves as the source of truth for the project's requirements, design decisions, and research methodology.
"""
    
    readme_path = specs_dir / "README.md"
    readme_path.write_text(readme_content)
    
    # Create a .gitkeep file to ensure the directory is tracked by git
    gitkeep_path = specs_dir / ".gitkeep"
    gitkeep_path.write_text("")
    
    print(f"Successfully created directory structure at: {specs_dir}")
    print(f"Created files:")
    print(f"  - {readme_path}")
    print(f"  - {gitkeep_path}")
    
    return specs_dir

if __name__ == "__main__":
    create_specs_directories()