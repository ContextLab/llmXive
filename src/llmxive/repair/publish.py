"""Apply a validated candidate for the separate PR-publishing CI job.

This module runs from the trusted base checkout, not the candidate. Never runs
model-authored code. A stale source hash rejects publication rather than merging
an untested candidate onto changed platform code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from llmxive.repair.runner import validate_proposal


def apply(repo: Path, output: Path) -> dict:
    result = json.loads((output / "result.json").read_text())
    if (
        result.get("status") != "validated_candidate"
        or result.get("review", {}).get("accept") is not True
        or result.get("safety_exit") != 0
    ):
        raise ValueError("candidate has not passed tests, fixed preservation checks and independent review")
    evidence = json.loads((output / "evidence.json").read_text())
    review = json.loads((output / "review.json").read_text())
    if (
        review != result["review"]
        or hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        != result["evidence_sha256"]
    ):
        raise ValueError("candidate evidence or review changed after validation")
    proposal = json.loads((output / "proposal.json").read_text())
    files, _, _ = validate_proposal(proposal, repo)
    if set(result["base_files"]) != set(files):
        raise ValueError("candidate paths do not match validated baseline")
    for name in files:
        path = repo / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if digest != result["base_files"][name]:
            raise ValueError(f"platform changed after validation: {name}")
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    body = (
        proposal["explanation"] + "\n\nValidation: the new regression failed against the baseline "
        "and passed with the fix; related existing tests and fixed preservation tests passed in containers without credentials "
        "or network access. Independently reviewed by " + result["reviewer_model"] + ".\n\n"
        "Regression: `" + result["regression"] + "`.\n\n"
        "This is a repair candidate, not an automatically merged change.\n"
    )
    (output / "pr-body.md").write_text(body)
    (output / "pr-title.txt").write_text(proposal["title"][:200])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    apply(Path.cwd(), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
