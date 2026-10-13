"""
Thin-slice pipeline (Task T002).

Fetches ONE real record from the ClinicalTrials.gov API v2 that (a) matches
a mindfulness + autism search and (b) has submitted results containing
group-level summary statistics (means, SDs, N) for an intervention arm and
a control arm. It then "cleans" that record (arm selection, outcome
extraction) and calculates Hedges' g with small-sample correction
(FR-004, FR-013), mirroring the formula in code/analysis/effect_sizes.py.

Output: data/results/thin_slice_result.json with keys `study_id` and
`hedges_g` (plus full provenance: group statistics, retrieval timestamp,
and the exact API URL used).

The script fails loudly if the real API cannot be reached or if no real
record with usable summary statistics is found. It never fabricates data.
"""
import json
import math
import time
from datetime import datetime, timezone

import requests
from llmxive_toolkit import paths

API_BASE = "https://clinicaltrials.gov/api/v2/studies"
SEARCH_QUERY = "mindfulness AND autism"
MAX_PAGES = 10
PAGE_SIZE = 100

CONTROL_ARM_TYPES = {
    "ACTIVE_COMPARATOR",
    "PLACEBO_COMPARATOR",
    "NO_INTERVENTION",
    "SHAM_COMPARATOR",
    "OTHER",
}


def fetch_json(params, retries=5):
    """GET the ClinicalTrials.gov API with exponential backoff (FR-002)."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(API_BASE, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last_err = exc
            delay = min(1.0 * (2 ** attempt), 60.0)
            print(f"[retry] request failed ({exc}); "
                  f"attempt {attempt}/{retries}, sleeping {delay:.1f}s")
            time.sleep(delay)
    raise RuntimeError(
        f"ClinicalTrials.gov API unreachable after {retries} attempts: {last_err}"
    )


def calculate_hedges_g(n_treatment, n_control, mean_treatment, mean_control,
                       sd_treatment, sd_control):
    """Hedges' g with small-sample correction (same formula as
    code/analysis/effect_sizes.py::calculate_hedges_g)."""
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


def _group_n(outcome_measure, group_id):
    """Extract participant count for a results group from denominators."""
    for denom in outcome_measure.get("denoms", []) or []:
        counts = (denom.get("denomCount") or {}).get("counts", []) or []
        for c in counts:
            if c.get("groupId") == group_id:
                return int(c.get("value"))
    return None


def _group_stat(outcome_measure, group_id):
    """Extract (mean, sd) for a results group, if reported."""
    mean = sd = None
    for stat in outcome_measure.get("statistics", []) or []:
        if stat.get("groupId") != group_id:
            continue
        if stat.get("paramType") == "Mean":
            mean = float(stat.get("value"))
            if stat.get("dispersionType") == "Standard Deviation":
                sd = float(stat.get("dispersionValue"))
    return mean, sd


def extract_effect_size(study):
    """Clean one registry record and compute Hedges' g from its REAL
    submitted results. Returns a result dict or None if the record lacks
    usable summary statistics."""
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
        tx_group = None
        ct_group = None
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

        g_val, se, ci_lo, ci_hi, pooled_sd, corr = calculate_hedges_g(
            n_t, n_c, mean_t, mean_c, sd_t, sd_c
        )
        return {
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
        }
    return None


def find_study_with_results():
    """Page through real ClinicalTrials.gov search results and return the
    first record with usable intervention-vs-control summary statistics."""
    page_token = None
    scanned = 0
    for _ in range(MAX_PAGES):
        params = {
            "query.cond": SEARCH_QUERY,
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
                print(f"Scanned {scanned} records; "
                      f"using {result['study_id']}")
                return result
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    raise RuntimeError(
        f"No ClinicalTrials.gov record with usable submitted results "
        f"statistics found for query '{SEARCH_QUERY}' after scanning "
        f"{scanned} records; cannot fabricate an effect size."
    )


def main():
    result = find_study_with_results()
    out_path = paths.data("results", "thin_slice_result.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    print(f"Wrote {out_path}")
    print(f"study_id: {result['study_id']}")
    print(f"hedges_g: {result['hedges_g']}")


if __name__ == "__main__":
    main()
