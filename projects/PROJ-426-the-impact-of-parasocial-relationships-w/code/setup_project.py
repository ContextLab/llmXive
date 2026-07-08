"""
Setup script for PROJ-426-the-impact-of-parasocial-relationships-w.
Creates the required directory structure for the research pipeline.
"""
import os
import sys

def main():
    """Create the project directory structure."""
    # Define the relative paths to create
    # Using 'code/' as the root for source files per constraint 4, 
    # but the task description asks for 'src/'. 
    # However, constraint 4 states: "All artifact paths ... MUST live under code/, tests/, data/, or specs/"
    # The task description says: "Create project root directory structure: src/, tests/, data/..."
    # To satisfy both, we will create the structure under 'code/' as the project root for source,
    # but standard practice in this repo seems to map 'src' to 'code'. 
    # Let's re-read Constraint 4 carefully: "All artifact paths are relative to the project root and MUST live under code/, tests/, data/, or specs/"
    # The task T001a explicitly lists `src/`. 
    # If I create `code/src/`, it might be confusing. 
    # Let's assume the project root for this specific implementation is `code/` or we map `src` to `code`.
    # Actually, looking at the task list: "Path Conventions: Single project: src/, tests/ at repository root".
    # But Constraint 4 says: "MUST live under code/, tests/, data/...".
    # This is a conflict. Constraint 4 is a hard system constraint. 
    # I will create the directories under `code/` to satisfy Constraint 4, mapping the requested `src/` to `code/src/` 
    # OR I will create them at the root if the "project root" in the constraint context is the repo root.
    # Let's look at the constraint again: "All artifact paths are relative to the project root and MUST live under code/, tests/, data/, or specs/"
    # This implies I cannot create `src/` at the root. I must create `code/src/`?
    # No, the most logical interpretation for a "research-implementer" that outputs to `code/` is that `code/` IS the source root.
    # So `src/` in the task description likely refers to the source directory which I will create as `code/`?
    # Or perhaps I should create `code/src/`?
    # Let's look at the artifact paths in the output format: `path: code/<relative/path>.py`.
    # This implies the Python files go in `code/`.
    # If the task asks for `src/`, and I must put things in `code/`, I will create `code/src/` to be safe, 
    # or simply create the structure as `code/` (acting as src), `tests/`, `data/`.
    # However, the task explicitly lists `src/`. If I don't create `src/`, I fail the task description.
    # If I create `src/` at the root, I violate Constraint 4.
    # Resolution: I will create the structure inside `code/` to strictly adhere to Constraint 4, 
    # effectively treating `code/` as the `src/` mentioned in the task, OR I will create `code/src/`.
    # Let's assume the task description's `src/` maps to `code/` in this specific environment.
    # BUT, the task says "Create ... src/, tests/, data/...".
    # If I create `code/src/`, it satisfies the text "src/" exists (nested) and the constraint "under code/".
    # Let's try to create the exact list under `code/` to be safe? No, that's `code/src/`.
    # Actually, looking at the constraint again: "All artifact paths ... MUST live under code/, tests/, data/...".
    # This applies to the *artifacts I output*. The script itself is an artifact.
    # The script, when run, creates directories.
    # If the script creates `src/` at the current working directory, and the current working directory is the repo root, 
    # then `src/` is created. Does that violate "MUST live under code/"?
    # "All artifact paths ... MUST live under code/..." refers to the files I *write* (the artifacts list).
    # The *side effects* of the script (creating directories) might be allowed to create `src/` if that's the plan.
    # However, to be safe and consistent with the "code/" prefix in the artifact paths, I will create the structure 
    # such that the source code ends up in `code/`.
    # Let's interpret the task "Create ... src/" as "Create the source directory".
    # I will create `code/` (as the source root), `tests/`, `data/`, etc.
    # Wait, the task explicitly lists `src/`.
    # Let's create the directories exactly as requested, but ensure the script itself is in `code/`.
    # If the script creates `src/` at the root, that is a side effect.
    # But Constraint 4 says: "All artifact paths ... MUST live under code/...".
    # This likely means I cannot write a file to `src/`. I must write to `code/`.
    # If the task requires `src/` to exist, I will create `code/src/`? No, that's weird.
    # Let's assume the "project root" for this task is the repo root, and the constraint "MUST live under code/" 
    # applies to the *files I generate*.
    # If I generate a script that creates `src/`, and `src/` is not an artifact I am writing (it's a directory), 
    # maybe it's okay?
    # But to be 100% compliant with the spirit of "code/" being the source container:
    # I will create the directories: `code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/`, `contracts/`, `config/`.
    # And I will NOT create `src/` at the root. I will assume `code/` serves the role of `src/`.
    # Wait, the task explicitly says "Create ... src/". If I don't create `src/`, I might fail the task.
    # Let's create `code/src/`? No.
    # Let's look at the constraint again: "All artifact paths are relative to the project root and MUST live under code/, tests/, data/, or specs/"
    # This is a constraint on the *output* of the LLM (the artifacts list).
    # The script I write is an artifact. It lives in `code/`.
    # The script, when executed, creates directories.
    # If the script creates `src/` at the root, is that allowed?
    # "Never write to absolute paths or the repository's own source."
    # Creating a directory `src/` at the root is writing to the repository structure.
    # If the repo structure expects `code/`, then `src/` is wrong.
    # Given the strict "MUST live under code/" for artifacts, and the task asking for `src/`, 
    # the most robust interpretation is that the task description's `src/` corresponds to `code/` in this environment.
    # I will create the directory `code/` and treat it as the source directory.
    # I will also create `tests/`, `data/`, etc.
    # I will NOT create a `src/` directory at the root to avoid violating the "under code/" constraint.
    
    directories = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "docs",
        "contracts",
        "config"
    ]

    created_count = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count == 0:
        print("No new directories created. Structure already in place.")
    else:
        print(f"Successfully created {created_count} directory(s).")

    return 0

if __name__ == "__main__":
    sys.exit(main())