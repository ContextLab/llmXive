import os
from pathlib import Path

def create_directories():
    """
    Creates all required project directories for the llmXive research pipeline.
    
    This function implements tasks T001a, T001b, T001c, and T001d:
    - T001a: Root directories (code/, data/, results/, logs/)
    - T001b: Code subdirectories (simulation/, preprocessing/, analysis/, visualization/)
    - T001c: Data subdirectories (raw/, scaled/, config/)
    - T001d: Results figures and scaled data subdirectories
    
    Creates .gitkeep files in each directory to ensure they are tracked by git.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    # T001a: Root project directories
    root_dirs = [
        'code',
        'data',
        'results',
        'logs'
    ]
    
    # T001b: Code subdirectories
    code_subdirs = [
        'code/simulation',
        'code/preprocessing',
        'code/analysis',
        'code/visualization'
    ]
    
    # T001c: Data subdirectories
    data_subdirs = [
        'data/raw',
        'data/scaled',
        'data/config'
    ]
    
    # T001d: Additional directories
    additional_dirs = [
        'results/figures',
        'data/scaled/standardized',
        'data/scaled/minmax',
        'data/scaled/robust'
    ]
    
    all_dirs = root_dirs + code_subdirs + data_subdirs + additional_dirs
    
    created_count = 0
    for dir_path in all_dirs:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            # Create .gitkeep to ensure directory is tracked in git
            gitkeep_path = full_path / '.gitkeep'
            gitkeep_path.touch()
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nDirectory setup complete. Created {created_count} new directories.")
    return created_count

if __name__ == '__main__':
    create_directories()