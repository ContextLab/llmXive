# Quickstart — Quality Fixes 009

Five-minute tour of the new auditors and the four user-story landing surfaces.

## Prerequisites

- Python 3.11 venv with project dependencies installed (`pip install -e .`).
- LaTeX toolchain on PATH (`lualatex`, `bibtex`).
- Poppler installed (`brew install poppler` on macOS, `apt-get install poppler-utils` on Linux) — provides `pdftotext`.
- Repo cloned at a clean working tree on branch `009-quality-fixes-pass`.

## 1. Audit personalities — see what voice + curation look like

```bash
# Score every persona's prompt + each persona's most recent contribution
python -m llmxive.audit.cli personality \
  --personalities-dir agents/prompts/personalities \
  --feed-glob 'projects/PROJ-*/activity.jsonl' \
  --since 7d

# Expected: a manifest under .audit/personality_rubric/<ts>.json
# Every accepted contribution scored 4×3 on the rubric; any flagged "manufactured" calls out the missing axis.
```

What you should see:
- Every persona card has ≥3 `interest_signals` in its frontmatter (FR-003).
- The most recent week of contributions shows non-trivial `abstain` density (manufactured-praise was the failure mode).
- Each accepted `comment`/`contribute` has a `curatorial_pointer` field.

## 2. Audit speckit artifacts — find template stubs

```bash
# Classify every speckit artifact under projects/ as real|partial|template
python -m llmxive.audit.cli speckit \
  --projects-dir projects \
  --templates-dir .specify/templates

# Inspect the manifest — every `template`-classified artifact is a prune candidate
jq '.items[] | select(.classification == "template") | .path' \
  .audit/template_vs_real/<ts>.json
```

To prune them (one-time clean-up for User Story 2):

```bash
python -m llmxive.audit.cli speckit --prune --confirm
# Atomic single commit; the manifest is committed alongside.
```

What you should see:
- A drop in `projects/PROJ-*/specs/**/*.md` file count.
- No `real`-classified artifact deleted (legacy migrations like PROJ-006 stay).
- CI will now fail if any `template` artifact reappears.

## 3. Audit PDFs — find rendering defects

```bash
# Walk every page of every PDF in papers/ and classify defects
python -m llmxive.audit.cli pdf \
  --papers-dir papers \
  --class papers/.style/llmxive.cls

# See the supported-PDFs registry update
git diff papers/.supported.json
```

What you should see:
- Each defect localised to (`paper_id`, `page`, `defect_type`).
- After fixes (User Story 3 implementation lands), the registry grows automatically; CI rebuilds every registered paper on every push.

## 4. Build a PDF without LLM involvement (Story 3 acceptance scenario 4)

```bash
# Restyle one arXiv source bundle and compile it with zero LLM calls
python -m llmxive.pipeline.pdf_pipeline.cli build \
  --source-dir papers/sources/PROJ-XXX-... \
  --out-dir papers/build/PROJ-XXX-...

# Verify no LLM call was made
grep -r "anthropic\|openai\|google.*generativeai\|llmxive.backends" \
  src/llmxive/pipeline/pdf_pipeline/   # must return nothing
```

What you should see:
- A deterministic PDF byte-stable on a second invocation (modulo timestamps).
- Every reference rendered `[N]` in cite-order; figures bounded; author block uniform.

## 5. Inspect feedback-loop delivery (Story 4 acceptance)

```bash
# Run the seeded-project test
pytest tests/real_call/test_seeded_project_revision_loop.py -v

# Look at one project's activity feed
jq -s . projects/PROJ-XXX-.../activity.jsonl | head -50

# Verify the manifest auditor accepts every recent dispatch
python -m llmxive.audit.cli feedback_loop \
  --projects-dir projects --since 24h
```

What you should see:
- Every recent agent contribution includes a `comments-considered` manifest block.
- The feedback-loop auditor reports 100% delivery (SC-010) and ≥95% valid manifests (SC-011).
- Seeded comments are addressed (`addressed` or `rebutted`) by ≥80% of revision runs (SC-012).

## 6. Continuous integration

`.github/workflows/audit.yml` runs all four auditors on every push:

- `audit-personality` (FR-004 + FR-005)
- `audit-speckit` (FR-011)
- `audit-pdf` (FR-022)
- `audit-feedback-loop` (FR-034)

A red CI build means a regression in one of the SCs (SC-002, SC-005, SC-009, SC-010, SC-011).

## Where to look in the code

- Auditors: [src/llmxive/audit/](../../src/llmxive/audit/)
- Activity feed store: [src/llmxive/feed/](../../src/llmxive/feed/)
- PDF pipeline (deterministic, no LLM): [src/llmxive/pipeline/pdf_pipeline/](../../src/llmxive/pipeline/pdf_pipeline/)
- Runner integration (feed injection + manifest validation): [src/llmxive/agents/runner.py](../../src/llmxive/agents/runner.py)
- Personality prompt + cards: [agents/prompts/personality.md](../../agents/prompts/personality.md), [agents/prompts/personalities/](../../agents/prompts/personalities/)
- LaTeX class: [papers/.style/llmxive.cls](../../papers/.style/llmxive.cls)

## Where to look for evidence (Constitution Principle II)

- Real-call tests under [tests/real_call/](../../tests/real_call/) — exercise the full corpus.
- Integration tests under [tests/integration/](../../tests/integration/) — exercise emitter/runner code paths.
- Fixture corpora under [tests/fixtures/audit/](../../tests/fixtures/audit/) — positive + negative cases per auditor (FR-024).
