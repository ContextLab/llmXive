import os

def main():
    # Define the directory structure required by the project
    directories = [
        "data/raw",
        "data/processed",
        "code/tests/unit",
        "code/tests/integration",
        "output/results",
        "output/plots",
        "output/reports",
        "output/exploratory"
    ]

    # Create directories
    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create requirements.txt
    requirements_content = """pandas
numpy
scipy
networkx
matplotlib
seaborn
pytest
"""
    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    print("Created requirements.txt")

if __name__ == "__main__":
    main()