"""Tests to ensure the Makefile runs the validation script after each target."""

import re
from pathlib import Path

MAKEFILE_PATH = Path(__file__).resolve().parents[2] / "Makefile"

# List of primary pipeline targets that should invoke validation.
# The 'validate' target itself is excluded because it is the validation step.
PIPELINE_TARGETS = [
    "download",
    "batch_correct",
    "normalize",
    "filter",
    "correlation_extract",
    "evaluate",
    "enrich",
    "clean",
    "sensitivity",
    "reproducibility-check",
    "all",
]


def _parse_makefile():
    """Parse the Makefile into a mapping of target -> list of recipe lines."""
    target_pattern = re.compile(r"^([a-zA-Z0-9_-]+):")
    current_target = None
    targets = {}
    with MAKEFILE_PATH.open() as f:
        for line in f:
            stripped = line.rstrip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue
            target_match = target_pattern.match(stripped)
            if target_match:
                current_target = target_match.group(1)
                targets[current_target] = []
                continue
            # Recipe lines start with a tab character
            if stripped.startswith("\t") and current_target:
                # Remove leading tab for easier inspection
                recipe_line = stripped.lstrip("\t")
                targets[current_target].append(recipe_line)
    return targets


def test_validation_invoked_for_each_target():
    """Ensure every pipeline target (except the validate target itself) calls the validation script."""
    targets = _parse_makefile()
    missing = []
    for tgt in PIPELINE_TARGETS:
        # Skip if the target is not defined in the Makefile (test will fail)
        if tgt not in targets:
            missing.append(f"{tgt} (target not defined)")
            continue
        # Check if any recipe line contains the validation invocation
        if not any("python -m src.pipeline.validate" in line for line in targets[tgt]):
            missing.append(tgt)
    assert not missing, f"The following targets do not invoke validation: {', '.join(missing)}"


def test_validate_target_exists_and_calls_validation():
    """The explicit `validate` target must exist and run the validation script."""
    targets = _parse_makefile()
    assert "validate" in targets, "Missing `validate` target in Makefile"
    # The validate target should have exactly one command invoking the script
    validation_calls = [
        line for line in targets["validate"] if "python -m src.pipeline.validate" in line
    ]
    assert validation_calls, "`validate` target does not run the validation script"
    assert len(validation_calls) == 1, "`validate` target should run the validation script exactly once"