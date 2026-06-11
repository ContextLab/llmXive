# Contract: Per-Paper Status Record

**Feature**: 023-pipeline-e2e-completion (US6, FR-022..024)
**Location**: `state/paper_status/<paper-id>.json` (single canonical home)

Written/updated by every compile, restyle, and audit run for the paper.
Consumed by `web_data.py` (site status) and by the repair-loop producer.

## Schema

```json
{
  "paper_id": "PROJ-### | submission id",
  "updated_at": "ISO-8601",
  "status": "audited | restyled_unaudited | fallback_original",
  "pdf": "path served on the site",
  "failure": {
    "stage": "restyle | compile | audit",
    "reason": "machine-readable reason string",
    "log_excerpt": "bounded excerpt of the failing output"
  },
  "audit": {
    "passed": true,
    "defects": [
      {"kind": "overflow | missing-figure | encoding | ...", "page": 3, "detail": "..."}
    ]
  },
  "repair_rounds": 0
}
```

`failure` is null on success; `audit` is null until the audit has run.

## Rules

- **No silent fallback**: serving the original (un-restyled) PDF REQUIRES
  `status = fallback_original` with a non-null `failure`. A fallback
  without a failure report is a contract violation (tested).
- **Repair loop**: a non-null `failure` or `audit.defects` triggers a
  repair work-spec (via the US1 revision machinery); `repair_rounds`
  increments per round and is bounded (cap → honest fallback status, never
  an infinite loop).
- **Re-audit**: after a repair round compiles, the audit re-runs and the
  record updates before the site does.
- **Site truthfulness**: `web/data/*` paper entries carry exactly the
  record's `status`; the site build fails closed if a served paper has no
  status record.
