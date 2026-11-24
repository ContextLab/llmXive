"""T009a: Pre-registration Draft.

Generates a preliminary ``pre-registration.json`` artifact containing the
analysis plan hash, timestamp, and parameters (R^2 target, power, alpha)
with a PLACEHOLDER predictor count. Per FR-016 this must run BEFORE the
source verification task (T011) and before any data processing.

The predictor count is a placeholder (null) at this stage because the
actual feature count is only known after source verification (T011)
succeeds; task T009 updates it later.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Analysis parameters (fixed by the spec / plan).
R2_TARGET = 0.1
POWER = 0.8
ALPHA = 0.05

# Placeholder predictor count: the true count (e.g., 21 per plan.md) is
# only confirmed after source verification (T011); T009 updates it.
PREDICTOR_COUNT_PLACEHOLDER = None

def _analysis_plan_text() -> str:
    """Return the authoritative analysis-plan text used for the hash.

    The plan is drawn from the spec's methodology (plan.md in the spec
    directory). If the file is absent, fall back to the canonical
    methodology description embedded in the spec so the hash is still
    deterministic and reproducible.
    """
    candidates = [
        paths.path("specs", "001-neural-oscillations-tDCS-biomarker", "plan.md"),
        paths.path("specs", "001-neural-oscillations-tDCS-biomarker", "spec.md"),
    ]
    for c in candidates:
        if c.is_file():
            return c.read_text(encoding="utf-8")
    return (
        "Analysis plan: band-pass filter EEG 1-45 Hz, common average "
        "reference, automated bad-channel rejection (z>5); Welch spectral "
        "power (delta, theta, alpha, beta, gamma); connectivity (PLV, wPLI) "
        "for C3-C4, C3-Cz, C4-Cz; ridge or rank-ridge regression with "
        "nested cross-validation to predict tDCS response percentage "
        "change; permutation testing (>=1000 permutations if N>=30); "
        "Benjamini-Hochberg FDR correction; sensitivity analysis over "
        "p in {0.01, 0.05, 0.1}."
    )

def compute_analysis_plan_hash() -> str:
    """SHA-256 hash of the analysis plan text."""
    return hashlib.sha256(_analysis_plan_text().encode("utf-8")).hexdigest()

def generate_pre_registration(
    r2_target: float = R2_TARGET,
    power: float = POWER,
    alpha: float = ALPHA,
    k_predictors= PREDICTOR_COUNT_PLACEHOLDER,
) -> dict:
    """Build the pre-registration document as a dict."""
    return {
        "artifact": "pre-registration",
        "task_id": "T009a",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "analysis_plan_hash": compute_analysis_plan_hash(),
        "parameters": {
            "r2_target": r2_target,
            "power": power,
            "alpha": alpha,
            "k_predictors": k_predictors,
        },
        "k_predictors_status": "placeholder" if k_predictors is None else "final",
        "notes": (
            "Preliminary pre-registration draft generated before source "
            "verification (T011). The predictor count is a placeholder "
            "and will be updated by the power analysis gate (T009) once "
            "the verified dataset and actual feature count are known."
        ),
    }

def main() -> int:
    out_path = paths.path("output", "pre-registration.json")
    doc = generate_pre_registration()
    out_path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    log.info("Pre-registration written to %s", out_path)
    # Also mirror into data/processed for pipeline consumers.
    mirror = paths.data("processed", "pre-registration.json")
    mirror.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    log.info("Mirror written to %s", mirror)
    print(json.dumps(doc, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
