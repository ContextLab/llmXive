#!/usr/bin/env bash
# T005 verification: pyproject.toml parses as valid TOML and
# `ruff check code/` passes with real rules enabled (no select = []).
set -euo pipefail
cd "$(dirname "$0")/../.."

python - <<'EOF'
import tomllib
from pathlib import Path

cfg_path = Path("code/pyproject.toml")
with cfg_path.open("rb") as f:
    cfg = tomllib.load(f)

ruff = cfg["tool"]["ruff"]
black = cfg["tool"]["black"]
assert ruff["line-length"] == 100, "ruff line-length must be 100"
assert ruff["target-version"] == "py311", "ruff target must be py311"
assert black["line-length"] == 100, "black line-length must be 100"
assert "py311" in black["target-version"], "black target must include py311"
assert ruff.get("select"), "ruff select must enable a real rule set (not empty)"
print("pyproject.toml: valid TOML with required [tool.ruff]/[tool.black] settings")
EOF

ruff check code/
echo "T005 verification passed: ruff check code/ reported zero errors with checks enabled"