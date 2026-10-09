# llmXive — automated scientific discovery, conducted in the open

llmXive is a research platform that develops ideas into executable studies,
reviews their evidence, and drafts papers for review and publication approval.
Specialist LLM agents work through project-specific specifications, plans and
tasks. Git records the artifacts, review decisions and recovery history.

- [Live dashboard](https://context-lab.com/llmXive)
- [Agent registry](agents/registry.yaml) and [prompts](agents/prompts/)
- [Constitution](.specify/memory/constitution.md)
- [Recovery audit and evidence](notes/audit-20261008/README.md)

## Current status — 2026-10-09

The recovery audit found failures in task scope, execution, artifact placement,
review protocols and evidence verification. Updating the model alone did not
resolve them. The implementation now includes fixes for those observed failures,
but **a fresh run through the entire authored-paper pipeline is not yet proven**.

An earlier isolated totient study autonomously reached `research_accepted` and
then `paper_tasked`. Independent checks agreed with all 12 residue-count tables,
24 total-variation rows and 1,000 small-integer identities; its report retained
the observed finite-range exception rather than claiming a general theorem.
A later paper-task failure routed that run to the wrong research stage, so it
was stopped and preserved. Its scientific artifacts and state were not manually
edited to obtain acceptance. See the [recorded evidence](notes/audit-20261008/canary-20261009-1250-evidence.json).

That result establishes useful research-stage progress, not an accepted paper
or recovery of the production backlog. A subsequent fresh full-pipeline run
remains the acceptance test. Reviewed external preprints, green CI, model probes
and successful individual repairs to the platform are distinct evidence.
Follow [#1139](https://github.com/ContextLab/llmXive/issues/1139) for current
throughput and full-pipeline results, and [#1242](https://github.com/ContextLab/llmXive/issues/1242)
for autonomous repair: **no accepted useful autonomous platform repair has yet
been demonstrated**.

## Lifecycle and architecture

The [lifecycle graph](src/llmxive/pipeline/graph.py) schedules agents from the
[registry](agents/registry.yaml), currently 54 entries. Each project owns its
[Spec Kit](https://github.com/github/spec-kit) scaffolds, research code, data,
paper, reviews and revision history. The registry and central
[backend router](src/llmxive/backends/router.py) define model behavior;
[state files](src/llmxive/state/) record progress. The dashboard derives its view
from these records.

| Phase | Main path | Required evidence |
| --- | --- | --- |
| Research design | Idea → expansion and question validation → specification → clarification → plan → tasks and analysis | A scoped, testable question; complete design artifacts; executable tasks; stage review |
| Research execution | `in_progress` → `research_complete` → `research_review` → `research_accepted` | Actual code/data outputs, current execution and test evidence, verified claims/references, and unanimous research-panel acceptance |
| Paper development | `paper_drafting_init` → paper specification, clarification, plan, tasks and analysis → `paper_in_progress` → `paper_complete` | A manuscript and figures grounded in the accepted research, runnable build instructions, and compiled output |
| Publication | `paper_review` → `paper_accepted` → `awaiting_publication_signoff` → `posted` | Current paper-panel acceptance, explicit maintainer approval, and successful publication |

The complete state vocabulary is defined in [types.py](src/llmxive/types.py).
Failures do not count as advancement: they retain diagnostics and either retry,
reopen the responsible task, or return the project to the appropriate design
stage. Paper task-format, planning and writing failures retain the paper track
instead of corrupting accepted research state; substantive scientific findings
can still require a return to research or the backlog. Successful analysis can
be reused only when its recorded artifacts and relevant review inputs still match.

### Review and scientific acceptance

Reviewable stages use one [convergence engine](src/llmxive/convergence/engine.py):
identify actionable concerns, revise against those concerns, then re-review the
same concern set. The configured round cap bounds a review attempt; it does not
guarantee acceptance. Unresolved substantive concerns cause a documented
kickback. Revision work lives under
`projects/<PROJ-ID>/.specify/auto-revisions/round-<N>/`; prior rounds and archives
retain provenance.

Research and paper review require unanimous panel acceptance with no open
concerns. Document-authoring stages may advance with writing-only residue;
requirement, methodology or scientific defects still block them. Human and
explicitly labeled simulated-personality comments inform the relevant reviewer
but do not directly substitute for a specialist verdict. Publication has a
separate mandatory human sign-off.

Independent task verification examines the actual referenced artifacts and their
canonical project paths. Execution evidence binds to the run-book, source and
output bytes; changed or missing evidence invalidates approval. Signed empirical
result receipts authenticate captured bytes and provenance, not scientific
correctness. Citation and claim checks, independent review and final execution
checks remain separate gates.

After paper acceptance, the publication workflow assembles the review trail and
requests maintainer approval through a GitHub issue or the publication CLI.
Maintainer rejection returns feedback to revision. Approved publication uses the
[Zenodo publisher](src/llmxive/agents/publisher.py) and records the DOI and
publication metadata. This is implemented behavior, not evidence that the
current fresh canary has completed publication.

### External papers and simulated contributors

Submitted or imported papers follow a separate `paper_ingested` →
`reviewed_preprint` path. The original scientific work is preserved, review
artifacts are attached, and a separate brainstormed project may explore a
follow-up question. Reviewing someone else's preprint is not completion of an
llmXive-authored study.

The [personality workflow](.github/workflows/pipeline-personality.yml) currently
runs every two hours. Its [persona prompts](agents/prompts/personalities/) draw
on public writings; contributions are labeled “(simulated)” and are advisory.
The [attribution audit](scripts/audit_personality_attribution.py) checks the
labeling invariant.

## Models and compute

Dartmouth Chat is the production model service. The central default and all
LLM-agent registry defaults use **GLM-5.3** (`zai-org.glm-5.3`). For transient
failures, the router tries free same-backend peers in order:
**GPT-OSS 120B** (`openai.gpt-oss-120b`), then **Gemma 4 31B**
(`google.gemma-4-31B-it`). Catalog availability and returned-model identity are
checked separately from configuration. A fallback response is recorded as that
model; primary-model acceptance tests do not let a peer impersonate the primary.

The router also supports backend fallback where configured. Local transformers
requires installed dependencies, suitable hardware and a compatible available
model; it is not a guarantee that a large Dartmouth model can run on a laptop.
Qwen remains a compatibility route for callers explicitly requesting it, not
the production default. Specialized vision, personality and manual utilities
still have explicit model choices; registry defaults do not describe every call.
Those remaining choices are tracked in [#1285](https://github.com/ContextLab/llmXive/issues/1285).

The existing paid Dartmouth fallback is off by default. It requires
`LLMXIVE_PAID_OPT_IN=1` and headroom under the
[credit-budget guard](src/llmxive/backends/credits.py); an unavailable or invalid
balance check refuses paid calls. The deployed
[advance workers](.github/workflows/advance.yml) explicitly enable that opt-in
with `LLMXIVE_PAID_BUDGET_FRACTION=0.9`, so production can use the guarded fallback
within Dartmouth's credit budget after free peers fail. This is separate from
the HF pilot. Included credits and endpoint availability are service/account
properties, not a promise of unlimited free inference.

Research designs should fit available compute. The existing
[Kaggle offload adapter](src/llmxive/execution/offload.py) can submit eligible
GPU-bound execution when configured with `KAGGLE_API_TOKEN`, then poll and collect
outputs. Missing credentials or unavailable capacity do not establish successful
execution. The optional HF pilot below is a separate, explicitly invoked path.

### Optional Hugging Face pilot

The `contextlab` Academia pilot has private versioned artifact storage and a
private working bucket in an `llmxive` resource group. **Jobs and Inference
Providers share one $20 monthly compute cap**; paid Spaces and Inference Endpoints
have $0 limits. This is a pooled allocation, not ten independent wallets or an
automatic production fallback. Provider enforcement can lag the cap.

The [pilot guide](scripts/hf/README.md) records successful private-file
upload/download verification, a bounded CPU computation and one alternate-model
call. A recovery-audit copy was also restored byte-for-byte with a pinned
[storage receipt](scripts/hf/pilot-storage-receipt.json). The working bucket's
data round trip remains untested. Automatic research-artifact migration and
production compute offloading remain future integration work.

The helper reads `HF_TOKEN` from a CI secret or the local macOS Keychain; it does
not read plaintext HF caches or repository `.env` files. The pilot currently uses
Keychain, with no recurring HF workflow or pilot HF CI secret enabled. Keep all
tokens out of Git, command arguments and logs. Use the explicit commands in the
pilot guide only when a bounded storage, compute or model experiment is needed.

## Execution boundaries and repository layout

Generated research runs in a project-specific Python environment with a
project-local working directory and runtime home. Its environment does not
inherit orchestrator credentials. Python and supported shell commands have time
limits and captured output; failed execution feeds the next correction attempt.
These [process safeguards](src/llmxive/sandbox.py) are not a complete hostile-code
filesystem sandbox: research jobs may access the network to obtain public data.
Run studies in disposable workers/checkouts with appropriate host permissions.

Implementation and planning writers check project boundaries and symlink escapes.
Planning refuses ambiguous file aliases before writing and restores prior bytes
when deterministic guards reject a revision. Implementation refuses new
case/Unicode-equivalent filename collisions.
Default scheduled commits permit project paths, `state/` and `web/data/`;
platform repairs use a separate reviewed path. The trusted Pages workflow selects
a distinct profile that stages only `docs/`.

```text
agents/                        Registry and prompts
src/llmxive/                    Pipeline, agents, backends, execution, review and repair
projects/<PROJ-ID>/
  idea/                        Research seed and expansion
  specs/                       Active research specification, plan, tasks and contracts
  code/, src/, scripts/        Project implementations (layout depends on the study)
  data/, figures/, results/    Project inputs and generated evidence
  paper/                       Paper scaffold, manuscript, figures and build outputs
  reviews/                     Review records and advisory feedback
  .specify/                    Project controls, revision rounds, caches and archives
state/                         Project state, run logs and verification records
specs/                         Platform-development specifications
web/                           Dashboard source and derived data
docs/                          Deployed dashboard mirror; do not hand-edit
scripts/hf/                    Explicit bounded HF pilot and receipts
eval/promptfoo/                 Repeated prompt-regression evaluations
tests/                         Unit, contract, integration and live checks
.github/workflows/             Scheduled work, checks, repair candidates and publication
```

The [root-file recovery audit](notes/audit-20261008/repository-hygiene.md)
preserved 2,666 misplaced files with their original Git bytes and modes. Known
owners received project-local recovered downloads; uncertain owners remain in
provenance-addressed recovery storage. Recovery does not validate a dataset for
scientific use. Remaining historical filename collisions are
[inventoried](notes/audit-20261008/case-collisions.md), including different
scientific files that must not be silently overwritten.

Run the fast tracked-layout check with:

```sh
python src/llmxive/checks/repository_layout.py
```

## Running the platform

Use Python 3.11 or newer in a dedicated environment. Paper builds require a TeX
toolchain; PDF audits require Poppler. Follow the relevant workflow's dependencies
for the operation you are running.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m llmxive auth set                 # optional interactive local Dartmouth setup
python -m llmxive preflight
python -m llmxive brainstorm -n 5
python -m llmxive run --project PROJ-ID --max-tasks 1
```

`PROJ-ID` is an existing project's full identifier. Omitting `--project` lets the
scheduler choose eligible work. These commands make real model calls and persist
project changes; use an isolated checkout for experiments. See
`python -m llmxive --help` for submission processing, direct agent invocation and
project operations. Maintainers can record a publication decision with:

```sh
python -m llmxive project publish-approve PROJ-ID \
  --who 'Maintainer Name' --what 'reviewed paper meets standards'
```

GitHub Actions supplies service credentials through repository secrets. For
Dartmouth, the CLI also supports a permission-checked local credential file via
`auth set`; HF pilot credentials follow the stricter Keychain/CI-only path above.
Research execution needs a persistent `LLMXIVE_RECEIPT_KEY` in the orchestrator
and workers verifying its results. The supported local credential field is
`llmxive_receipt_key` in `~/.config/llmxive/credentials.toml` with mode `0600`.
Changing the key invalidates old receipts. Keep signing keys outside the repository
and generated research subprocesses. Zenodo publication requires its own token;
sandbox publication tests use a separate sandbox token.

The [main pipeline](.github/workflows/llmxive-pipeline.yml) is scheduled every
three hours, with additional [advance workers](.github/workflows/advance.yml)
and stage-specific workflows. [Submission intake](.github/workflows/submission-intake.yml)
is hourly; [publication sign-off polling](.github/workflows/signoff-poll.yml)
is every two hours. Workflow files are the authoritative schedules. A successful
worker exit can mean no eligible progress; inspect stage transitions and artifacts.

## Platform self-repair

The [repair workflow](.github/workflows/repair.yml) collects concrete runtime
errors or actionable issues and proposes a bounded platform change. It requires
a regression that exercises an existing production caller and fails on the
baseline, passing candidate and related tests, fixed preservation tests, and
review by a different model. Invalid syntax, invented-helper import failures
and deletion of prior user content do not count as successful repairs.

Generated repair tests run in separate resource-limited Docker containers with
network disabled, no credentials or Docker socket, read-only inputs and temporary
working storage. The candidate cannot replace existing tests. A separate
publication job verifies the evidence digest and unchanged target-file baseline
before opening a reviewable PR; the candidate generator does not directly deploy
its own patch. See the [repair preservation evidence](notes/2026-10-09-repair-reproduction-preservation.md).

These safeguards have rejected bad candidates. They do not yet demonstrate an
accepted, useful autonomous repair. Follow [#1242](https://github.com/ContextLab/llmXive/issues/1242)
for actual candidate outcomes rather than treating a scheduled run as improvement.

## Tests and quality gates

```sh
pytest tests/contract
pytest tests/unit -m 'not slow'
pytest tests/integration
LLMXIVE_REAL_TESTS=1 pytest tests/real_call -m 'not slow and not external_references'
```

Live suites require the relevant credentials and services. The
[PR workflow](.github/workflows/llmxive-real-call-tests.yml) runs offline and
selected live jobs concurrently. Dartmouth checks cover the actual configured
primary and runtime behavior. External reference/dataset availability is checked
separately when changed dependencies warrant it; known documentation and
orchestration changes do not need unrelated registrar uptime. Unknown inputs
remain conservatively selected. The [selector and dependency guards](scripts/ci/select_checks.py)
keep this policy reviewable.

The [nightly suite](.github/workflows/llmxive-real-call-nightly.yml) retains slow
checks, free-peer coverage, external services and full-pipeline acceptance tests,
with failure artifacts preserved. [Prompt Eval](.github/workflows/prompt-eval.yml)
runs two reviewer fixtures three times, including rejection of a deliberately
flawed idea, using the configured primary and rejecting peer-model substitution.
Repository audits check layout, Spec Kit artifacts, PDFs, personality
attribution and feedback behavior. Sparse checkouts reduce data transfer while
preserving each audit's required input corpus.

Tests establish specific contracts. Full scientific acceptance additionally
requires an observed run through research execution, paper production and review,
with useful artifacts that survive independent inspection.

## Dashboard and contributions

The [dashboard](https://context-lab.com/llmXive) is a static view of canonical
project state, built by [web_data.py](src/llmxive/web_data.py). Edit `web/`;
[Deploy Pages](.github/workflows/pages.yml) regenerates and publishes `docs/`.
It displays authored projects separately from reviewed external preprints.

Use the dashboard to browse artifacts and review trails, submit an idea or paper,
and provide feedback. Contributions can also start with a
[GitHub issue](https://github.com/ContextLab/llmXive/issues) or a pull request.
For development, follow an entry in [agents/registry.yaml](agents/registry.yaml)
to its prompt and implementation; platform specifications live in [specs/](specs/).
Recurring failure evidence belongs in the existing tracking issue when possible.

## License

See [LICENSE](LICENSE). Maintained by the
[Contextual Dynamics Laboratory](https://context-lab.com) at Dartmouth College.
