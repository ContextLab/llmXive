import os
from pathlib import Path

def main():
    """Configure linting and formatting tools."""
    # Create .ruff.toml
    ruff_config = """[lint]
    select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
    ignore = ["E501", "B008"]
    target-version = "py311"

    [format]
    line-length = 100
    quote-style = "double"
    indent-style = "space"
    """
    
    Path(".ruff.toml").write_text(ruff_config)
    print("Created .ruff.toml")

    # Create pyproject.toml for black
    black_config = """[tool.black]
    line-length = 100
    target-version = ['py311']
    """
    
    Path("pyproject.toml").write_text(black_config)
    print("Created pyproject.toml with Black configuration")

if __name__ == "__main__":
    main()
