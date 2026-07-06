"""
Setup script for linting (ruff) and formatting (black) tools.
This task creates the configuration files and ensures dependencies are listed.
"""
import os
from pathlib import Path

def create_config_files():
    """Create .ruff.toml and .black.toml in the code/ directory."""
    base_dir = Path(__file__).parent
    
    # Ensure base directory exists
    base_dir.mkdir(parents=True, exist_ok=True)

    # Ruff configuration
    ruff_config = base_dir / ".ruff.toml"
    if not ruff_config.exists():
        ruff_config.write_text(
            "[lint]\n"
            "select = [\"E\", \"F\", \"W\", \"I\", \"N\", \"UP\", \"B\", \"C4\", \"SIM\"]\n"
            "ignore = [\"E501\", \"W292\"]\n"
            "\n"
            "[format]\n"
            "quote-style = \"double\"\n"
            "indent-style = \"space\"\n"
            "line-length = 88\n"
        )
        print(f"Created {ruff_config}")
    else:
        print(f"{ruff_config} already exists.")

    # Black configuration
    black_config = base_dir / ".black.toml"
    if not black_config.exists():
        black_config.write_text(
            "[tool.black]\n"
            "line-length = 88\n"
            "target-version = ['py311']\n"
            "include = '\\.pyi?$'\n"
            "extend-exclude = '''\n"
            "/(\n"
            "  \\.git\n"
            "  | \\.hg\n"
            "  | \\.mypy_cache\n"
            "  | \\.tox\n"
            "  | \\.venv\n"
            "  | _build\n"
            "  | buck-out\n"
            "  | build\n"
            "  | dist\n"
            ")/\n"
            "'''\n"
        )
        print(f"Created {black_config}")
    else:
        print(f"{black_config} already exists.")

    # Update requirements.txt if necessary
    req_file = base_dir / "requirements.txt"
    if req_file.exists():
        content = req_file.read_text()
        new_deps = ["ruff", "black"]
        updated = False
        for dep in new_deps:
            if dep not in content:
                content += f"{dep}\n"
                updated = True
        if updated:
            req_file.write_text(content)
            print(f"Updated {req_file} with new dependencies.")
        else:
            print(f"{req_file} already contains required dependencies.")
    else:
        # If requirements.txt doesn't exist, create it with dependencies
        req_file.write_text("ruff\nblack\n")
        print(f"Created {req_file} with linting dependencies.")

if __name__ == "__main__":
    create_config_files()