<!--
SYNC IMPACT REPORT
==================
Version change: (uninitialized template) → 1.0.0
Rationale: Initial ratification of the llmXive constitution. MAJOR bump from
template-only state (no prior numbered version) to first formally adopted
governance document.

Modified principles:
  - [PRINCIPLE_1_NAME] → I. Single Source of Truth (NON-NEGOTIABLE)
  - [PRINCIPLE_2_NAME] → II. Verified Accuracy (NON-NEGOTIABLE)
  - [PRINCIPLE_3_NAME] → III. Robustness & Reliability (Real-World Testing)
  - [PRINCIPLE_4_NAME] → IV. Cost Effectiveness (Free-First)
  - [PRINCIPLE_5_NAME] → V. Fail Fast

Added sections:
  - Additional Constraints & Operational Standards
  - Development Workflow & Quality Gates
  - Governance (concrete rules in place of placeholder)

Removed sections:
  - None (template placeholders replaced in place).

Templates requiring updates:
  - ✅ .specify/templates/plan-template.md   (Constitution Check section
       references this file generically; no edit needed — gates are sourced
       from this constitution at plan time)
  - ✅ .specify/templates/spec-template.md   (No principle conflicts; mandatory
       sections remain compatible)
  - ✅ .specify/templates/tasks-template.md  (Phases & gating compatible;
       real-call testing principle reinforced via existing test categories)
  - ✅ .specify/templates/checklist-template.md (Generic; no edit needed)
  - ⚠ pending: README.md "Development Guidelines" section may benefit from a
       cross-link to this constitution; not required for ratification.

Follow-up TODOs:
  - None. Ratification date is set to today since this is the initial adoption.
-->

# llmXive Constitution

## Core Principles

### I. Single Source of Truth (NON-NEGOTIABLE)

Every function, resource, configuration value, prompt template, schema, and
documented fact MUST exist in exactly ONE canonical location and be referenced
(imported, included, or linked) from every other site that needs it. Duplicate
implementations, copy-pasted helper functions, parallel JSON/YAML configs, and
forked prompt templates are prohibited.

Before adding any new function, file, or resource, the contributor MUST search
the repository for existing equivalents. When an equivalent is found, one of
three actions MUST be taken:

1. **Modify in place** if the existing implementation has a bug or missing
   capability — update the canonical version and verify all callers still work.
2. **Delete** if the implementation is no longer used by any part of the
   project — confirm zero references via grep, then remove the code, its tests,
   and any documentation that mentions it.
3. **Split and refactor** if the function legitimately needs multiple variants —
   extract the shared logic into a single helper, have each variant call the
   shared helper, and refactor every existing caller to use the new structure.

**Rationale**: Duplicated logic is the dominant source of long-term defects in
research codebases. With LLM-driven generation, the temptation to "just write a
new helper" is high; this principle forces deliberate consolidation so the
project remains tractable as it grows.

### II. Verified Accuracy (NON-NEGOTIABLE)

Every user-facing claim, every external reference (papers, URLs, datasets, API
documentation, model identifiers, statistics), and every assertion in
generated research output MUST be verified DIRECTLY and MANUALLY against
primary sources before being committed. Acceptable verification means:

- Web fetching the cited URL and reading the actual content (not summarizing
  from memory or training data).
- Downloading cited PDFs and confirming the quoted passage exists verbatim.
- Running an API call against the documented provider and confirming the
  response shape matches what the code or docs claim.
- For numeric facts (dates, version numbers, benchmark results), comparing
  against the primary source and recording the source URL alongside the claim.

If a claim cannot be verified, the contributor MUST either remove it or mark
it explicitly as `[UNVERIFIED]` with a reason. "I think I remember this" is
not verification. Plausible-sounding citations are not citations.

**Rationale**: An automated scientific-discovery platform that publishes
hallucinated references or fabricated facts is worse than no platform at all.
The credibility of every output depends on this principle being upheld
without exception.

### III. Robustness & Reliability (Real-World Testing)

All core functions MUST be exercised by tests that perform REAL operations in
the environments the code will run in. Mock objects, stubbed network layers,
fake filesystems, and synthetic-only test fixtures are prohibited as the
primary verification path for core functionality. Specifically:

- LLM provider integrations MUST include tests that issue real API calls to at
  least one supported provider and assert the response shape.
- File and dataset download paths MUST be tested by performing actual
  downloads against the real source.
- Code-execution and pipeline stages MUST be tested by running the actual
  generated code end-to-end against real inputs.
- Database, filesystem, and IO behavior MUST be tested by writing and reading
  real entries on real storage (a temp directory or test database is
  acceptable; an in-memory mock is not).
- UI / web interface behavior MUST be visually verified (screenshot or
  rendered-PNG comparison) before release.

Mock-based tests MAY be added as a secondary, fast-feedback layer ONLY AFTER
a real-call test has demonstrated correctness, and they MUST use the same
calling syntax as the real path so divergence is caught.

**Rationale**: This project orchestrates external models, downloads, code
execution, and figure generation. Mock-only tests routinely pass while the
real pipeline is broken. Real-call tests are the only honest signal that the
system works.

### IV. Cost Effectiveness (Free-First)

When choosing services, dependencies, models, hosting, storage, or tooling,
the project MUST prefer free or open-source options over paid ones whenever a
free option is technically viable. Concretely:

- Prefer free LLM tiers, open-weight models, and self-hosted inference where
  quality permits, over paid API tiers.
- Prefer GitHub Pages, GitHub Actions free minutes, and public free hosting
  over paid PaaS for the web interface and CI.
- Prefer permissive open-source libraries over commercial SDKs.
- Cache aggressively to avoid repeated paid calls when paid services are
  unavoidable.

A paid service MAY be adopted only when (a) no free alternative meets the
documented technical requirement, AND (b) the additional cost is justified
in writing in the relevant plan or PR description, AND (c) the dependency on
the paid service is encapsulated so it can be swapped if a free option later
becomes viable.

**Rationale**: This is a research project, not a funded product. Cost
discipline keeps the platform accessible to contributors and ensures the
system can run sustainably without ongoing budget approvals.

### V. Fail Fast

Every entry point — pipeline stage, CLI command, API call, code-generation
run, paper-build job — MUST validate its critical preconditions BEFORE
performing any expensive, slow, or costly operation. Failures MUST surface
within seconds, not after a multi-minute compute or API spend.

Mandatory fail-fast checks include:

- Required environment variables and API keys present and non-empty.
- Required CLI tools (e.g., `pdflatex`, `git`, language runtimes) installed
  and on PATH.
- Required input files exist, are readable, and parse correctly.
- Network reachability for required hosts when an operation depends on them.
- Disk space, write permissions, and output-directory existence.
- Schema validation of configuration before any data-mutating step runs.

Validation MUST raise a clear, actionable exception or exit non-zero with a
message identifying which precondition failed and how to fix it. Silent
fallbacks, retry-forever loops, and "best-effort" continuation past a failed
precondition are prohibited.

**Rationale**: Long-running scientific pipelines that fail late waste hours
of compute and API spend. Up-front validation is cheap; late failure is
expensive. This principle protects both the user's time and the project's
budget.

## Additional Constraints & Operational Standards

The following operational standards apply to all work in this repository:

- **Repository hygiene**: After taking screenshots, debugging dumps, or
  one-off scripts, contributors MUST either delete them or move them to a
  durable location (e.g., `scripts/` or a project-specific folder). The repo
  root MUST NOT accumulate transient artifacts.
- **Secrets**: Files containing API keys, tokens, passwords, or personal
  information MUST be added to `.gitignore` BEFORE any change is committed.
  All commits MUST be inspected for inadvertent secret inclusion prior to
  push.
- **Documentation parity**: When code in tests, examples, or public APIs
  changes, the corresponding documentation (READMEs, docstrings, web docs)
  MUST be updated in the same commit or PR.
- **Dependency tracking**: When new pip or npm packages are introduced, the
  appropriate manifest (`requirements.txt`, `package.json`) MUST be updated
  in the same change.
- **Project structure**: Each research project MUST follow the standardized
  directory layout (`idea/`, `technical-design/`, `implementation-plan/`,
  `code/`, `data/`, `paper/`, `reviews/`) and carry a `.llmxive/config.json`
  with the canonical metadata.
- **Identifiers**: Each project MUST have a unique `PROJ-###-descriptive-name`
  identifier used consistently across `papers/`, `code/`, `data/`,
  `technical_design_documents/`, `implementation_plans/`, and `reviews/`.

## Development Workflow & Quality Gates

The following gates apply to every change before it can be merged or
released:

- **Constitution Check (planning)**: Every implementation plan generated by
  `/speckit-plan` MUST include a Constitution Check section that explicitly
  evaluates the design against Principles I–V. Violations MUST be either
  resolved or recorded in a Complexity Tracking table with explicit
  justification.
- **Pre-push verification**: Before pushing to GitHub, contributors MUST run
  the full verification suite — tests, linters, documentation builds, and
  any project-specific validation scripts. If any fix changes code, the
  ENTIRE suite MUST be re-run; partial re-verification is not acceptable.
- **Real-call test discipline**: When tests fail repeatedly, contributors
  MUST NOT simplify or weaken the tests. The required response is to
  (a) record the problem in notes, (b) commit and push current state to
  preserve work, and (c) fix the underlying CODE so the original tests pass.
- **Frequent commits**: While debugging or developing, contributors MUST
  commit and push at meaningful checkpoints so work is recoverable if
  context is lost.
- **Reference validation**: Before any paper or user-facing document is
  considered complete, every cited reference MUST be downloaded and reviewed
  per Principle II.
- **Review thresholds**: Status advancement (Backlog → Ready → In Progress
  → Done) follows the point-based review system documented in the project
  README; LLM reviews count 0.5 points and human reviews count 1 point. The
  documented minimums MUST be met before transition.

## Governance

This constitution supersedes ad-hoc practices, individual preferences, and
prior conventions. When this document conflicts with other guidance, this
document wins, EXCEPT that explicit user instructions in `CLAUDE.md`,
`AGENTS.md`, or direct user requests override the constitution per the
project's instruction-priority policy.

**Amendment procedure**:

1. Proposed amendments MUST be opened as a PR that modifies this file and
   updates the version line per the semantic-versioning rules below.
2. The PR description MUST include a Sync Impact Report enumerating affected
   templates, docs, and downstream artifacts, and MUST mark each as updated
   or pending.
3. Amendments take effect when merged into `main`. The `LAST_AMENDED_DATE`
   MUST be updated to the merge date.

**Versioning policy** (semantic versioning of the constitution itself):

- **MAJOR**: Backward-incompatible governance changes, principle removals,
  or principle redefinitions that invalidate prior compliance claims.
- **MINOR**: Addition of a new principle or section, or material expansion
  of existing guidance.
- **PATCH**: Clarifications, wording fixes, typo corrections, and
  non-semantic refinements.

**Compliance review**: Every PR review and every plan-to-implementation
gate MUST verify that the change complies with Principles I–V. Reviewers
MUST cite the specific principle when requesting changes for compliance
reasons. Unjustified violations block merge.

**Runtime guidance**: For day-to-day development guidance not covered
here, contributors should consult the project `README.md` and the
repository-level `CLAUDE.md`.

**Version**: 1.0.0 | **Ratified**: 2026-04-28 | **Last Amended**: 2026-04-28
