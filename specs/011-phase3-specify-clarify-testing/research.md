# Phase 0 Research: Phase 3 (Spec Kit Specify → Clarify) Validation

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-05-17

## Purpose

Resolve every decision that downstream phases depend on, with explicit rationale and alternatives. The spec has zero `[NEEDS CLARIFICATION]` markers; this document records the design decisions implicit in the plan so that anyone reading the code later understands WHY each path was chosen.

---

## D1. Where does the inspection-capture wrap go?

**Decision**: A new helper module `src/llmxive/speckit/_inspection.py` exposes `capture(project_dir, agent_name, system_prompt, user_prompt, raw_response, parsed_output, file_diffs, reset_artifacts, spec_root)` which writes `<spec_root>/inspections/<project_id>/<agent_name>.json`. The driver (`scripts/validate_phase3.py`) wraps the existing `python -m llmxive run` invocation by monkey-patching `chat_with_fallback` for the duration of the call to capture prompts + response, and reads the agent-written `spec.md` before+after to compute the diff.

**Rationale**:
- FR-013 forbids modifying the Specifier/Clarifier agents themselves unless a real bug is found. A capture helper that lives outside the agents satisfies this constraint.
- Monkey-patching `chat_with_fallback` (the canonical LLM entry point used by both agents through `slash_command.SlashCommandAgent.handle_response`) gives us the prompts + response without touching any agent code. The patch is scoped to the duration of one invocation and removed in a `try/finally` block.
- The before/after diff of `spec.md` is reconstructed from the filesystem snapshot — also no agent edits needed.

**Alternatives considered**:
- (a) Adding an `inspect: bool = False` parameter to each agent's `__init__`. Rejected — invasive (modifies 2 agent classes + the orchestrator), and FR-013 disallows it without bug justification.
- (b) Parsing the run-log JSONL after the run completes. Rejected — the run-log captures outcome metadata, not the verbatim prompt or LLM response. Would require expanding the run-log format, which is a project-wide concern (used by website Activity tab, etc.).
- (c) Running each agent class directly in-process with a custom chat function. Rejected — bypasses the production code path (orchestrator + lock acquisition + run-log write). Violates the spec's "go through production path" intent.

## D2. How does FR-015 reset semantic work without modifying the agents?

**Decision**: The validation harness (`scripts/validate_phase3.py`) performs the reset at preflight time. Before invoking `python -m llmxive run`, the harness checks `projects/<id>/specs/<n>-<slug>/` for any existing directories and `shutil.rmtree`s them. The list of removed paths is captured in the upcoming inspection record's `reset_artifacts` key. The harness also detects + removes any stale `state/projects/<id>.yaml::speckit_research_dir` pointer that referenced the wiped dir (sets the field to `None`).

**Rationale**:
- FR-013 — agents stay untouched. The reset is an environmental concern, not an agent concern.
- The reset is deterministic and inspectable: the maintainer can `git diff` the harness output to see what was removed.
- `speckit_research_dir` is set on the Project model by `SpecifierAgent.write_artifacts` (line 161 of specify_cmd.py). Resetting it to `None` keeps the validator happy when the stage is rolled back to `project_initialized`.

**Alternatives considered**:
- (a) Adding a `--reset` flag to `python -m llmxive run`. Rejected — broader scope than this spec; would require a per-stage cleanup contract that doesn't exist yet.
- (b) Letting the Specifier overwrite in place. Rejected — Specifier writes via `feature_dir.mkdir(parents=True, exist_ok=True)`; the dir name is derived from `create-new-feature.sh` which numbers sequentially, so a previous run's `001-test` and a new run's `001-test` would conflict on `spec.md`. The Specifier doesn't delete the pre-existing spec.md; it overwrites by `spec_path.write_text`. Risk: a partial older spec.md whose section headers don't match the new content could leave the file in a weird half-state if writing fails mid-stream. Wiping is safer.

## D3. Should the three regression tests (FR-012) mock the LLM?

**Decision**: Yes — the three FR-012 tests mock the LLM response (using the same `monkeypatch.setattr` pattern the project already uses for `chat_with_fallback` in other integration tests). The end-to-end smoke test against PROJ-261/262 calls the real LLM.

**Rationale**:
- Constitution Principle III ("Robustness & Reliability — Real-World Testing") says mocks are prohibited as the PRIMARY verification path. The PRIMARY Phase 3 verification IS the end-to-end real-call run on PROJ-261/262. The regression tests are SECONDARY — they exist specifically to catch regressions in the guards (`_real_only_guard`, `_diff_guard`, `clarify_cmd._parse_clarifier_response`) when an LLM returns known-bad shapes. Reproducing those known-bad shapes via a real LLM call is non-deterministic; mocking is the only honest way to test "does the guard reject this exact bad shape?".
- The mocked tests use the REAL guard functions — only the LLM response is faked. This satisfies the "same calling syntax as the real path so divergence is caught" requirement from Principle III.

**Alternatives considered**:
- (a) Pure real-call regression tests (no mocks). Rejected — would require crafting prompts that reliably elicit each known-bad shape from the live LLM, which is non-deterministic and burns budget every CI run.
- (b) Recorded-fixture playback (vcr-style). Rejected — adds a new dependency (`vcrpy` or similar) for marginal benefit; the mock pattern already in use is simpler.

## D4. What is the JSON shape of an inspection record?

**Decision**: A single JSON object per `(project, agent)` pair. Top-level keys: `project_id`, `agent_name`, `agent_version`, `model`, `backend`, `started_at`, `ended_at`, `duration_s`, `outcome`, `reset_artifacts`, `prompts`, `raw_response`, `parsed_output`, `file_diffs`, `error`. See `contracts/inspection-record.md` for the formal schema.

**Rationale**:
- JSON (not YAML) so the file can be loaded by any language without a YAML lib; pretty-printed (`indent=2`) so a maintainer can diff two records by eye.
- Single-file-per-invocation (vs. one giant log file) so a re-run on one project overwrites only its own records.
- Includes the `error` field even when null so the schema is uniform across success + failure cases.

**Alternatives considered**:
- (a) One file per record, JSONL-streamed. Rejected — harder to diff; loses pretty-printing benefit.
- (b) Splitting prompts + response into separate `.txt` files. Rejected — fragmentation; harder to git-grep across.

## D5. Carry-forward manifest format

**Decision**: A single YAML file `specs/011-…/carry-forward.yaml` at the spec root. Top-level keys: `spec`, `generated_at`, `final_commit`, `projects` (list, one entry per canonical with `project_id`, `final_state`, `final_commit`, `agents_run` (list of `{name, iterations, outcome}`), `justification` (free-form prose ≤ 200 words explaining what passed / what's parked / why)). Matches the precedent set by `specs/004-…/carry-forward.yaml` so Phase 4's validation can read it without adapter code.

**Rationale**:
- Consistency with the existing carry-forward convention (spec 004 — Phase 2 → Phase 3 handoff) means Phase 4's validation just opens the file and processes the `projects` list.
- YAML (not JSON) matches the existing precedent.
- The `final_commit` and `final_state` together let a future auditor reconstruct the exact moment of handoff.

**Alternatives considered**:
- (a) Different schema from spec 004. Rejected — uses brand-new format for no benefit; breaks the convention.
- (b) Skipping the manifest if all projects pass (only emit on partial failure). Rejected — Phase 4 validation needs the manifest unconditionally to know which canonicals to operate on.

## D6. What counts as a "real bug" that justifies modifying the agents (vs. just patching the harness)?

**Decision**: A real bug = any failure mode where the agent's behavior diverges from the spec or the prompt's stated contract. Examples that would qualify: Clarifier returns 0 patches when 5 markers are present and the prompt explicitly says "resolve every marker"; Specifier writes `spec.md` with diff-prefix content that bypasses the `_diff_guard`; the wall_clock budget is exceeded by 2× without a timeout signal. Examples that would NOT qualify: stylistic preference about output formatting; a prompt-engineering tweak to elicit more detail; a perf optimization. When a real bug is found, the bug-fix commit MUST cite the failing inspection record by path (e.g., `specs/011-…/inspections/PROJ-261/clarifier.json`).

**Rationale**:
- FR-013 explicitly says no agent edits without a real bug. Defining "real bug" up front prevents scope creep during execution.
- Citing the inspection record by path makes the bug fix reproducible — any future reader can open the cited record and see exactly the failure that motivated the fix.

**Alternatives considered**:
- (a) Allowing any improvement during Phase 3 work. Rejected — bloats the spec's scope into "improve the agents" which is out of scope per FR-013.
- (b) Forbidding all agent edits absolutely. Rejected — would block fixing a genuinely surfaced bug, which is the spec's whole point of running the validation.

## D7. Sequencing — single-project vs. parallel runs?

**Decision**: Sequential per canonical. The harness processes PROJ-261 fully (Specifier → Clarifier → carry-forward update for this project) before moving to PROJ-262. Concurrent invocations on the same project are blocked by the existing per-project lock in `pipeline/lock.py`; the harness assumes no other cron tick is running against the canonicals during the validation window.

**Rationale**:
- 2 canonicals × 2 agents × ≤60s each ≈ 4 minutes typical. Parallelism saves ~half the wall-clock at the cost of much harder debugging when one project fails. Sequential is simpler and the time savings are negligible.
- Sequential simplifies the inspection-record write path — no risk of race-condition file collisions.

**Alternatives considered**:
- (a) Parallel via `concurrent.futures.ThreadPoolExecutor(max_workers=2)`. Rejected — added complexity for trivial time savings.

## Open follow-ups (not in scope for this spec)

None. The spec's scope is fully covered by D1–D7.
