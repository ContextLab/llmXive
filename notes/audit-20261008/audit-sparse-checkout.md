# Preserve audit coverage while reducing checkout latency

The four legacy `audit.yml` jobs each spent over six minutes materializing unrelated repository content in PR #1531. This change gives each job a sparse profile covering its complete input directories. Auditor code, filtering, URL verification, failure gates and package installation remain unchanged. The repository-layout job is owned by the separate case-collision fix and is untouched.

## Input inventory

- Spec Kit: every `projects/PROJ-*/specs/` directory, `.specify/templates/`, and `state/projects/` (the latter controls stage-aware scaffold filtering).
- PDF: all `papers/`, including style, registry and every future PDF.
- Personality: every `projects/PROJ-*/activity.jsonl`, all persona cards, and the evidence-URL verifier script.
- Feedback: every project activity feed and `.audit/dispatches/` directory, including records outside the seven-day window. The auditor applies its existing time filter.

Each job first checks its corpus against the complete Git index. A missing tracked input fails the job before the auditor can produce a falsely empty/partial manifest. Exact Git glob pathspecs retain nested specification files without accidentally matching `code/specs/`, which the auditor never reads.

## Real-corpus verification

At base `c95996fa5e106216da756a75746eaab6e9a370e7`, a clean validation worktree was created on a temporary **case-sensitive APFS volume**. The regular Mac volume collapses `API_analysis.md` and `api_analysis.md` in PROJ-715; that separate defect is tracked in #1532. Both original files were preserved byte-for-byte in this proof, without modifying science.

The reference checkout materialized the union of all four complete input sets. Every corpus file was checked against its Git blob SHA-1. All four auditors then ran on that complete corpus. Each job's exact workflow sparse patterns were applied in turn, all indexed corpus bytes checked again, and the auditor rerun. `inputs_scanned`, full `items` including rules/defects, and `summary` matched exactly; only manifest timestamps/IDs were excluded from comparison. Feedback used a fixed since boundary (`2026-10-02T00:00:00Z`). Detailed counts and SHA-256 digests are in `audit-sparse-equivalence.json`.

| Job | All tracked corpus files preserved | Audited result | Total files materialized by profile |
| --- | ---: | --- | ---: |
| Spec Kit | 9,857 | 6,907 real artifacts | 10,124 |
| PDF | 13 | 0 PDF inputs | 280 |
| Personality | 684 | 515 passing contributions across 667 feeds | 951 |
| Feedback | 667 | 0 dispatch-record inputs | 934 |

The zero PDF/dispatch counts are properties of this Git snapshot, also observed before sparse checkout. They are not proof that published PDFs or feedback dispatches have been audited. Profiles preserve the complete directories so future committed inputs are included automatically.

Four real-Git regression cases exercise the workflow patterns against multiple projects, nested specs, activity, dispatch records, PDFs, style and registry; each removes an expected file and proves the guard fails. Auditor/CI-selection focused suite: **70 passed, 2 skipped**. `actionlint`, Ruff and `git diff --check` pass. Exact-head CI and measured remote checkout duration remain pending.
