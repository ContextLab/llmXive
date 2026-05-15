# Quickstart

Three runnable scenarios — each validates one of the spec's P1/P1/P2 user stories.

## Scenario 1 — Generate one personality contribution end-to-end (User Story 1)

Goal: confirm the umbrella prompt produces a frontmatter-compliant contribution on the first attempt; the rubric reads it; liveness check passes for the cited pointer; the contribution lands on disk.

```bash
# Pick a fresh project (any project in flesh_out_complete or later)
export PROJ_ID="PROJ-562-identifying-stimulus-driven-neural-activ"
# Force a single personality tick (no rotation advancement)
LLMXIVE_NETWORK_TESTS=1 python -m llmxive personality tick --persona ada-lovelace --project "$PROJ_ID"

# Verify the contribution was written
ls projects/$PROJ_ID/reviews/research/ada-lovelace-simulated__$(date +%Y-%m-%d)__research.md

# Verify the frontmatter has all required fields
python -c "
import yaml, sys
text = open(sys.argv[1]).read()
fm = yaml.safe_load(text.split('---')[1])
assert fm['position'] in {'lean_toward','lean_against','suggest_revision','abstain'}, fm
assert fm.get('interest_signal'), 'missing interest_signal'
if fm['position'] != 'abstain':
    assert fm['adjacent_work'], 'missing adjacent_work'
    for w in fm['adjacent_work']:
        assert 'verified_at' in w, 'liveness check did not stamp verification'
print('PASS')
" projects/$PROJ_ID/reviews/research/ada-lovelace-simulated__$(date +%Y-%m-%d)__research.md
```

Expected: `PASS`. If liveness check fails, the contribution does not land on disk (per FR-002).

## Scenario 2 — Speckit artifact prune dry-run (User Story 2)

Goal: confirm the audit script identifies template-shaped artifacts and reports them without deletion.

```bash
# Dry-run: audit-only, no deletions
python -m llmxive speckit audit-artifacts --dry-run --out /tmp/speckit-audit.json

# Inspect the report
python -c "
import json
r = json.load(open('/tmp/speckit-audit.json'))
print(f'audited {r[\"total_artifacts\"]} artifacts')
print(f'REAL: {r[\"summary\"][\"real\"]}, TEMPLATE: {r[\"summary\"][\"template\"]}')
print('TEMPLATE paths:')
for a in r['artifacts']:
    if a['classification'] == 'TEMPLATE':
        print(' -', a['path'])
        for d in a['transitive_dependents']:
            print('     dep:', d)
"
```

Expected: a small list of TEMPLATE paths (per the audit run that informed the spec, only PROJ-023's secondary `specs/002-.../spec.md` should be classified TEMPLATE on the current repo).

To actually execute the prune + stage rollback:

```bash
python -m llmxive speckit prune-templates --apply
```

This deletes the template artifacts, deletes their transitive dependents, rolls back the affected projects' `current_stage` to the latest stage with surviving real artifacts, and appends a `template_artifact_purge` event to each project's `history.jsonl`. The run is logged to `state/run-log/<YYYY-MM>/<run-id>.jsonl` per FR-023.

## Scenario 3 — PDF audit against `docs/papers/` (User Story 3)

Goal: confirm the audit script renders every page of every PDF, runs the deterministic checkers, classifies failures, and exits zero on a clean audit set.

```bash
# Make sure poppler is installed (required by pdf2image)
which pdftoppm || (echo 'install poppler: brew install poppler OR apt-get install poppler-utils' && exit 1)

# Run the audit; produces JSON reports under state/audit/pdf/<date>/
python -m llmxive pdf-pipeline audit docs/papers/ --out-dir state/audit/pdf/

# Exit code: 0 if every page passed, non-zero if any failure (including audit_tool_crash)
echo "audit exit code: $?"

# Summary across all reports
python -c "
import json, pathlib, datetime
today = datetime.date.today().isoformat()
reports = list(pathlib.Path(f'state/audit/pdf/{today}').glob('*.json'))
total_pages = total_failures = 0
class_counts = {}
for p in reports:
    r = json.load(open(p))
    total_pages += r['total_pages']
    total_failures += r['summary']['total_failures']
    for k, v in r['summary']['failure_classes'].items():
        class_counts[k] = class_counts.get(k, 0) + v
print(f'audited {len(reports)} PDFs, {total_pages} pages, {total_failures} failures')
print('by class:', class_counts)
"
```

Expected (after implementation): zero failures across all reports.

For a single PDF (e.g., to drill into a specific failure):

```bash
python -m llmxive pdf-pipeline audit docs/papers/PROJ-001-mechanistic-.../main-llmxive.pdf \
  --out state/audit/pdf/$(date +%Y-%m-%d)/PROJ-001.json
```

## Verifying zero-LLM constraint (FR-013 / SC-007)

```bash
# Static AST test — fails if any pdf_pipeline file imports an LLM client
python -m pytest tests/unit/test_pdf_pipeline_no_llm.py -v

# Runtime check — running the audit with no API keys set
env -i HOME="$HOME" PATH="$PATH" python -m llmxive pdf-pipeline audit docs/papers/
# (Should succeed; LLM client import would raise via the module-level guard.)
```

## Verifying scheduler throughput (SC-005)

```bash
# Set the parallelism cap and force a single tick
PIPELINE_PARALLELISM=8 python -m llmxive pipeline tick --max-projects 8 --dry-run

# Inspect what would advance:
# Expected: up to 8 distinct project IDs, none monopolized by a single in_progress project.
```
