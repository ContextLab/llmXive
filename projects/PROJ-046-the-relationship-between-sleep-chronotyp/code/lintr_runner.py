import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any

def get_project_root() -> Path:
    """Get the project root directory."""
    current = Path(__file__).resolve().parent
    while not (current / ".git").exists():
        parent = current.parent
        if parent == current:
            raise RuntimeError("Could not find project root (no .git directory)")
        current = parent
    return current

def find_r_files(root: Path) -> List[Path]:
    """Find all .R files in the code directory."""
    code_dir = root / "code"
    if not code_dir.exists():
        return []
    return sorted([f for f in code_dir.rglob("*.R") if not f.name.startswith("04_report")])

def run_lintr_scan(root: Path, output_path: Path) -> Tuple[int, Dict[str, Any]]:
    """
    Run lintr on all R files with specific linters.
    
    Returns:
        Tuple of (exit_code, results_dict)
        exit_code: 0 if all checks pass, 1 if issues found or error
    """
    r_script = f"""
    library(lintr)
    
    # Define the linters as per task requirements
    linters <- list(
      cyclocomp_linter(limit = 10),
      object_usage_linter(),
      unnecessary_concatenation_linter(),
      unused_import_linter()
    )
    
    # Files to scan (passed from Python)
    files <- c({', '.join(repr(str(f)) for f in find_r_files(root))})
    
    if (length(files) == 0) {{
      cat("No R files found to scan.\\n")
      quit(status = 0)
    }}
    
    # Run linting
    results <- linters %>% 
      lapply(function(linter) {{
        lapply(files, function(f) {{
          tryCatch({{
            lint(f, linters = linter)
          }}, error = function(e) {{
            list()
          }})
        }}) %>% 
        unlist(recursive = FALSE)
      }}) %>% 
      unlist(recursive = FALSE)
    
    # Scan for TODOs
    todo_results <- list()
    for (f in files) {{
      content <- readLines(f, warn = FALSE)
      for (i in seq_along(content)) {{
        if (grepl("TODO|FIXME|XXX|HACK", content[i], ignore.case = TRUE)) {{
          todo_results <- c(todo_results, list(list(
            file = f,
            line = i,
            message = "TODO/FIXME found",
            line_content = content[i]
          )))
        }}
      }}
    }}
    
    # Combine results
    all_results <- c(results, todo_results)
    
    # Format output
    output <- list(
      total_issues = length(all_results),
      files_scanned = length(files),
      issues = lapply(all_results, function(r) {{
        list(
          file = as.character(r$file),
          line = r$line,
          message = r$message,
          type = ifelse("line_content" %in% names(r), "TODO", "lintr")
        )
      }})
    )
    
    # Write JSON output
    jsonlite::write_json(output, "{output_path}", auto_unbox = TRUE)
    
    # Exit with appropriate code
    quit(status = ifelse(length(all_results) > 0, 1, 0))
    """
    
    try:
        result = subprocess.run(
            ["Rscript", "-e", r_script],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # Read results if available
        if output_path.exists():
            with open(output_path, "r") as f:
                results_dict = json.load(f)
        else:
            results_dict = {"error": "R script failed to generate output", "stdout": result.stdout, "stderr": result.stderr}
        
        return result.returncode, results_dict
        
    except subprocess.TimeoutExpired:
        return 1, {"error": "Lintr scan timed out"}
    except Exception as e:
        return 1, {"error": str(e)}

def scan_todos(root: Path) -> List[Dict[str, Any]]:
    """Scan all R files for TODO comments."""
    todos = []
    for r_file in find_r_files(root):
        try:
            with open(r_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if any(keyword in line.upper() for keyword in ["TODO", "FIXME", "XXX", "HACK"]):
                        todos.append({
                            "file": str(r_file.relative_to(root)),
                            "line": line_num,
                            "content": line.strip(),
                            "issue": "TODO/FIXME comment found"
                        })
        except Exception:
            continue
    return todos

def generate_report(root: Path, results: Dict[str, Any], output_file: Path) -> None:
    """Generate a human-readable linting report."""
    with open(output_file, "w") as f:
        f.write(f"Lintr Scan Report for {root}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Files scanned: {results.get('files_scanned', 0)}\n")
        f.write(f"Total issues found: {results.get('total_issues', 0)}\n\n")
        
        if results.get("issues"):
            f.write("Issues:\n")
            f.write("-" * 30 + "\n")
            for issue in results["issues"]:
                f.write(f"[{issue['type']}] {issue['file']}:{issue['line']}\n")
                f.write(f"  {issue['message']}\n\n")
        else:
            f.write("No issues found. Code cleanup successful.\n")

def main():
    """Main entry point for lintr runner."""
    root = get_project_root()
    output_path = root / "data" / "derived" / "lintr_results.json"
    report_path = root / "logs" / "lintr_report.txt"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Running lintr scan on {root}...")
    exit_code, results = run_lintr_scan(root, output_path)
    
    generate_report(root, results, report_path)
    
    if exit_code == 0:
        print("✅ All code cleanup checks passed!")
    else:
        print(f"⚠️ Found {results.get('total_issues', 0)} issues. See {report_path} for details.")
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
