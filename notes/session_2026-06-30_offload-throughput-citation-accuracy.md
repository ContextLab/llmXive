# Session 2026-06-30 — Kaggle offload, throughput, citation accuracy

Goal (standing): get **10+ projects to `paper_drafting_init`** ("paper init")
WITHOUT sacrificing scientific quality — by making real pipeline fixes
(more robust + powerful + efficient + comprehensive). The count climbs over
time via CI, **not instantly** (user's explicit framing).

State at session end: **3 at `paper_drafting_init`** (PROJ-575, 601, 607).
The count is gated on CI/cron runtime (implement batches → execution →
review → Kaggle offloads), which a local session cannot compress.

## Fixes pushed this session (all suite-green, quality gates intact)

1. **Kaggle GPU offload — fully wired** (`3e5c775c9`, `47045b7af`). The offload
   lane (issue #367) existed but never fired in the main pipeline:
   - `llmxive-pipeline.yml`'s run step never passed `KAGGLE_API_TOKEN` →
     `offload.is_available()` was False there. Added it.
   - `code_adapter.md` (v1.1.0) hard-stripped GPU code → no compute-infra
     failure → no offload trigger → CPU fabrication. Now KEEPS scaled GPU code
     (`device="cuda"`, ~16GB/~9h) so the CPU run fails fast and auto-offloads.
   - `execution/stage.py` fabrication feedback steers GPU-needed metrics to
     Kaggle, not a CPU proxy.
   - `credentials.load_kaggle_creds()` resolves Kaggle creds from
     `credentials.toml` (a `[kaggle]` table / flat keys / verbatim token), same
     place as the Dartmouth key; `offload._ensure_kaggle_auth` routes through it.
   - NOTE: the offload runs ONLY in CI (kaggle CLI not installed locally; creds
     are CI secrets; kernels are async). Cannot be driven from a local session.

2. **`--stage` dispatch bug** (`22306d58c`). `llmxive-pipeline.yml`'s
   `workflow_dispatch` dropdown offered STEP names (`speckit_implement`, …) but
   the CLI `--stage` validates against the `Stage` enum (project STATES) → any
   pick hard-failed `exit 2`. CLI error now lists valid Stages; input is
   free-text Stage. Also fixed a self-introduced conftest env-leak: `_cmd_run`
   sets `LLMXIVE_GROUNDING_GUARD`/`CLAIM_LAYER`/`CLAIM_FILL` via
   `os.environ.setdefault`; an in-process `_cmd_run` test leaked them into
   network-free reviser tests (exact-call-count asserts) → order-dependent
   failure. New autouse fixture snapshots+restores the three flags.

3. **Citation-gate accuracy** (`021748536` / `4a449f0cb`). Publisher article
   pages (msp.org, ScienceDirect, …) serve a GENERIC `<title>` (journal/issue)
   while the real article title is in the BODY → `<title>`-only overlap
   false-MISMATCHed real articles (a hard-blocking, fabrication-grade verdict).
   `_title_in_body` upgrades MISMATCH→VERIFIED when the cited title appears
   VERBATIM (≥4-token contiguous phrase) in the page body. STRENGTHENS the gate
   (a fabricated title is absent → stays MISMATCH); verified against the live
   msp.org page + offline tests.

4. **Implement throughput** (`3d3a3bdc9`). `IMPLEMENT_TASK_BATCH` 12→30. The old
   cap was sized by a STALE comment assuming a "50-min implement cron", but
   maintenance.yml (50 min) only seeds brainstorms — the implement batch runs in
   advance.yml/reprocess.yml (150 min) + the pipeline (330 min). The 600s
   wall-clock budget (the real safety lever) is unchanged, so raising the COUNT
   cap lets fast scaffolding/setup tasks drain many-per-batch with ZERO added
   timeout risk. No per-task quality change.

## Stage-by-stage investigation (what's sound)

- **77 in_progress projects; only 4 ever reached execution.** The other 73 have
  INCOMPLETE task lists (e.g. PROJ-492 64/68, PROJ-099 8/61, PROJ-256 48/1) —
  draining their implement batches per cron tick, NOT stuck. (Throughput fix
  above targets exactly this.)
- **Execution/fabrication gate is correct.** PROJ-306's stale record shows "235
  fabricated signals" from `code/.venv` (PIL/pytest) — but the CURRENT
  `find_fabrication` returns **0** for 306 (15606 `.venv`/site-packages files
  skipped by `_skip_path`; fix `ad5ce2c25`). The record is stale telemetry,
  re-computed fresh each CI attempt. 306's real blocker is a per-project import
  bug (`from utils import expon`) its fix-loop resolves — cron-bound.
- **Review zone** (552, 261) holdouts: 552 is fabrication-clean but has GENUINELY
  broken citations (real 404 `katlas.org/wiki/KnotAtlasAPI`, dead host
  `knotinfo.math.indiana.edu`, non-existent GitHub path) — the gate is RIGHT to
  block; repairing those is the project's fix-loop, not a hand-edit.

## Path to 10+ (cron-bound, no quality compromise)

GPU papers: CI fix-loop restores GPU code → Kaggle offload → real results →
research_complete. Brainstorm projects: faster implement batches → execution →
review. Both run in CI over many cron cycles (advance.yml every cycle ×6 workers,
pipeline every 3h). Local session cannot compress this.

## Resumption pointers

- Re-check count: scan `projects/*/` for `current_stage == paper_drafting_init`.
- To drive a GPU offload locally in a future session: `pip install kaggle` +
  drop creds into `~/.config/llmxive/credentials.toml` (now supported), then the
  offload `is_available()` and can dispatch.
- Constraints held all session: GENERAL platform fixes only (src/, agents/,
  workflows/), never per-project code/data edits; `PRE_COMMIT_ALLOW_NO_CONFIG=1`;
  push via `git merge -X ours origin/main` loop; discard driver byproducts
  (`git checkout -- state/ projects/`); human input only for DOI sign-off.

## Update — deep Kaggle-offload repair + local-driving CI-bound proof

After wiring local Kaggle creds (user provided a `KGAT_…` token at ~/Desktop;
username `jeremy9`), driving the offload locally surfaced that it was THOROUGHLY
broken — NINE distinct bugs, all fixed + pushed (suite green 4560):

1. KAGGLE_API_TOKEN not passed to llmxive-pipeline.yml (the execution lane).
2. code_adapter stripped GPU code (→ CPU fabrication, no offload trigger).
3. fabrication feedback steered GPU metrics to a CPU proxy.
4. creds resolved only from env, not credentials.toml (`load_kaggle_creds`).
5. **kgat_ tokens use BEARER auth, not Basic** — Kaggle's "Create New API Token"
   now issues `KGAT_…` personal-access tokens; the kaggle>=1.7 client consumes
   them via `KAGGLE_API_TOKEN` (Bearer). `_ensure_kaggle_auth` now detects a
   kgat_ key (case-insensitive) + exports KAGGLE_API_TOKEN; `load_kaggle_creds`
   pairs a bare kgat_ token with KAGGLE_USERNAME.
6. **broken wheel**: bare `pip install kaggle` pulls kaggle 2.2.3 + kagglesdk
   0.1.32, whose wheel drops `competitions.legacy` → `import kaggle` raises →
   is_available False. PINNED `kaggle==2.2.3` + `kagglesdk==0.1.31` in advance.yml
   + reprocess.yml + ADDED the install to llmxive-pipeline.yml.
7. title!=slug for long names → kaggle>=2 rejects push 400. Title now derives
   from the (truncated) slug so it round-trips.
8. poll() false-ERROR on a transient `404 Client Error` (substring "error"). Now
   parses only the reported `has status "<X>"` token (incl. 2.x enum form).
9. kernel cloned the whole repo INTO /kaggle/working (the output) → retrieve
   downloads the entire repo + times out. Now clones to /tmp/llmxive-clone.

PROVEN on real Kaggle GPU: dispatched 657 → kernel ran clone+install+run+retrieve
end-to-end. The clean retrieve (just the log) confirmed fix #9. The run FAILED on
657's OWN code (circular import `src/inference/hooks.py ↔ logging_hooks.py`),
producing no artifacts — i.e. GPU papers need the fix-loop to repair THEIR code
before offload yields results.

Local driving of a GPU paper is **CI-bound by design**: the offload clones the
repo from origin, so each fix-loop repair must be committed+pushed before the
offload can use it. Pushing intermediate per-project state locally risks corrupting
origin (which the crons + the offload build on), so only CI's controlled
commit-push step can stage fixes safely. Confirmed: a local drive of 657 sat in the
implement phase, 0% CPU, WAITING on the slow free reasoning model (Dartmouth qwen
ignores BOTH `enable_thinking=False` AND `/no_think` — ~15s/call even for a 1-word
answer; tested live). Killed the drive; nothing broken pushed.

NET: the GPU-offload path (the user's insight) went from 9-ways-broken to
proven-working. Count stayed 3 at paper_drafting_init — crossings are multi-day CI
runtime (fix-loop rounds × ~15s reasoning × ~15-min async Kaggle × 3-round review
× ~16 GPU papers). ACTION to unlock at scale: set CI secret KAGGLE_API_TOKEN =
the kgat_ token + add KAGGLE_USERNAME=jeremy9 (the new client needs Bearer + a
username for the kernel ref).
