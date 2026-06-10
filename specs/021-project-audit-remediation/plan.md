# Implementation Plan — Spec 021 (Project-Audit Remediation, issue #294)

**Branch**: `claude/zealous-gates-e5pv8o` | **Spec**: [spec.md](spec.md)

## Summary

Execute the actionable core of audit issue #294: reconcile the repo's
canonical truth (delete the contradictory legacy config universe, purge
abolished point-system text, pin prose↔registry model agreement), make
the librarian relevance judge deterministic (#112), convert fatal
LLM-output validation failures into bounded retry-with-feedback, and add
a prompt-regression eval gate. Validate with real calls (Constitution
III) on real projects.

## Technical context

**Language**: Python 3.11 (`src/llmxive/`), no new runtime dependencies.
**Testing**: pytest; real-call suites gated by `LLMXIVE_REAL_TESTS=1`.
**Eval gate**: promptfoo CLI (node 22, `npx`, no checked-in node deps)
with a Python provider/assertion that reuse production code.
**Environment note**: the implementation container cannot reach
`chat.dartmouth.edu` (network policy); real-call validation uses the
constitutionally-sanctioned local transformers backend
(`Qwen/Qwen2.5-0.5B-Instruct`) through the identical router code path,
plus the real external claim sources (OEIS, Wikipedia, Wikidata, arXiv,
Crossref), which are reachable. CI (where the Dartmouth secret exists)
exercises the Dartmouth path via the existing real-call workflows and
the new prompt-eval workflow.

## Constitution check

| Principle | Disposition |
|---|---|
| I — Single Source of Truth | Core of the change: deletes the parallel config universe (zero-reference sweep performed first); eval assertions import the production parser instead of re-implementing it; `test_config_consistency` pins README↔registry agreement. |
| II — Verified Accuracy | Model-name reconciliation driven by run-log evidence (`google.gemma-4-31B-it` served live; `KNOWN_FREE_MODELS`), not memory. No new external claims introduced. |
| III — Real-World Testing | New real-call test (`test_relevance_judge_real.py`) runs real inference 3× + a disk cache round-trip; local backend + claim resolvers validated against real models/sources. Mock-style unit tests are the secondary layer, added alongside the real-call test. |
| IV — Free-First | No paid services. `instructor` dependency rejected; promptfoo is OSS run via `npx`. Guard test enforces free-models-only registry. |
| V — Fail Fast | Retry loop is bounded (2 re-asks) and only for typed validation errors; all other exceptions keep fail-fast semantics. Judge cache never latches fail-open outcomes. |
| VI — Convergent Review | Unchanged; this work removes the last user-facing text contradicting it. |

## Project structure (files touched)

```
Deleted: pipeline_config.yaml, pipeline_schema.json, package.json,
         package-lock.json, prompts/, system_prompts/, src/core/,
         scripts/{10 .js files, pipeline_api.py, pipeline_config_manager.py,
         configurable_pipeline_orchestrator.py, llmxive-cli.py,
         code_execution_manager.py, test-full-pipeline.sh,
         migrate_legacy_layout.py}, tests/{legacy island}
Modified: src/llmxive/web_data.py, src/llmxive/agents/{advancement,base,
          librarian,paper_reviewer,research_reviewer}.py,
          src/llmxive/backends/{local,router}.py,
          src/llmxive/librarian/relevance_judge.py,
          README.md, CLAUDE.md, web/index.html (+ regenerated
          web/data/projects.json), tests/real_call/conftest.py
Added:    tests/unit/test_config_consistency.py,
          tests/unit/test_relevance_judge_determinism.py,
          tests/unit/test_agent_malformed_response_retry.py,
          tests/real_call/test_relevance_judge_real.py,
          eval/promptfoo/{promptfooconfig.yaml,llmxive_provider.py,
          assert_review_frontmatter.py},
          .github/workflows/prompt-eval.yml,
          specs/021-project-audit-remediation/
```

## Design decisions

1. **Verdict cache keyed by content hash of the system prompt**
   (`JUDGE_PROMPT_VERSION`): editing the rubric changes every key, so
   stale verdicts are never addressed again — no TTL/invalidation
   machinery needed (vs the librarian result cache, which carries
   explicit TTLs because sources go stale; frozen judgments must not).
2. **Retry-with-feedback lives in `Agent.run`, not in a new client
   wrapper**: every non-speckit agent inherits it with zero per-agent
   code; the router keeps owning backend policy. `MalformedResponseError`
   is the single opt-in signal, so non-validation failures retain
   fail-fast behavior.
3. **promptfoo provider routes through `chat_with_fallback`** rather
   than promptfoo's `openai:` provider so evals run under production
   serving semantics (free-model guard, breakers, peer fallback), and so
   the same config works offline via `LLMXIVE_EVAL_BACKEND=local`.
4. **`docs/` untouched**: the Pages workflow regenerates it wholesale
   from `web/` on merge to main (`rm -rf docs; cp -R web docs`).
