"""T001a: Ensure the code/ directory exists at the repository root.

Creates the directory (idempotent) and writes a marker file so the
directory's presence is verifiable in version control.
"""
from llmxive_toolkit import paths

code_dir = paths.code()
marker = code_dir / ".gitkeep"
marker.touch(exist_ok=True)
print(f"code/ directory ready at: {code_dir}")