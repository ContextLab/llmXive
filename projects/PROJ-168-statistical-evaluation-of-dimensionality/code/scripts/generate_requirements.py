"""
Script to automatically convert environment.yml to requirements.txt using pip-tools.

This script reads the project's environment.yml file, extracts the dependencies,
and uses pip-compile to generate a fully resolved requirements.txt with pinned versions.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def find_environment_yml():
    """Find environment.yml in the project root or parent directories."""
    current = Path(__file__).resolve()
    # Search up to 5 levels
    for _ in range(5):
        env_file = current / "environment.yml"
        if env_file.exists():
            return env_file
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    # Check project root explicitly if not found
    project_root = Path(__file__).resolve().parent.parent
    env_file = project_root / "environment.yml"
    if env_file.exists():
        return env_file
    
    raise FileNotFoundError(
        "Could not find environment.yml. Please ensure it exists in the project root."
    )

def convert_yaml_to_pip_requirements(env_file: Path) -> str:
    """
    Convert environment.yml to a pip-compatible requirements format.
    
    We create a temporary requirements file that pip-compile can understand,
    filtering out conda-only packages that don't have pip equivalents.
    """
    import yaml
    
    with open(env_file, 'r') as f:
        env_data = yaml.safe_load(f)
    
    dependencies = env_data.get('dependencies', [])
    pip_deps = []
    
    # Common conda-only packages that should be skipped or mapped
    conda_only = {'conda-forge', 'defaults'}
    pip_mapping = {
        'scikit-learn': 'scikit-learn',
        'scikit-misc': 'scikit-misc',
        'umap-learn': 'umap-learn',
        'leidenalg': 'leidenalg',
        'snakemake': 'snakemake',
        'statsmodels': 'statsmodels',
        'geoparse': 'geoparse',  # Note: GEOparse might be conda-only, check if pip exists
    }
    
    for dep in dependencies:
        if isinstance(dep, dict):
            # Handle pip section in conda env
            if 'pip' in dep:
                for pip_dep in dep['pip']:
                    pip_deps.append(pip_dep)
            continue
        
        if dep in conda_only:
            continue
        
        # Check if it's a conda-only package
        if dep.lower() in ['geoparse']:
            # GEOparse is often conda-only, but let's try pip
            pip_deps.append('GEOparse>=3.0.0')
            continue
        
        # Simple version parsing (e.g., "pandas>=2.0.0" -> "pandas>=2.0.0")
        if '>=' in dep or '<=' in dep or '==' in dep or '>' in dep or '<' in dep:
            pip_deps.append(dep)
        else:
            # Package name only, let pip-compile resolve the version
            pip_deps.append(dep)
    
    return '\n'.join(pip_deps)

def run_pip_compile(temp_req_file: Path, output_file: Path):
    """Run pip-compile to generate the requirements.txt."""
    try:
        # Ensure pip-tools is installed
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-q', 'pip-tools'],
            check=True,
            capture_output=True
        )
        
        # Run pip-compile
        result = subprocess.run(
            [
                sys.executable, '-m', 'piptools', 'compile',
                '--no-header',  # Don't include the header comments
                '--resolver=backtracking',
                '--strip-extras',
                str(temp_req_file),
                '--output-file', str(output_file)
            ],
            check=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Successfully generated {output_file}")
            return True
        else:
            print(f"pip-compile failed: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Error running pip-compile: {e}")
        if hasattr(e, 'stderr'):
            print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    """Main entry point for the script."""
    print("Starting requirements generation...")
    
    # Find environment.yml
    try:
        env_file = find_environment_yml()
        print(f"Found environment.yml at: {env_file}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Determine output path
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    output_file = project_root / "code" / "requirements.txt"
    
    # Create temporary file for pip-compile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
        temp_req_file = Path(tmp.name)
        try:
            # Convert and write temporary requirements
            pip_requirements = convert_yaml_to_pip_requirements(env_file)
            tmp.write(pip_requirements)
            tmp.flush()
            
            print(f"Created temporary requirements file: {temp_req_file}")
            print(f"Dependencies to compile:\n{pip_requirements}")
            
            # Run pip-compile
            success = run_pip_compile(temp_req_file, output_file)
            
            if success:
                print(f"\nFinal requirements.txt created at: {output_file}")
                print("\nGenerated content:")
                with open(output_file, 'r') as f:
                    print(f.read())
                sys.exit(0)
            else:
                print("\nFailed to generate requirements.txt")
                sys.exit(1)
                
        finally:
            # Clean up temporary file
            if temp_req_file.exists():
                temp_req_file.unlink()

if __name__ == "__main__":
    main()