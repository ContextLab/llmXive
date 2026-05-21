# Quickstart — Paper Revision Implementer + Publisher

Operator-facing recipes for the spec-013 agents. All commands assume
you're at the repo root and have a working Python environment with
`pip install -e ".[dev]"` already run.

## Prerequisites

```bash
# Dartmouth Chat API key (for the LLM-driven implementer; existing pattern)
cat > ~/.config/llmxive/credentials.toml <<'EOF'
[dartmouth]
api_key = "..."

# Zenodo Sandbox token for tests (separate account at sandbox.zenodo.org)
[zenodo_sandbox]
api_token = "..."

# Zenodo production token for real publication (Account -> Applications -> Personal access tokens
# with scopes deposit:write + deposit:actions)
[zenodo]
api_token = "..."
EOF

# LaTeX toolchain on PATH:
which lualatex bibtex   # both required

# Verify scheduler picks up implementable projects
python -c "from llmxive.scheduler import _NEVER_PICK; \
  assert 'READY_FOR_IMPLEMENTATION' not in _NEVER_PICK; \
  assert 'paper_accepted' not in _NEVER_PICK"
```

## Recipe 1 — Run the implementer on a fixture project

```bash
# Pick a project parked at READY_FOR_IMPLEMENTATION
llmxive project status PROJ-578-https-arxiv-org-abs-2605-14906

# Drive a single scheduler tick (the implementer picks up the project)
llmxive run --once --project PROJ-578-...
```

**Expected outputs**:
1. `specs/auto-revisions/PROJ-578-.../round-1/implementer-log.yaml` written
2. `projects/PROJ-578-.../paper/source/main.tex` modified (line-level edits)
3. `projects/PROJ-578-.../paper/metadata.json::authors` extended with one new `kind: "llm"` entry
4. `projects/PROJ-578-.../paper/revision_history.yaml` appended (round 1)
5. `projects/PROJ-578-.../paper/pdf/main.pdf` regenerated
6. `current_stage` transitions `READY_FOR_IMPLEMENTATION → paper_review`

**Inspect**:
```bash
yq '.task_outcomes[] | {id: .task_id, status: .status}' \
  specs/auto-revisions/PROJ-578-.../round-1/implementer-log.yaml | head -20
```

## Recipe 2 — Drive the per-specialist re-review

After the implementer routes the project to `paper_review`, the next
scheduler tick fires all 12 specialist reviewers with the spec-012
diff-check protocol.

```bash
llmxive run --once --project PROJ-578-...
```

**Expected**: each specialist reads their prior review + the modified
paper and emits a new review record. If every reviewer accepts →
`paper_accepted`. Otherwise → back to `READY_FOR_IMPLEMENTATION` with
a round-2 revision spec.

## Recipe 3 — Publish an accepted paper to Zenodo Sandbox

For testing — the `[zenodo_sandbox]` token gates the call to
`sandbox.zenodo.org`.

```bash
# A project at paper_accepted is picked up by the publisher agent automatically.
LLMXIVE_ZENODO_ENV=sandbox llmxive run --once --project PROJ-578-...
```

**Expected outputs**:
1. `projects/PROJ-578-.../paper/publication.yaml` written
2. `projects/PROJ-578-.../paper/metadata.json` gets `doi`, `doi_url`, `zenodo_id`, `volume`, `issue`
3. `projects/PROJ-578-.../paper/pdf/main.pdf` regenerated with `\paperstatus{Auto-Reviewed | Auto-Revised | Published}`, `\paperdoi{10.5072/zenodo.<n>}`, `\papervolume{26}`, `\paperissue{05}`
4. PDF uploaded to Zenodo Sandbox; deposition published
5. `current_stage` transitions `paper_accepted → posted`
6. Activity-log entry emitted

**Verify**:
```bash
yq '.doi, .doi_url, .zenodo_id' projects/PROJ-578-.../paper/publication.yaml
# Optional: HEAD the DOI URL (sandbox DOIs do resolve, but are flagged as test)
curl -I "$(yq -r .doi_url projects/PROJ-578-.../paper/publication.yaml)"
```

## Recipe 4 — Publish to production Zenodo (real DOI)

Same as Recipe 3 but without the sandbox env var. The `[zenodo].api_token`
section is used. Production DOIs are PERMANENT — Zenodo does not allow
deletion of published depositions, only `newversion` updates.

```bash
llmxive run --once --project PROJ-578-...
```

## Recipe 5 — Re-publish after a new revision round (DOI versioning)

If a `posted` project re-enters `paper_review` (e.g., a critical bug is
found after publication) and eventually re-reaches `paper_accepted`:

```bash
# The next scheduler tick after re-acceptance picks up the project again.
llmxive run --once --project PROJ-578-...
```

The publisher detects `metadata.json::zenodo_id` is set, invokes
Zenodo's `/actions/newversion` endpoint, and registers a NEW DOI version.
The original DOI continues to resolve to the prior PDF.

**Verify**:
```bash
yq '.doi_versions' projects/PROJ-578-.../paper/publication.yaml
# Should show 2 entries; the second is the new canonical doi.
```

## Recipe 6 — Recover a `publish_blocked` project

If Zenodo's API is unreachable for 5 consecutive ticks, the project
transitions to `publish_blocked`. To retry:

```bash
llmxive project republish PROJ-578-...
# This rolls current_stage back to paper_accepted and resets the
# failure counter. The next scheduler tick re-attempts publication.

llmxive run --once --project PROJ-578-...
```

## Recipe 7 — Run the real-call tests

```bash
LLMXIVE_REAL_TESTS=1 pytest \
  tests/real_call/test_paper_reviewer_chunk_summary.py \
  tests/real_call/test_implementer_e2e.py \
  tests/real_call/test_publisher_zenodo_sandbox.py \
  -v
```

These tests exercise:
- Real Dartmouth Chat API call for chunk-summary generation
- Real implementer round on a synthetic 3-task fixture
- Real Zenodo Sandbox publication producing a `10.5072/...` test DOI

Expected wall-clock budget: ≤2 min per test (Zenodo Sandbox is
typically faster than production).

## Troubleshooting

| Symptom | Likely cause | Fix |
|-|-|-|
| `KeyError: 'dartmouth'` in credentials | Token not provisioned | Add `[dartmouth]` section to `~/.config/llmxive/credentials.toml` |
| `ZenodoAPIError: 401` | Token missing scopes | Regenerate token at zenodo.org with `deposit:write` + `deposit:actions` |
| Implementer marks every task `skipped` | LLM not returning structured edits | Inspect `implementer-log.yaml::model_response_excerpt`; check prompt at `src/llmxive/agents/prompts/implementer_edit.md` |
| LaTeX compile fails after every edit | Class file mismatch | Verify `papers/.style/llmxive.cls` is on TEXINPUTS path; run a manual `lualatex` on the modified `main.tex` to surface the actual error |
| `publish_blocked` after 5 retries | Zenodo down or token expired | `curl -I -H "Authorization: Bearer $ZENODO_API_TOKEN" https://zenodo.org/api/deposit/depositions` should return 200; if not, regenerate token |
| DOI resolves to "page not found" | Zenodo not yet propagated | Sandbox DOIs resolve in ~30s; production in ~5min. Retry the HEAD after waiting. |
