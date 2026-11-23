"""
Setup script to create the requirements.txt file with pinned versions.
"""
from pathlib import Path

def main():
    base_path = Path(__file__).parent.parent
    requirements_path = base_path / "requirements.txt"
    
    requirements_content = """# llmXive Project: Neural Correlates of Anticipatory Reward Processing
# Core data processing and analysis
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.11.0
statsmodels>=0.14.0
scikit-learn>=1.3.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0

# Configuration and utilities
pyyaml>=6.0

# Testing
pytest>=7.4.0
"""
    
    requirements_path.write_text(requirements_content)
    print(f"Created requirements.txt at: {requirements_path}")
    print("Dependencies listed:")
    print(requirements_content)

if __name__ == "__main__":
    main()