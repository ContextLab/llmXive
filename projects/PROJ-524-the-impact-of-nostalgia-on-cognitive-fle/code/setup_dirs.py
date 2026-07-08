import os
import sys

def main():
    """
    Creates necessary directories for the project structure.
    Specifically creates the stimuli directory under data/.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stimuli_dir = os.path.join(project_root, 'data', 'stimuli')
    
    if not os.path.exists(stimuli_dir):
        os.makedirs(stimuli_dir)
        print(f"Created directory: {stimuli_dir}")
    else:
        print(f"Directory already exists: {stimuli_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
