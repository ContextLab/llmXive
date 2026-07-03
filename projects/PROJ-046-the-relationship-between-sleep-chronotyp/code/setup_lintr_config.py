import os
import json
from typing import Optional

def create_lintr_config(project_root: str = ".") -> str:
    """
    Creates the .lintr configuration file for the project.
    
    Args:
        project_root: The root directory of the project.
        
    Returns:
        The path to the created file.
    """
    config_path = os.path.join(project_root, "code", ".lintr")
    
    # Ensure the code directory exists
    code_dir = os.path.join(project_root, "code")
    os.makedirs(code_dir, exist_ok=True)
    
    config_content = """# lintr configuration for PROJ-046
# Enforces consistent style for R scripts in the chronotype-moral-judgement pipeline
exclusions: list()
linters: list(
  # General style
  absolute_path_linter(),
  assignment_linter(),
  braces_linter(),
  commas_linter(),
  commented_code_linter(),
  commented_todos_linter(),
  equals_na_linter(),
  function_left_parentheses_linter(),
  infix_spaces_linter(),
  line_length_linter(120),
  object_length_linter(50),
  object_name_linter(),
  object_usage_linter(),
  paren_body_linter(),
  pipe_continuation_linter(),
  quotes_linter(),
  semicolons_linter(),
  spaces_inside_linter(),
  spaces_left_parentheses_linter(),
  trailing_blank_lines_linter(),
  trailing_whitespace_linter(),
  unnecessary_concatenation_linter(),
  whitespace_linter()
)
"""
    
    with open(config_path, 'w') as f:
        f.write(config_content)
        
    return config_path

def main():
    """Main entry point for the script."""
    # Determine project root (assuming script is in code/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    config_path = create_lintr_config(project_root)
    print(f"lintr configuration created at: {config_path}")

if __name__ == "__main__":
    main()