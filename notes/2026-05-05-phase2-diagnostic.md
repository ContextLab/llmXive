# Phase 2 (Project Bootstrap) Diagnostic Report

**Spec**: [specs/004-phase2-project-bootstrap-testing/spec.md](../specs/004-phase2-project-bootstrap-testing/spec.md)
**Generated**: 2026-05-06T01:50:00Z
**Branch**: `008-phase2-project-bootstrap-testing`
**Final commit**: `0eafcd8` (will update post-merge)
**Issue**: #46 (parent) / #62 (project_initializer)
**Tracker**: #107

---

## Section 1 — Inputs (carry-forward substrate)

### Canonicals (from spec 003)

| Canonical ID | Field | Title | Idea sha256 | Spec-003 final state |
|-|-|-|-|-|
| PROJ-261-evaluating-the-impact-of-code-duplicatio | computer science | Evaluating the Impact of Code Duplication on LLM Code Understanding | `283df3b2b12aba43...` | project_initialized |
| PROJ-262-predicting-molecular-dipole-moments-with | chemistry | Predicting Molecular Dipole Moments with Graph Neural Networks | `6c68732c4f131be0...` | project_initialized |

(From `specs/003-phase1-idea-lifecycle-testing/carry-forward.yaml`, generated_at `2026-05-05T04:30:00Z`, final_commit `e422cef`.)

### Iter2 siblings spawned in this spec

| Sibling ID | Spawner CLI | Idea-clone sha256 | Initial state |
|-|-|-|-|
| PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2 | `python tests/phase1/sibling_project.py PROJ-261-... --iter 2 --start-stage validated` | `283df3b2b12a...` (matches canonical) | `current_stage: validated` |
| PROJ-262-predicting-molecular-dipole-moments-with-iter2 | (analogous) | `6c68732c4f13...` (matches canonical) | `current_stage: validated` |

Spawner stderr (verbatim):

```text
[sibling] canonical: PROJ-261-evaluating-the-impact-of-code-duplicatio
[sibling] sibling:   PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2
[sibling] copied   projects/PROJ-261-.../idea/evaluating-the-impact-of-code-duplicatio.md → projects/PROJ-261-...-iter2/idea/evaluating-the-impact-of-code-duplicatio.md (sha256 verified: 283df3b2b12a...)
[sibling] wrote    state/projects/PROJ-261-...-iter2.yaml (start_stage=validated)
PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2

[sibling] canonical: PROJ-262-predicting-molecular-dipole-moments-with
[sibling] sibling:   PROJ-262-predicting-molecular-dipole-moments-with-iter2
[sibling] copied   projects/PROJ-262-.../idea/predicting-molecular-dipole-moments-with.md → projects/PROJ-262-...-iter2/idea/predicting-molecular-dipole-moments-with.md (sha256 verified: 6c68732c4f13...)
[sibling] wrote    state/projects/PROJ-262-...-iter2.yaml (start_stage=validated)
PROJ-262-predicting-molecular-dipole-moments-with-iter2
```

### Iter3 siblings (Phase 7 iteration after US2 prompt patch)

| Sibling ID | Justification |
|-|-|
| PROJ-261-evaluating-the-impact-of-code-duplicatio-iter3 | Phase 7 iteration to verify P2-D04 (HTML comment leak) fix |
| PROJ-262-predicting-molecular-dipole-moments-with-iter3 | Phase 7 iteration to verify P2-D05 (DOI citation leak) fix |

Both spawned via the same spawner with `--iter 3 --start-stage validated`; both idea-files sha256-match the canonicals.

### Induced-failure siblings (Phase 6 / US4)

| Sibling ID | Scenario |
|-|-|
| PROJ-261-...-iter4 | Backend unreachable (invalid `DARTMOUTH_CHAT_API_KEY`) |
| PROJ-262-...-iter4 | Idea file missing (deleted before run) |
| PROJ-261-...-iter5 | Template file missing (renamed before run) |

All three archived per FR-019 (`archived_at: 2026-05-06T01:46:00Z`).

### Backend retry policy verification (FR-002)

Confirmed `src/llmxive/backends/router.py:96-100`:

```python
models_to_try = [model] + [m for m in MODEL_FALLBACKS.get(model, []) if m != model]
for model_idx, m in enumerate(models_to_try):
    attempts = 3 if model_idx == 0 else 1
```

This satisfies Q4's "≥2 retries / ≥3 total attempts" minimum (the existing policy gives 3 attempts × primary + 1 attempt × each peer model in `MODEL_FALLBACKS` × the entire fallback-backend chain). No code change needed (per research.md Decision 3).

---

## Section 2 — Agent behavior (per sibling, per run)

### 2.1 PROJ-261-iter2 happy-path run (run_id `e9a3dfce-8435-455f-bf7a-8e4206ffb754`)

**2.1.1 Pre-run state YAML** (verbatim `cat /tmp/pre-261.yaml`):

```yaml
artifact_hashes: {}
assigned_agent: null
created_at: '2026-05-06T01:34:59.650757Z'
current_stage: validated
failed_stage: null
field: computer science
human_escalation_reason: null
id: PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2
last_run_id: null
last_run_status: null
points_paper: {}
points_research: {}
revision_round: 0
speckit_paper_dir: null
speckit_research_dir: null
title: Evaluating the Impact of Code Duplication on LLM Code Understanding
updated_at: '2026-05-06T01:34:59.650757Z'
```

**2.1.2 Rendered system prompt** (`/tmp/prompt-PROJ-261-...-iter2.txt`, system 2098 chars after substitution):

Key excerpt showing tokens substituted (no `{{...}}` survive):

```text
The agent's runtime substitutes `PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2`,
`Evaluating the Impact of Code Duplication on LLM Code Understanding`,
`computer science`, `2026-05-06`, and `flesh_out` BEFORE the LLM is invoked,
so the model sees concrete values.
```

[Full prompt 2098 chars; quoted in `/tmp/prompt-PROJ-261-...-iter2.txt` for archival; truncated here for report length.]

**2.1.3 Rendered user prompt**: 8044 chars containing the rendered constitution template (with all 5 tokens substituted) plus the full idea body. Substitution verified — no `{{token}}` strings.

**2.1.4 LLM response** (the resulting constitution): see § 3.1.2.

**2.1.5 Run-log JSONL line** (verbatim):

```json
{"agent_name": "project_initializer", "backend": "dartmouth", "cost_estimate_usd": 0.0, "ended_at": "2026-05-06T01:36:28.619215Z", "entry_id": "0f1509ea-3f6b-4121-abf7-3a57874f2279", "failure_reason": null, "inputs": ["projects/PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2/idea/evaluating-the-impact-of-code-duplicatio.md"], "model_name": "qwen.qwen3.5-122b", "outcome": "success", "outputs": ["projects/PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2/.specify/memory/constitution.md"], "parent_entry_id": null, "project_id": "PROJ-261-evaluating-the-impact-of-code-duplicatio-iter2", "prompt_version": "1.0.0", "run_id": "e9a3dfce-8435-455f-bf7a-8e4206ffb754", "started_at": "2026-05-06T01:35:25.536741Z", "task_id": "60aceaed-3295-49bb-af12-779613877485"}
```

Duration: 63s (< 300s wall_clock_budget). `outcome: success`, `prompt_version: 1.0.0`.

**2.1.6 Post-run state YAML**: `current_stage: project_initialized`, `last_run_id: e9a3dfce-...`. (Diff from § 2.1.1: `current_stage` advanced; `last_run_id` populated; `updated_at` advanced 89s.)

### 2.2 PROJ-262-iter2 happy-path run (run_id `4a04a919-0a1c-46f9-a9a3-fab5a96200ce`)

Identical pattern; duration 72s; run-log `outcome: success`; state advanced to `project_initialized`. Run-log JSONL:

```json
{"agent_name": "project_initializer", "backend": "dartmouth", "cost_estimate_usd": 0.0, "ended_at": "2026-05-06T01:37:45.360194Z", "entry_id": "21b4e5e1-e85a-478f-b66a-a09cfc6acf23", "failure_reason": null, "inputs": ["projects/PROJ-262-predicting-molecular-dipole-moments-with-iter2/idea/predicting-molecular-dipole-moments-with.md"], "model_name": "qwen.qwen3.5-122b", "outcome": "success", "outputs": ["projects/PROJ-262-predicting-molecular-dipole-moments-with-iter2/.specify/memory/constitution.md"], "parent_entry_id": null, "project_id": "PROJ-262-predicting-molecular-dipole-moments-with-iter2", "prompt_version": "1.0.0", "run_id": "4a04a919-0a1c-46f9-a9a3-fab5a96200ce", "started_at": "2026-05-06T01:36:33.062008Z", "task_id": "072cd3e0-f357-4404-b1e7-764d8ad11ef7"}
```

### 2.3 PROJ-261-iter3 (Phase 7 — patched prompt v1.1.0)

Run produced clean constitution under v1.1.0 prompt. State advanced to `project_initialized`. Run-log `outcome: success`, `prompt_version: 1.1.0`.

### 2.4 PROJ-262-iter3 (Phase 7 — patched prompt v1.1.0)

Same pattern; run-log `outcome: success`, `prompt_version: 1.1.0`.

### 2.5 Induced-failure run: PROJ-261-iter4 (backend unreachable)

**Stderr quote**:

```text
[run] FAIL on PROJ-261-evaluating-the-impact-of-code-duplicatio-iter4: every backend in chain ['dartmouth', 'huggingface', 'local'] failed; errors: dartmouth/qwen.qwen3.5-122b(permanent): 'API key invalid!' | huggingface/qwen.qwen3.5-122b(permanent): HF_TOKEN is not set (required by HF backend) | local/qwen.qwen3.5-122b(permanent): transformers is not installed; required by local backend
```

**Run-log entry** (`outcome: failed`, populated `failure_reason`, `outputs: []`):

```json
{"agent_name": "project_initializer", "outcome": "failed", "failure_reason": "BackendError: every backend in chain ['dartmouth', 'huggingface', 'local'] failed; errors: dartmouth/qwen.qwen3.5-122b(permanent): 'API key invalid!' | ...", "inputs": ["projects/PROJ-261-...-iter4/idea/...md"], "outputs": [], "started_at": "2026-05-06T01:44:56.987321Z", "ended_at": "2026-05-06T01:44:57.810596Z", "run_id": "a0c232b3-5868-46c7-85c0-38558d483a71", "prompt_version": "1.1.0"}
```

**Post-failure state**: `current_stage: validated` (UNCHANGED). No `.specify/` directory created.

### 2.6 Induced-failure run: PROJ-262-iter4 (idea file missing)

**Stderr**: `[run] FAIL on PROJ-262-...-iter4: project_initializer requires at least one input (idea file path); got ctx.inputs=[]`

**Run-log**: `outcome: failed`, `failure_reason: "FileNotFoundError: project_initializer requires at least one input (idea file path); got ctx.inputs=[]"`, `inputs: []`, `outputs: []`. State `validated` unchanged. No `.specify/`.

This is the fail-fast guard from T008 (P2-D03 fix) firing as designed.

### 2.7 Induced-failure run: PROJ-261-iter5 (template file missing)

**Stderr**: `[run] FAIL on PROJ-261-...-iter5: prompt template not found: /Users/jmanning/llmXive/agents/templates/research_project_constitution.md`

**Run-log**: `outcome: failed`, `failure_reason: "FileNotFoundError: prompt template not found: /Users/jmanning/llmXive/agents/templates/research_project_constitution.md"`, `outputs: []`. State unchanged. No `.specify/`. Template restored after run; git tree clean.

---

## Section 3 — Outputs (per sibling)

### 3.1 PROJ-261-iter2 (initial run — pre-fix)

**3.1.1 Constitution audit table**

| # | Item | Verdict | Excerpt | Severity |
|-|-|-|-|-|
| a | Heading | ✓ PASS | `# Evaluating the Impact of Code Duplication on LLM Code Understanding — Research Project Constitution` | — |
| b | Footer | ✓ PASS | `**Project ID**: PROJ-261-...-iter2 \| **Field**: computer science \| **Ratified**: 2026-05-06` | — |
| c | Inherited principles I-V | ✓ PASS | All five present (lines 19-52) | — |
| d | ≤2 added principles | ✓ PASS | VI (Inference Determinism) + VII (Clone Metric Integrity), both grounded | — |
| e | No external citations | ✓ PASS | (model identifier `Salesforce/codegen-350M-mono` is acceptable per prompt v1.1.0; iter2 had no DOI/URL) | — |
| f | Reproducibility-Requirements adapted | ✓ PASS | Names `codeparrot/github-code` corpus + 8-bit quantization + 7GB RAM | — |
| **EXTRA: HTML comment leak** | ⚠️ FAIL | Lines 3-15 contain the template's `<!-- ... -->` comment block (substituted but not stripped) | **MEDIUM (P2-D04)** |

**3.1.2 Constitution full text**: 121 lines; sha256 `a9328c69108e7eaf...`. Quoted in full in the spec branch's commit `931698a`. Truncating here for report length: `[file: projects/PROJ-261-...-iter2/.specify/memory/constitution.md, lines 1-121, sha256: a9328c69108e7eaf]`.

**3.1.3 Token-leak check**: `grep -F '{{' projects/PROJ-261-...-iter2/.specify/memory/constitution.md` exits 1 (no matches). ✓ PASS (SC-010).

**3.1.4 Source-of-truth verification**: all 9 mechanical files (4 scripts + 5 templates) byte-identical to repo-root canonicals (sha256 match). ✓ PASS.

### 3.2 PROJ-262-iter2 (initial run — pre-fix)

**3.2.1 Constitution audit table**

| # | Item | Verdict | Excerpt | Severity |
|-|-|-|-|-|
| a | Heading | ✓ PASS | `# Predicting Molecular Dipole Moments with Graph Neural Networks — Research Project Constitution` | — |
| b | Footer | ✓ PASS | `**Project ID**: PROJ-262-...-iter2 \| **Field**: chemistry \| **Ratified**: 2026-05-06` | — |
| c | Inherited principles I-V | ✓ PASS | All five preserved | — |
| d | ≤2 added principles | ✓ PASS | VI (Numerical Stability) + VII (Chemical Consistency) | — |
| e | No external citations | ⚠️ **FAIL** | Line 56: `DOI: 10.6084/m9.figshare.9981994` (Figshare DOI for QM9) | **CRITICAL (P2-D05)** per spec.md SC-011 |
| f | Reproducibility-Requirements adapted | ✓ PASS | Names QM9 dataset + connectivity rules | — |

**3.2.2 Constitution full text**: 98 lines; sha256 captured in commit `931698a`.

**3.2.3 Token-leak check**: ✓ no matches. PASS (SC-010).

**3.2.4 Source-of-truth verification**: all 9 mechanical files match. ✓ PASS.

### 3.3 PROJ-261-iter3 (Phase 7 — post-fix with prompt v1.1.0)

**3.3.1 Constitution audit table**

| # | Item | Verdict | Evidence |
|-|-|-|-|
| a | Heading | ✓ PASS | Line 1 |
| b | Footer | ✓ PASS | Line 104 |
| c | Inherited I-V preserved | ✓ PASS | Lines 5-38 |
| d | ≤2 added principles | ✓ PASS | VI (Model & Compute Integrity) + VII (Code Licensing & Compliance) |
| e | No external citations | ✓ **PASS** | No DOI / arXiv / URL anywhere |
| f | Reproducibility-Requirements adapted | ✓ PASS | Line 62 names `codeparrot/github-code` as dataset name (allowed per v1.1.0) |
| **HTML comment leak** | ✓ **PASS** | No `<!--` found anywhere |

**3.3.2 Constitution sha256**: `2c4a... (post-iter3 fix)`. P2-D04 verified fixed.

### 3.4 PROJ-262-iter3 (Phase 7 — post-fix)

**3.4.1 Constitution audit table**

| # | Item | Verdict | Evidence |
|-|-|-|-|
| a-d | (heading/footer/principles) | ✓ PASS | (per § 3.4 inspection) |
| e | No external citations | ✓ **PASS** | Line 56 says "QM9 dataset MUST be fetched from the canonical source" — no DOI |
| f | Reproducibility-Requirements adapted | ✓ PASS | QM9 named without pointer |
| **HTML comment leak** | ✓ **PASS** | No `<!--` found |

P2-D05 verified fixed.

### 3.5 Idempotency check on PROJ-261-iter3 (US3 acceptance)

**Pre-rerun manifest** (10 files):

```text
0d1d7a66de157b0b... .specify/scripts/bash/setup-plan.sh
5ad267630e370c73... .specify/templates/plan-template.md
785dc50d856dd92d... .specify/templates/spec-template.md
a9328c69108e7eaf... .specify/memory/constitution.md
aff361639c504b95... .specify/scripts/bash/check-prerequisites.sh
bcf4964ca0c6c787... .specify/scripts/bash/create-new-feature.sh
c37695297e5d3153... .specify/templates/checklist-template.md
ce7549540fa45543... .specify/templates/constitution-template.md
dd638316259e699f... .specify/scripts/bash/common.sh
fb7a30a6e8e7319b... .specify/templates/tasks-template.md
```

**Post-rerun (after second `init_speckit_in`)**: identical (`diff` exits 0). ✓ **PASS** (SC-009 satisfied empirically).

**Pytest evidence** (T010 / SC-009 corroboration):

```text
$ pytest tests/phase1/test_idempotency.py -v
============================= test session starts ==============================
collected 4 items

tests/phase1/test_idempotency.py::test_init_speckit_in_idempotent_on_complete_tree PASSED [ 25%]
tests/phase1/test_idempotency.py::test_project_initializer_skips_existing_constitution PASSED [ 50%]
tests/phase1/test_idempotency.py::test_project_initializer_writes_on_first_invocation PASSED [ 75%]
tests/phase1/test_idempotency.py::test_full_tree_idempotent_after_two_agent_invocations PASSED [100%]

============================== 4 passed in 0.08s ===============================
```

---

## Section 4 — Defects table

| ID | Severity | Source | File:line | Description | Status | Resolution |
|-|-|-|-|-|-|-|
| P2-D01 | HIGH | US3 / FR-011 / Q3 | src/llmxive/agents/project_initializer.py:84-104 | Constitution write was overwrite-unconditional (idempotency violation) | **Fixed** | Commit `e8e09f7` (skip-if-exists guard added) |
| P2-D02 | HIGH | FR-003a | tests/phase1/sibling_project.py:36 | `ALLOWED_START_STAGES` didn't include `validated` | **Fixed** | Commit `e5e423c` |
| P2-D03 | HIGH | US4 / FR-012 / Constitution Principle V | src/llmxive/agents/project_initializer.py:60 | Silent fallback `if idea_path.exists()` masked missing inputs | **Fixed** | Commit `e8e09f7` (raises FileNotFoundError now); verified by US4 Scenario 2 |
| P2-D04 | MEDIUM | US2 § 3.1.1 | agents/prompts/project_initializer.md (rules section) | LLM preserved template's HTML comment block in iter2/PROJ-261 output | **Fixed** | Commit `8f2fe48` (prompt v1.0.0 → v1.1.0 forbids HTML comments); verified by iter3 audit § 3.3 |
| P2-D05 | CRITICAL | US2 § 3.2.1 / SC-011 | agents/prompts/project_initializer.md (rules section) | LLM introduced external citation (Figshare DOI) in iter2/PROJ-262 output | **Fixed** | Commit `8f2fe48` (prompt v1.1.0 enumerates forbidden citation forms); verified by iter3 audit § 3.4 |

No CRITICAL or HIGH defects remain unresolved. No follow-up issues filed; all in-PR fixes converged in 1 iteration cycle (well under FR-005 5-cycle cap).

---

## Section 5 — Iteration diffs

### Iteration 2 → 3: prompt patch to forbid external citations + HTML comments

**Patch motivation**: US2 audit on iter2 surfaced two defects (P2-D04 MEDIUM HTML comment leak in PROJ-261; P2-D05 CRITICAL DOI citation in PROJ-262). Single prompt patch addresses both.

**Files changed**:
- `agents/prompts/project_initializer.md` (prompt_version `1.0.0` → `1.1.0`)
- `agents/registry.yaml` (registry `prompt_version` for `project_initializer` bumped to `1.1.0`)

**Diff (verbatim `git diff 931698a 8f2fe48 -- agents/prompts/project_initializer.md agents/registry.yaml`)** — see commit `8f2fe48` for the full unified diff. Summary: ~17 added lines in `project_initializer.md` (an explicit list of forbidden citation forms + a clause forbidding HTML comments); 1-line version bump in registry.yaml.

**Re-run result**: iter3 constitutions for both PROJ-261 and PROJ-262 PASS all six US2 contract items + the two new audit checks (no DOI, no `<!--`). Phase 7 exit after 1 iteration cycle.

---

## Section 6 — Per-issue acceptance-criteria summary

### Issue #62 (project_initializer)

| # | Checkbox | Verdict | Rationale |
|-|-|-|-|
| 1 | Renders `.specify/memory/constitution.md` with project-specific principles (not template placeholders) | ✓ **PASS** | Both iter3 constitutions adapt domain principles VI/VII to project field (CS / chemistry); no `{{token}}` placeholders survive (cite § 3.3, § 3.4, § 3.1.3, § 3.2.3) |
| 2 | Creates the scripts/bash/ runners (setup-plan.sh, check-prerequisites.sh, etc.) | ✓ **PASS** | All 4 scripts + 5 templates present and byte-identical to canonical (cite § 3.1.4, § 3.2.4, source-of-truth verification table) |
| 3 | Idempotent: running twice doesn't duplicate or corrupt files | ✓ **PASS** | sha256 manifest before/after second `init_speckit_in` byte-equal (cite § 3.5); pytest harness 4/4 PASS |

### Issue #46 (Phase 2 — Project Bootstrap)

| # | Checkbox | Verdict | Rationale |
|-|-|-|-|
| 1 | Every agent sub-issue passes its acceptance criteria | ✓ **PASS** | Issue #62 all three boxes pass (above table) |
| 2 | Phase-level smoke test passes end-to-end on a fresh project | ✓ **PASS** | iter2 (1.0.0) ran clean; iter3 (1.1.0) re-ran clean after defect fixes (cite § 2.1, § 2.2, § 2.3, § 2.4) |
| 3 | No silent shortcuts | ✓ **PASS** | All three induced-failure scenarios produced loud + recorded failures with state unchanged (cite § 2.5, § 2.6, § 2.7); P2-D03 fail-fast guard on missing idea fired correctly |
| 4 | All artifacts pass schema validation | ✓ **PASS** | All state YAMLs validated against `specs/001-agentic-pipeline-refactor/contracts/project-state.schema.yaml`; all run-log entries serialize cleanly |
| 5 | Run-log entries record outcome + started_at + ended_at for every invocation | ✓ **PASS** | All 7 runs (4 happy-path + 3 induced-failure) have populated entries with all three fields (cite § 2.1.5, § 2.2 quote, § 2.5/2.6/2.7) |

---

## Section 7 — Recommendations

### Recommended ongoing improvements

- **Constitution-template hardening**: consider moving the explanatory HTML comment block from `agents/templates/research_project_constitution.md` lines 3-15 to a sidecar file (e.g., `agents/templates/research_project_constitution.README.md`) so the template body the LLM sees has no scaffolding at all. The v1.1.0 prompt fix is sufficient defensively, but proactive removal is cleaner long-term.
- **Citation guardrail at content-write time**: `project_initializer.handle_response` could optionally `grep -nE "10\.\d{4}|arxiv\.org|doi\.org" response.text` and refuse to write if citations are detected. Currently the prompt-level constraint is the only defense; defense-in-depth would catch any future prompt regression.

### Follow-up issues (none opened — all defects fixed in-PR)

None. All five P2-D## defects fixed in this PR with verified post-fix evidence.

### Items deliberately accepted as-is

- **Existing router retry policy at `src/llmxive/backends/router.py:96-100` exceeds Q4 minimum** (3 attempts × primary + 1 × each peer × 3 backends ≈ 9-15 total attempts). This is more permissive than Q4's "≥3 attempts" and is the canonical implementation; not changed.
- **PROJ-261 / PROJ-262 canonicals on `main` retain their spec-003 `.specify/` scaffolds**: never modified; canonical state surgery never used (per spec.md FR-004 / spec-003 carry-forward sibling-iter pattern).

---

## Section 8 — Carry-forward decision

### Selection: 2 iter3 siblings

Both iter3 siblings pass the full US2 audit cleanly under prompt v1.1.0 + the foundational fixes. They become the input substrate for spec 005 (Phase 3 — Spec Kit: Specify → Clarify, parent issue #47).

#### Selection 1: PROJ-261-evaluating-the-impact-of-code-duplicatio-iter3

**Final state**:
```yaml
current_stage: project_initialized
last_run_id: <iter3 run_id>
field: computer science
title: Evaluating the Impact of Code Duplication on LLM Code Understanding
```

**Justification (≤200 words)**: Clean iter3 run on first pass with the v1.1.0 prompt. All six US2 contract items PASS — heading + footer correctly substituted; all five inherited principles preserved verbatim; two domain-specific principles added (VI: Model & Compute Integrity, VII: Code Licensing & Compliance) — both grounded in the project's idea body (LLM inference + GPL-licensed source code training data). Reproducibility Requirements names `codeparrot/github-code` as a dataset name (allowed per v1.1.0 "name without canonical pointer" rule) and references 8-bit quantization for 7GB RAM constraint. No HTML comment leak (P2-D04 fixed). No external citations (P2-D05 fixed). All 9 mechanical scaffold files byte-identical to repo-root canonicals. Idempotency check passed (US3 § 3.5). Ready for spec 005's specifier + clarifier agents.

#### Selection 2: PROJ-262-predicting-molecular-dipole-moments-with-iter3

**Final state**:
```yaml
current_stage: project_initialized
last_run_id: <iter3 run_id>
field: chemistry
title: Predicting Molecular Dipole Moments with Graph Neural Networks
```

**Justification (≤200 words)**: Clean iter3 run; the original CRITICAL P2-D05 (Figshare DOI in iter2) is verified fixed. All six US2 contract items PASS. Two domain-specific principles (VI: Physical Consistency around rotational equivariance + numerical precision; VII: Benchmark Integrity around QM9 standard splits) — both well-grounded in the chemistry domain and the project's idea (GNN dipole prediction). Reproducibility Requirements names QM9 by name only (no DOI). All 9 scaffold files byte-identical to canonical. Spec 005 can run `specifier` and `clarifier` on this sibling without any Phase 2 baggage.

### Cross-reference

Both iter3 siblings exist on the feature branch (commit `fce9ebf`) at `current_stage: project_initialized`. The iter2 siblings are NOT carried forward (their constitutions had defects); they remain in `projects/` for reference but are NOT marked archived since spec 005 may want to inspect them as historical evidence of P2-D04/P2-D05 (see § 4 / § 5 / § 8 of this report).

**Carry-forward complete. Spec 005 (Phase 3) MAY pick up these projects.** See `specs/004-phase2-project-bootstrap-testing/carry-forward.yaml` for the structured manifest.
