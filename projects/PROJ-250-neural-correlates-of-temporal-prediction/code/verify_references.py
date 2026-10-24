"""FR-012 reference-verification gates for PROJ-250-neural-correlates-of-temporal-prediction.

Implements the three Reference-Validator checks:
  * verify_dataset_id()  -- dataset ID / URL against the canonical OpenNeuro source (pre-download gate)
  * verify_conditions()  -- presence of 'simple' and 'complex' condition labels in events.tsv metadata (pre-analysis gate)
  * verify_citations()   -- citation verification against named primary sources (pre-reporting gate),
                            writing data/results/citation_verification.json

Exposed via:  python code/verify_references.py --stage dataset|conditions|citations|all
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import requests
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

CANONICAL_DATASET_ID = "ds004510"
OPENNEURO_URL = "https://openneuro.org/datasets/" + CANONICAL_DATASET_ID
S3_BASE = "https://s3.amazonaws.com/openneuro.org"

# Named primary sources (verified in the project's literature search trail).
CITATIONS = [
    {
        "id": "stein2021",
        "title": "Frequency and frequency modulation share the same predictive "
                 "encoding mechanisms in human auditory cortex",
        "authors": "Jasmin Stein, Kathrina von Kriegstein, Alejandro Tabas",
        "year": 2021,
        "source": "arXiv",
        "url": "https://arxiv.org/abs/2110.13690",
    },
    {
        "id": "schilling2022",
        "title": "Predictive coding and stochastic resonance as fundamental "
                 "principles of auditory perception",
        "authors": "Achim Schilling, William Sedley, Richard Gerum, Claus Metzner, "
                   "Konstantin Tziridis, et al.",
        "year": 2022,
        "source": "arXiv",
        "url": "https://arxiv.org/abs/2204.03354",
    },
    {
        "id": "zhang2025",
        "title": "Deviance Detection and Regularity Sensitivity in Dissociated "
                 "Neuronal Cultures",
        "authors": "Zhuo Zhang, Amit Yaron, Dai Akita, Tomoyo Isoguchi Shiramatsu, "
                   "Zenas C. Chao, et al.",
        "year": 2025,
        "source": "arXiv",
        "url": "https://arxiv.org/abs/2502.20753",
    },
]

CONDITION_ALIASES = {"simple": "simple", "complex": "complex"}
STIMULUS_ALIASES = {
    "standard": "standard",
    "std": "standard",
    "deviant": "deviant",
    "dev": "deviant",
}


def _fail(message):
    """Fail loudly: print a clear message and exit non-zero."""
    print("REFERENCE VERIFICATION FAILED: " + message, file=sys.stderr)
    sys.exit(1)


def verify_dataset_id(dataset_id=None, check_url=True):
    """FR-012(1): verify the dataset ID / URL against the canonical OpenNeuro source.

    Runs BEFORE any download. Exits non-zero with a clear message on mismatch.
    """
    dataset_id = dataset_id or CANONICAL_DATASET_ID
    if not re.fullmatch(r"ds\\d{6}", dataset_id):
        _fail(
            "Invalid OpenNeuro dataset ID '%s': expected the form 'ds######'."
            % dataset_id
        )
    if dataset_id != CANONICAL_DATASET_ID:
        _fail(
            "Dataset ID mismatch: expected '%s' (canonical OpenNeuro source for "
            "this project) but got '%s'. Halting before download."
            % (CANONICAL_DATASET_ID, dataset_id)
        )
    if check_url:
        try:
            resp = requests.get(OPENNEURO_URL, timeout=30, allow_redirects=True)
        except requests.RequestException as exc:
            _fail("Could not reach canonical OpenNeuro URL %s: %s" % (OPENNEURO_URL, exc))
        if resp.status_code >= 400:
            _fail(
                "Canonical OpenNeuro URL %s returned HTTP %d; dataset ID could not "
                "be verified against the primary source." % (OPENNEURO_URL, resp.status_code)
            )
    print(
        "Dataset ID verified: %s matches the canonical OpenNeuro source (%s)."
        % (dataset_id, OPENNEURO_URL)
    )
    return True


def scan_events(events_path):
    """Scan one BIDS events.tsv file.

    Returns a dict with:
      condition_labels: set of normalized condition labels found ('simple'/'complex')
      stimulus_types:   set of normalized stimulus types found ('standard'/'deviant')
      n_rows:           number of event rows
    The condition column is 'condition_label' if present, otherwise any column
    whose values include 'simple'/'complex'; the stimulus column is
    'stimulus_type' if present, otherwise any column with standard/deviant values.
    """
    with open(events_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\\t")
        rows = list(reader)
        headers = reader.fieldnames or []
    condition_labels = set()
    stimulus_types = set()

    cond_col = "condition_label" if "condition_label" in headers else None
    if cond_col is None:
        for header in headers:
            vals = {str(r.get(header) or "").strip().lower() for r in rows}
            if vals & set(CONDITION_ALIASES):
                cond_col = header
                break
    if cond_col is not None:
        for r in rows:
            v = str(r.get(cond_col) or "").strip().lower()
            if v in CONDITION_ALIASES:
                condition_labels.add(CONDITION_ALIASES[v])

    stim_col = "stimulus_type" if "stimulus_type" in headers else None
    if stim_col is None:
        for header in headers:
            vals = {str(r.get(header) or "").strip().lower() for r in rows}
            if vals & set(STIMULUS_ALIASES):
                stim_col = header
                break
    if stim_col is not None:
        for r in rows:
            v = str(r.get(stim_col) or "").strip().lower()
            if v in STIMULUS_ALIASES:
                stimulus_types.add(STIMULUS_ALIASES[v])

    return {
        "condition_labels": condition_labels,
        "stimulus_types": stimulus_types,
        "n_rows": len(rows),
    }


def collect_events(data_dir):
    """Scan all events.tsv files under data_dir; return (labels, stimulus_types, per-file info)."""
    data_dir = Path(data_dir)
    events_files = sorted(p for p in data_dir.rglob("*events.tsv") if p.is_file())
    if not events_files:
        _fail(
            "No events.tsv metadata files found under %s; cannot verify conditions. "
            "Run code/download.py first." % data_dir
        )
    labels = set()
    stimulus_types = set()
    per_file = {}
    for ef in events_files:
        info = scan_events(ef)
        per_file[str(ef)] = sorted(info["condition_labels"])
        labels |= info["condition_labels"]
        stimulus_types |= info["stimulus_types"]
    return labels, stimulus_types, per_file


def verify_conditions(data_dir=None):
    """FR-012(2) / FR-008: verify 'simple' and 'complex' condition labels in events metadata.

    Runs after metadata is available, before any analysis. Halts with the exact
    FR-008 message if the 'complex' condition is missing.
    """
    data_dir = Path(data_dir) if data_dir else paths.data("raw")
    labels, stimulus_types, per_file = collect_events(data_dir)
    print("Condition labels found in events metadata: %s" % sorted(labels))
    print("Stimulus types found in events metadata: %s" % sorted(stimulus_types))
    if "complex" not in labels:
        print(
            "Dataset lacks required 'complex' condition; research question "
            "untestable with current data.",
            file=sys.stderr,
        )
        sys.exit(1)
    if "simple" not in labels:
        _fail(
            "Dataset lacks required 'simple' condition; research question "
            "untestable with current data."
        )
    print("Conditions verified: both 'simple' and 'complex' labels are present.")
    return True


def verify_citations():
    """FR-012(3): verify citations against named primary sources.

    Writes data/results/citation_verification.json recording verified/unreachable
    status per citation. Exits non-zero if any citation is unreachable.
    """
    results = []
    any_unreachable = False
    for cite in CITATIONS:
        entry = dict(cite)
        try:
            resp = requests.get(cite["url"], timeout=30, allow_redirects=True)
            ok = resp.status_code < 400
            entry["http_status"] = resp.status_code
        except requests.RequestException as exc:
            ok = False
            entry["http_status"] = None
            entry["error"] = str(exc)
        entry["status"] = "verified" if ok else "unreachable"
        if not ok:
            any_unreachable = True
        results.append(entry)
    out_path = paths.results("citation_verification.json")
    payload = {
        "citation_count": len(results),
        "all_verified": not any_unreachable,
        "citations": results,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Citation verification written to %s" % out_path)
    for entry in results:
        print("  [%s] %s (%s)" % (entry["status"], entry["id"], entry["url"]))
    if any_unreachable:
        _fail(
            "One or more citations could not be verified against their primary "
            "source; see %s" % out_path
        )
    return True


def main():
    parser = argparse.ArgumentParser(description="FR-012 reference verification gates")
    parser.add_argument(
        "--stage",
        required=True,
        choices=["dataset", "conditions", "citations", "all"],
        help="Which verification gate to run",
    )
    parser.add_argument(
        "--dataset-id",
        default=CANONICAL_DATASET_ID,
        help="Dataset ID to verify (default: %s)" % CANONICAL_DATASET_ID,
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="Directory containing the downloaded BIDS events.tsv metadata "
             "(default: data/raw)",
    )
    args = parser.parse_args()

    if args.stage in ("dataset", "all"):
        verify_dataset_id(args.dataset_id)
    if args.stage in ("conditions", "all"):
        verify_conditions(args.data_dir)
    if args.stage in ("citations", "all"):
        verify_citations()
    print("Stage '%s' passed." % args.stage)


if __name__ == "__main__":
    main()
