"""
Script to convert environment.yml to requirements.txt.
This enforces the 'Single Source of Truth' principle for dependencies.
"""
import sys
import os
import re
from pathlib import Path

def parse_environment_yml(filepath):
    """
    Parse a conda environment.yml file and extract pip-installable packages.
    Handles nested 'pip' sections and top-level conda packages.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Environment file not found: {filepath}")

    packages = []
    in_pip_section = False

    with open(filepath, 'r') as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue

        # Detect section headers
        if stripped.startswith('dependencies:'):
            in_pip_section = False
            continue

        if stripped.startswith('- pip:'):
            in_pip_section = True
            continue

        # Parse list items
        if stripped.startswith('- '):
            item = stripped[2:].strip()
            
            if in_pip_section:
                # Direct pip package specification (e.g., package==1.0, git+https://...)
                if item:
                    packages.append(item)
            else:
                # Top-level conda package (e.g., python=3.9, numpy, pandas=1.5)
                # We extract the package name and version, converting to pip format
                pkg_name = item
                version = ""
                
                # Handle different version specifiers: =, ==, -, etc.
                # Conda often uses = for equality, pip uses ==
                if '=' in pkg_name:
                    # Split on first '=' to separate name and version
                    parts = pkg_name.split('=', 1)
                    pkg_name = parts[0].strip()
                    version_part = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Convert conda version specifiers to pip format
                    # Conda: numpy=1.21 -> pip: numpy==1.21
                    if version_part:
                        version = "==" + version_part
                
                # Only include non-python packages or python with version
                if pkg_name.lower() != 'python':
                    packages.append(f"{pkg_name}{version}")
                elif version:
                    # Keep python version if specified
                    packages.append(f"{pkg_name}{version}")

    return packages

def clean_package_name(name):
    """
    Ensure package name is in standard format for pip.
    Conda sometimes uses different casing or underscores.
    PEP 503 standard normalization: lowercase, replace underscores/hyphens with hyphens.
    """
    # Standardize to lowercase and replace underscores with hyphens
    return name.lower().replace('_', '-')

def main():
    """
    Main entry point to generate requirements.txt from environment.yml.
    """
    # Determine paths relative to this script's location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    env_file = project_root / 'environment.yml'
    req_file = project_root / 'requirements.txt'

    if not env_file.exists():
        print(f"Error: {env_file} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {env_file}...")
    try:
        packages = parse_environment_yml(env_file)
    except Exception as e:
        print(f"Error parsing environment file: {e}", file=sys.stderr)
        sys.exit(1)

    # Clean and deduplicate
    # Normalize names and keep the first occurrence of each normalized name
    seen = set()
    unique_packages = []
    for pkg in packages:
        # Extract base name for deduplication (before version specifier)
        base_name = re.split(r'[<>=!~]', pkg)[0].strip()
        normalized_name = clean_package_name(base_name)
        
        if normalized_name not in seen:
            seen.add(normalized_name)
            unique_packages.append(pkg)

    # Filter out python version specifiers that aren't pip compatible
    # e.g., "python=3.9" -> keep, but "python" alone might be redundant
    final_packages = []
    for pkg in unique_packages:
        # Skip if it's just 'python' without version
        if pkg.lower() == 'python':
            continue
        final_packages.append(pkg)

    if not final_packages:
        print("Warning: No valid packages found to write to requirements.txt")
        # Create empty file to satisfy build systems
        req_file.write_text("")
        return

    # Write to requirements.txt
    with open(req_file, 'w') as f:
        f.write("# Auto-generated from environment.yml\n")
        f.write("# Do not edit manually. Edit environment.yml instead.\n")
        f.write("\n")
        for pkg in final_packages:
            f.write(f"{pkg}\n")

    print(f"Successfully wrote {len(final_packages)} packages to {req_file}")

if __name__ == '__main__':
    main()