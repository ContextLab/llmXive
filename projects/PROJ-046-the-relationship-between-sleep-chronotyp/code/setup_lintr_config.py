"""
Module to configure lintr for the project.
This module creates the .lintr configuration file.
"""
import os
import json
from typing import Optional
from pathlib import Path

def create_lintr_config(project_root: Path, config_path: Optional[Path] = None) -> str:
    """
    Create a .lintr configuration file for the project.
    
    Args:
        project_root: Path to the project root directory
        config_path: Optional path to the config file (defaults to project_root/.lintr)
    
    Returns:
        Path to the created config file
    """
    if config_path is None:
        config_path = project_root / ".lintr"
    
    # Define the lintr configuration
    lintr_config = {
        "exclude_linters": [
            "object_usage_linter",
            "library_call_linter"
        ],
        "linters": [
            "line_length_linter(120)",
            "object_name_linter('snake_case')",
            "assignment_linter('->')",
            "whitespace_linter()",
            "commented_code_linter()",
            "trailing_whitespace_linter()",
            "brace_linter()",
            "commas_linter()",
            "spaces_inside_linter()",
            "spaces_left_parentheses_linter()",
            "paren_body_linter()",
            "single_quotes_linter()",
            "unnecessary_concatenation_linter()",
            "redundant_ifelse_linter()",
            "seq_linter()",
            "no_tab_linter()",
            "numeric_leading_zero_linter()",
            "equals_na_linter()",
            "infix_spaces_linter()",
            "constant_comparison_linter()",
            "cyclocomp_linter(limit=15)",
            "duplicate_argument_linter()",
            "empty_assignment_linter()",
            "fixed_regex_linter()",
            "for_loop_index_linter()",
            "function_argument_linter()",
            "implicit_assignment_linter()",
            "implicit_integer_linter()",
            "inner_combine_linter()",
            "missing_package_linter()",
            "nonportable_path_linter()",
            "paren_brace_linter()",
            "pipe_continuation_linter()",
            "redundant_equals_linter()",
            "regex_subset_linter()",
            "return_linter()",
            "sort_linter()",
            "string_boundary_linter()",
            "system_file_linter()",
            "unneeded_concatenation_linter()",
            "unused_imports_linter()",
            "use_lintr()",
            "which_grepl_linter()",
            "xml_nodes_linter()",
            "yoda_test_linter()"
        ],
        "exclusions": {
            "data/*": ["all"],
            "tests/*": ["object_name_linter"],
            "code/00_config.R": ["all"],
            "code/measurements.md": ["all"]
        }
    }
    
    # Write the configuration file
    with open(config_path, 'w') as f:
        # Format as R list syntax for .lintr
        f.write("# R lintr configuration for PROJ-046\n")
        f.write("# Enforces style consistent with tidyverse and project standards\n")
        f.write("exclude_linters: [\n")
        for linter in lintr_config["exclude_linters"]:
            f.write(f"  {linter},\n")
        f.write("]\n")
        f.write("linters: [\n")
        for linter in lintr_config["linters"]:
            f.write(f"  {linter},\n")
        f.write("]\n")
        f.write("exclusions: [\n")
        for path, exclusions in lintr_config["exclusions"].items():
            f.write(f"  {path}: [\n")
            for excl in exclusions:
                f.write(f"    {excl},\n")
            f.write("  ]\n")
        f.write("]\n")
    
    return str(config_path)

def main():
    """Main entry point."""
    from pathlib import Path
    import sys
    
    # Find project root
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "code").exists() and (current / "data").exists():
            project_root = current
            break
        current = current.parent
    else:
        print("ERROR: Could not find project root")
        sys.exit(1)
    
    print(f"Creating lintr config at {project_root}/.lintr")
    config_path = create_lintr_config(project_root)
    print(f"SUCCESS: Created {config_path}")

if __name__ == "__main__":
    main()
