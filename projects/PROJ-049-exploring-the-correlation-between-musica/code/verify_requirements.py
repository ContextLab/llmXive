import subprocess
import sys
from pathlib import Path

def normalize(line):
    """
    Normalize a requirement line to lowercase package name to avoid 
    casing mismatches (e.g., PyYAML vs pyyaml).
    """
    if '==' in line:
        pkg, ver = line.split('==', 1)
        return f"{pkg.lower()}=={ver}"
    return line.lower()

def main():
    """
    Verification for T002:
    1. Run pip freeze.
    2. Filter the output to only include packages listed in requirements.txt.
    3. Write this filtered list to installed.txt.
    4. Compare requirements.txt and installed.txt to ensure no version mismatches.
    """
    req_path = Path('requirements.txt')
    if not req_path.exists():
        print("Error: requirements.txt not found.")
        sys.exit(1)

    # Read required packages and versions
    with open(req_path, 'r') as f:
        # Filter out comments and empty lines
        required_lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    required_packages = {line.split('==')[0].lower() for line in required_lines}

    # 1. Run pip freeze
    try:
        result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True, check=True)
        installed_lines = result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error running pip freeze: {e}")
        sys.exit(1)

    # 2. Filter installed packages to only those in requirements.txt
    filtered_installed = []
    for line in installed_lines:
        if '==' in line:
            pkg_name = line.split('==')[0].lower()
            if pkg_name in required_packages:
                filtered_installed.append(line)
    
    # Sort both to ensure diff is based on content, not order
    required_lines.sort()
    filtered_installed.sort()

    # 3. Write to installed.txt
    with open('installed.txt', 'w') as f:
        f.write('\n'.join(filtered_installed) + '\n')

    # 4. Compare using normalization to handle casing (e.g. PyYAML vs pyyaml)
    mismatches = []
    req_set = {normalize(line) for line in required_lines}
    inst_set = {normalize(line) for line in filtered_installed}
    
    for req in req_set:
        if req not in inst_set:
            mismatches.append(req)

    if mismatches:
        print(f"Version mismatches found. Expected but not found in environment: {mismatches}")
        sys.exit(1)

    print("Verification successful: installed.txt matches requirements.txt for all pinned dependencies.")
    sys.exit(0)

if __name__ == "__main__":
    main()