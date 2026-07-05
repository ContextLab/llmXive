"""Script to create the specs directory structure."""

import os
import sys
from pathlib import Path

def create_specs_directory_structure():
    """Create the specs directory structure and placeholder files."""
    base_path = Path(__file__).parent.parent
    specs_dir = base_path / 'specs' / '001-assessing-the-impact-of-sample-size-on-t'
    
    specs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create placeholder files
    placeholder_files = {
        'design.md': '# Design Document\n\nPlaceholder for design details.',
        'spec.md': '# Specification\n\nPlaceholder for user stories and requirements.',
        'plan.md': '# Project Plan\n\nPlaceholder for project plan.',
        'research.md': '# Research Notes\n\nPlaceholder for research notes.',
        'data-model.md': '# Data Model\n\nPlaceholder for data model documentation.',
    }
    
    for filename, content in placeholder_files.items():
        file_path = specs_dir / filename
        if not file_path.exists():
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created {file_path}")
            
    print("Specs directory structure creation complete.")
    
if __name__ == '__main__':
    create_specs_directory_structure()