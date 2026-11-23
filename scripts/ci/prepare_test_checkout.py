"""Materialize real PDF and project-template inputs without research datasets."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path


def prepare(repo: Path) -> list[str]:
    # Read the test's existing sample size so CI cannot silently shrink coverage
    # or drift when the real-PDF regression sample changes.
    source = ast.parse((repo / "tests/unit/test_audit_pdf.py").read_text())
    count = next(
        ast.literal_eval(node.value)
        for node in source.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "_SAMPLE_SIZE" for t in node.targets)
    )
    if type(count) is not int or count < 1:
        raise ValueError("invalid real-PDF sample size")
    paths = (
        subprocess.check_output(
            ["git", "ls-tree", "-rz", "--name-only", "HEAD", "docs/papers"],
            cwd=repo,
        )
        .decode()
        .split("\0")
    )
    selected = sorted(p for p in paths if p.endswith(".pdf"))[:count]
    if len(selected) != count:
        raise RuntimeError("real PDF audit sample is missing; refusing reduced coverage")
    # test_template_sync parametrizes itself from every tracked project copy.
    # Omitting those would silently remove thousands of regression checks.
    template_paths = (
        subprocess.check_output(
            ["git", "ls-tree", "-rz", "--name-only", "HEAD", "projects"], cwd=repo
        )
        .decode()
        .split("\0")
    )
    templates = [
        p
        for p in template_paths
        if len(Path(p).parts) == 5 and Path(p).parts[2:4] == (".specify", "templates")
    ]
    subprocess.run(
        ["git", "sparse-checkout", "add", "--stdin"],
        cwd=repo,
        input="\n".join("/" + p for p in selected + templates) + "\n",
        text=True,
        check=True,
    )
    if not all((repo / path).is_file() for path in selected + templates):
        raise RuntimeError("real PDF sample checkout did not materialize")
    print("Real PDF sample: " + ", ".join(selected))
    print(f"Project template files: {len(templates)}")
    return selected


if __name__ == "__main__":
    prepare(Path.cwd())
