# Quickstart: Claim-Verification Layer

## What it does

Stops llmXive agents from publishing fabricated facts. Every check-worthy claim is extracted, registered, resolved against a real source (or a signed result receipt), and rendered from the verified value — the model never retypes a fact. Unresolved claims block the document and auto-route for retry (no routine human input).

## Prerequisites

- Python 3.11, repo installed (`pip install -e .` in `/Users/jmanning/llmXive`).
- Dartmouth key for real resolution: `llmxive.credentials.load_dartmouth_key()` (or `~/.config/llmxive/credentials.toml`).
- Receipt signing key (process-local secret, never in a prompt).
- `LLMXIVE_REAL_TESTS=1` to run real-call tests.

## Verify the core scenario (the 27,635 → 9,988 fix)

```bash
export LLMXIVE_REAL_TESTS=1
python -m pytest tests/real_call/test_claim_resolve_real.py -q
```
Asserts: the fabricated "27,635 prime knots at 13 crossings" claim resolves to **refuted / not-enough-info** (no resolvable source supports it), while the true count **9,988** (OEIS A002863) resolves to **verified** from a resolvable reference; the rendered spec contains the verified value or the block marker — never the fabricated number, and never a human-input request.

## Use the layer programmatically

```python
from pathlib import Path
from llmxive.claims import service
from llmxive.config import repo_root

rendered, claims, report = service.process_document(
    text=agent_output,
    artifact_path="projects/PROJ-552/specs/001-x/spec.md",
    project_id="PROJ-552-quantifying-the-complexity-of-knot-diagr",
    backend=backend, model=None, repo_root=repo_root(),
)
if report.blocked:
    # unresolved claims were auto-routed; document does not advance
    ...
else:
    write(rendered)   # contains only verified values
```

## Mint + verify a result receipt (internal results)

```python
from llmxive.results import harness, receipt
r = harness.mint_receipt(value="0.42", kind="scalar",
    producer={"script_path": "code/PROJ-552/run.py", "code_sha": code_sha,
              "entrypoint": "main", "seed": 0},
    inputs={"dataset_id": "knots-13", "data_sha256": data_sha, "params": {}},
    env_sha=env_sha, captured={"stdout_path": "...", "return_repr": "0.42"},
    repo_root=repo_root(), project_id="PROJ-552-...")
assert receipt.verify_receipt(r, key=receipt.load_signing_key())   # tamper-evident
```
A write-up may then cite `result:<r.result_id>` by pointer; a results numeral with no backing receipt is blocked.

## Run the one-time marker migration

```bash
python -m llmxive.claims.migrate            # rewrites [UNVERIFIED: …] → [UNRESOLVED-CLAIM: …]
python -m llmxive.claims.migrate --dry-run  # list files that would change
```

## Offline gate (no network)

```bash
python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider \
  --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs
```

## Success signals (map to SC-001…SC-008)

- No advanced document contains an unverified number/citation (SC-001/002).
- Every advanced result number traces to a receipt whose captured output matches (SC-003); no model can introduce an unbacked result value (SC-004).
- Zero human interventions for claim resolution in an end-to-end run (SC-005).
- A verified claim renders identically everywhere with no re-resolution (SC-006).
- Design parameters/thresholds are not flagged (SC-007).
- Each non-numeric claim type flags a known-false instance (SC-008).
