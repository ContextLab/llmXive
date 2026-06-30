"""
Script to initialize the Python project requirements.
Writes the specific list of dependencies to code/requirements.txt.
"""
import os

REQUIRED_PACKAGES = [
    "pandas",
    "scikit-learn",
    "xgboost",
    "pymatgen",
    "requests",
    "pyyaml",
    "matplotlib",
    "seaborn",
    "statsmodels",
    "pytest",
]

def main():
    # Ensure the code directory exists if the script is run from root
    # The task specifies the output path as code/requirements.txt
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "code")
    output_file = os.path.join(output_dir, "requirements.txt")

    # Create directory if it doesn't exist (though T001 should have done this)
    os.makedirs(output_dir, exist_ok=True)

    # Write the requirements
    with open(output_file, "w") as f:
        for package in REQUIRED_PACKAGES:
            f.write(f"{package}\n")

    print(f"Successfully wrote requirements to {output_file}")
    print("Dependencies included:")
    for package in REQUIRED_PACKAGES:
        print(f"  - {package}")

if __name__ == "__main__":
    main()