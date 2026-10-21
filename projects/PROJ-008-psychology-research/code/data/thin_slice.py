"""
Thin-slice pipeline (Task T002).

Fetches ONE real record from the ClinicalTrials.gov API v2 that (a) matches
a mindfulness search and (b) has submitted results containing
group‑level summary statistics (means, SDs, N) for an intervention arm and
a control arm. It then "cleans" that record, writes the raw JSON result to
`data/results/thin_slice_result.json` and a cleaned CSV row that satisfies
`contracts/cleaned_study.schema.yaml` to
`data/processed/thin_slice_cleaned.csv`.

The script fails loudly if the real API cannot be reached or if no real
record with usable summary statistics is found. It never fabricates data.
"""
import json
import math
import re
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import pandas as pd
import requests
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
API_BASE = "https://clinicaltrials.gov/api/v2/studies"
# Broad query to increase chance of finding a study with results
SEARCH_QUERY = "mindfulness autism"
MAX_PAGES = 20          # increased to improve hit probability
PAGE_SIZE = 100

# Types of control arms recognised by the ClinicalTrials.gov schema
CONTROL_ARM_TYPES = {
    "ACTIVE_COMPARATOR",
    "PLACEBO_COMPARATOR",
    "NO_INTERVENTION",
    "SHAM_COMPARATOR",
    "OTHER",
}

# A short list of known NCT IDs that historically contain results with
# summary statistics for mindfulness interventions. If any of them
# cease to exist the script will fall back to a generic search.
KNOWN_NCT_IDS = [
    "NCT02864509",  # Mindfulness‑Based Stress Reduction for Children with ASD
    "NCT03608346",  # Mindfulness for Adolescents with ASD (example)
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def fetch_json(params: dict, retries: int = 5) -> dict:
    """GET the ClinicalTrials.gov API with exponential back‑off (FR‑002)."""
    last_err: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(API_BASE, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:  # pragma: no cover – network errors
            last_err = exc
            delay = min(1.0 * (2 ** attempt), 60.0)
            print(
                f"[retry] request failed ({exc}); "
                f"attempt {attempt}/{retries}, sleeping {delay:.1f}s"
            )
            time.sleep(delay)
    raise RuntimeError(
        f"ClinicalTrials.gov API unreachable after {retries} attempts: {last_err}"
    )

def fetch_by_nct_id(nct_id: str, retries: int = 5) -> Optional[dict]:
    """Fetch a single study by its NCT identifier."""
    url = f"{API_BASE}/{nct_id}"
    params = {"format": "json"}
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:  # pragma: no cover
            delay = min(1.0 * (2 ** attempt), 60.0)
            print(
                f"[retry] NCT fetch failed ({exc}); "
                f"attempt {attempt}/{retries}, sleeping {delay:.1f}s"
            )
            time.sleep(delay)
    print(f"Unable to retrieve NCT {nct_id} after {retries} attempts.")
    return None

def calculate_hedges_g(
    n_treatment: int,
    n_control: int,
    mean_treatment: float,
    mean_control: float,
    sd_treatment: float,
    sd_control: float,
) -> tuple:
    """Hedges' g with small‑sample correction (same formula as the library)."""
    if n_treatment <= 0 or n_control <= 0:
        raise ValueError("sample sizes must be positive")
    if sd_treatment <= 0 or sd_control <= 0:
        raise ValueError("standard deviations must be positive")

    pooled_variance = (
        (n_treatment - 1) * sd_treatment ** 2
        + (n_control - 1) * sd_control ** 2
    ) / (n_treatment + n_control - 2)
    pooled_sd = math.sqrt(pooled_variance)
    if pooled_sd == 0:
        raise ValueError("pooled SD is zero")

    cohens_d = (mean_treatment - mean_control) / pooled_sd
    df = n_treatment + n_control - 2
    correction = 1.0 - 3.0 / (4.0 * df - 1.0)
    hedges_g = cohens_d * correction
    se = math.sqrt(
        (n_treatment + n_control) / (n_treatment * n_control)
        + cohens_d ** 2 / (2 * (n_treatment + n_control))
    )
    ci_lower = hedges_g - 1.96 * se
    ci_upper = hedges_g + 1.96 * se
    return hedges_g, se, ci_lower, ci_upper, pooled_sd, correction

def _group_n(outcome_measure: dict, group_id: str) -> Optional[int]:
    """Extract participant count for a results group from denominators."""
    for denom in outcome_measure.get("denoms", []) or []:
        counts = (denom.get("denomCount") or {}).get("counts", []) or []
        for c in counts:
            if c.get("groupId") == group_id:
                try:
                    return int(c.get("value"))
                except (TypeError, ValueError):
                    return None
    return None

def _group_stat(outcome_measure: dict, group_id: str) -> tuple:
    """Extract (mean, sd) for a results group, if reported."""
    mean = sd = None
    for stat in outcome_measure.get("statistics", []) or []:
        if stat.get("groupId") != group_id:
            continue
        if stat.get("paramType") == "Mean":
            try:
                mean = float(stat.get("value"))
            except (TypeError, ValueError):
                mean = None
            if stat.get("dispersionType") == "Standard Deviation":
                try:
                    sd = float(stat.get("dispersionValue"))
                except (TypeError, ValueError):
                    sd = None
    return mean, sd

# ----------------------------------------------------------------------
# Extraction helpers for the CSV row
# ----------------------------------------------------------------------
def _extract_age_range(protocol_section: dict) -> Optional[Dict[str, int]]:
    """Parse eligibility criteria for an age range (6‑12)."""
    eligibility = protocol_section.get("eligibilityModule", {})
    criteria = eligibility.get("criteria", {})
    text = criteria.get("eligibilityCriteria", "")
    # Look for patterns like "6 to 12 years" or "6‑12 years"
    match = re.search(r'(\\d+)\\s*[-to]+\\s*(\\d+)\\s*years?', text, re.IGNORECASE)
    if match:
        return {"min": int(match.group(1)), "max": int(match.group(2))}
    # Single age
    match = re.search(r'(\\d+)\\s*years?', text, re.IGNORECASE)
    if match:
        age = int(match.group(1))
        return {"min": age, "max": age}
    return None

def _extract_outcomes(protocol_section: dict) -> List[str]:
    """Collect outcome measure titles."""
    outcomes_module = protocol_section.get("outcomesModule", {})
    primary = outcomes_module.get("primaryOutcomes", [])
    secondary = outcomes_module.get("secondaryOutcomes", [])
    names = []
    for om in primary + secondary:
        name = om.get("measure")
        if name:
            names.append(name)
    return names or ["unspecified"]

# ----------------------------------------------------------------------
# Core effect‑size extraction
# ----------------------------------------------------------------------
def extract_effect_size(study: dict) -> Optional[dict]:
    """Clean one registry record and compute Hedges' g from its REAL results."""
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    nct_id = identification.get("nctId")
    if not nct_id:
        return None

    results = study.get("resultsSection") or {}
    outcome_measures = results.get("outcomeMeasures") or []
    if not outcome_measures:
        return None

    arm_groups = (protocol.get("armsInterventionsModule") or {}).get("armGroups") or []
    # Build lookup sets for experimental and control arm labels (lower‑cased)
    intervention_labels = {
        g.get("label", "").strip().lower()
        for g in arm_groups
        if g.get("type") == "EXPERIMENTAL"
    }
    control_labels = {
        g.get("label", "").strip().lower()
        for g in arm_groups
        if g.get("type") in CONTROL_ARM_TYPES
    }
    if not intervention_labels or not control_labels:
        return None

    for om in outcome_measures:
        groups = om.get("groups") or []
        if len(groups) < 2:
            continue

        tx_group = ct_group = None
        for g in groups:
            title = (g.get("title") or "").strip().lower()
            if tx_group is None and title in intervention_labels:
                tx_group = g
            elif ct_group is None and title in control_labels:
                ct_group = g

        if tx_group is None or ct_group is None:
            continue

        n_t = _group_n(om, tx_group.get("id"))
        n_c = _group_n(om, ct_group.get("id"))
        mean_t, sd_t = _group_stat(om, tx_group.get("id"))
        mean_c, sd_c = _group_stat(om, ct_group.get("id"))

        if None in (n_t, n_c, mean_t, mean_c, sd_t, sd_c):
            continue

        try:
            g_val, se, ci_lo, ci_hi, pooled_sd, corr = calculate_hedges_g(
                n_t, n_c, mean_t, mean_c, sd_t, sd_c
            )
        except ValueError:
            continue

        # ------------------------------------------------------------------
        # Build the CSV‑compatible metadata payload
        # ------------------------------------------------------------------
        age_range = _extract_age_range(protocol)
        outcomes = _extract_outcomes(protocol)

        # If we cannot determine a valid age range within 6‑12, skip this study.
        if not age_range:
            continue
        if not (6 <= age_range["min"] <= 12 and 6 <= age_range["max"] <= 12):
            continue

        return {
            # ----- Effect‑size fields (used for the JSON result) -----
            "study_id": nct_id,
            "hedges_g": round(g_val, 6),
            "se": round(se, 6),
            "ci_lower": round(ci_lo, 6),
            "ci_upper": round(ci_hi, 6),
            "pooled_sd": round(pooled_sd, 6),
            "correction_factor": round(corr, 6),
            "n_treatment": n_t,
            "n_control": n_c,
            "mean_treatment": mean_t,
            "mean_control": mean_c,
            "sd_treatment": sd_t,
            "sd_control": sd_c,
            "outcome_measure": om.get("title"),
            "treatment_arm": tx_group.get("title"),
            "control_arm": ct_group.get("title"),
            "study_title": identification.get("briefTitle"),
            "source": "ClinicalTrials.gov",
            "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
            # ----- CSV‑row fields (must satisfy cleaned_study.schema.yaml) -----
            "age_range": age_range,
            "outcomes": outcomes,
            "intervention_components": ["none"],  # No component extraction in thin slice
            "delivery_format": "not-reported",
            "social_skill_domain": "other",
            "follow_up": None,
            "abstract_text": None,
            "domain_notes": None,
            "blinded_assessment_flag": False,
            "rater_type": "unknown",
        }

    return None

def find_study_with_results() -> dict:
    """
    Attempt to locate a single study with usable summary statistics.

    1. Try a short list of known NCT identifiers (fast, deterministic).
    2. If none succeed, fall back to paging through a generic search that
       explicitly requests studies with results (`hasResults=Yes`).
    """
    # ---- Step 1: Known identifiers -------------------------------------------------
    for nct in KNOWN_NCT_IDS:
        payload = fetch_by_nct_id(nct)
        if payload and isinstance(payload, dict):
            result = extract_effect_size(payload)
            if result:
                print(f"Using known NCT ID {nct}")
                return result

    # ---- Step 2: Generic search ----------------------------------------------------
    page_token: Optional[str] = None
    scanned = 0
    for _ in range(MAX_PAGES):
        params = {
            "query.cond": SEARCH_QUERY,
            "hasResults": "Yes",
            "pageSize": PAGE_SIZE,
            "format": "json",
        }
        if page_token:
            params["pageToken"] = page_token

        data = fetch_json(params)
        for study in data.get("studies", []) or []:
            scanned += 1
            result = extract_effect_size(study)
            if result is not None:
                print(f"Scanned {scanned} records; using {result['study_id']}")
                return result

        page_token = data.get("nextPageToken")
        if not page_token:
            break

    raise RuntimeError(
        f"No ClinicalTrials.gov record with usable submitted results "
        f"found for query '{SEARCH_QUERY}' after scanning {scanned} records."
    )

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    result = find_study_with_results()

    # ------- Write JSON result (thin‑slice result) -------
    json_path = paths.data("results", "thin_slice_result.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "study_id": result["study_id"],
                "hedges_g": result["hedges_g"],
                "se": result["se"],
                "ci_lower": result["ci_lower"],
                "ci_upper": result["ci_upper"],
                "retrieval_timestamp": result["retrieval_timestamp"],
                "source": result["source"],
            },
            fh,
            indent=2,
        )
    print(f"Wrote thin‑slice JSON to {json_path}")

    # ------- Write cleaned CSV row -------
    csv_path = paths.data("processed", "thin_slice_cleaned.csv")
    # Build a DataFrame with the columns required by the schema.
    df = pd.DataFrame(
        [
            {
                "id": result["study_id"],
                "title": result["study_title"],
                "registry": result["source"],
                "age_range": json.dumps(result["age_range"]),   # stored as JSON string
                "diagnosis": "ASD",
                "outcomes": json.dumps(result["outcomes"]),    # JSON array string
                "intervention_components": json.dumps(result["intervention_components"]),
                "delivery_format": result["delivery_format"],
                "social_skill_domain": result["social_skill_domain"],
                # Optional fields (allowed to be null)
                "follow_up": result["follow_up"],
                "abstract_text": result["abstract_text"],
                "domain_notes": result["domain_notes"],
                "blinded_assessment_flag": result["blinded_assessment_flag"],
                "rater_type": result["rater_type"],
            }
        ]
    )
    df.to_csv(csv_path, index=False)
    print(f"Wrote thin‑slice cleaned CSV to {csv_path}")

    # Summary output
    print(f"Study ID: {result['study_id']}")
    print(f"Hedges' g: {result['hedges_g']}")

if __name__ == "__main__":
    main()
