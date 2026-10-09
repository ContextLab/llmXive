"""Conservative PR check selection; unknown paths always retain live coverage."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def select(paths: list[str]) -> dict[str, bool]:
    offline = live = False
    for path in paths:
        # These are audit records or human documentation, never runtime prompts.
        if path in {"README.md", "CLAUDE.md", "AGENTS.md", "LICENSE"}:
            continue
        offline = True
        if path.startswith(("tests/unit/", "tests/contract/", "web/", "docs/", "notes/")):
            continue
        live = True
    return {"offline": offline, "live": live}


def main() -> None:
    pages = json.loads(Path(sys.argv[1]).read_text())
    if not isinstance(pages, list) or any(not isinstance(p, list) for p in pages):
        raise ValueError("expected paginated GitHub changed-file arrays")
    paths = []
    for page in pages:
        for item in page:
            paths.append(item["filename"])
            if item.get("previous_filename"):
                paths.append(item["previous_filename"])
    result = select(paths)
    # GitHub limits this endpoint to 3000 files. Never infer a safe skip from
    # an empty/truncated list; a manual dispatch also supplies this sentinel.
    if not paths or sum(map(len, pages)) >= 3000:
        result = {"offline": True, "live": True}
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write("".join(f"{key}={str(value).lower()}\n" for key, value in result.items()))
    print(json.dumps({"changed_paths": len(paths), **result}))


if __name__ == "__main__":
    main()
