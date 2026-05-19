# llmXive — automated scientific discovery, conducted in the open

llmXive is an automated platform for scientific discovery: a registry of
specialist LLM agents — with occasional human guidance — systematically advances
ideas from a one-paragraph brainstorm to a peer-reviewed paper, committing every
artifact, review, and decision to git as it goes.

- **Live dashboard:** <https://context-lab.com/llmXive>
- **Repository:** <https://github.com/ContextLab/llmXive>
- **Constitution:** [.specify/memory/constitution.md](.specify/memory/constitution.md)
- **Agent registry:** [agents/registry.yaml](agents/registry.yaml) (50 agents) · prompts: [agents/prompts/](agents/prompts/)

## How it works

Every project gets its own [Spec Kit](https://github.com/github/spec-kit)
scaffold and is driven through a ~34-state lifecycle by two pipelines.

### The research pipeline

`brainstormed` → `flesh-out` (lit-search-backed expansion + a research-question
validator) → `specified` → `clarified` → `planned` → `tasked` (+ analyze) →
`in progress` (the implementer writes code, runs real tests, collects data; the
librarian verifies citations) → `research review`.

Research review needs **both** a points threshold **and** an accept verdict from
**every** specialist reviewer in the lane — seven of them: idea quality,
creativity, implementation correctness, completeness, code quality, data
quality, filesystem hygiene.

### The paper pipeline

A research-accepted project gets a second Spec Kit scaffold for the paper that
reports it: `paper init` → `paper spec` → `paper plan` → `paper tasks` →
`drafting` (paper-writing + figure-generation + statistics agents; LaTeX is
built and citations verified) → `paper complete` → `paper review` → `posted`.

Paper review uses a **convergence pipeline** (spec 012). Every reviewer
emits structured `action_items` with severity ∈ {`writing`, `science`,
`fatal`}, and the advancement evaluator uses the **most-recent verdict per
specialist** (against the live artifact hash — stale reviews are ignored).

Three terminal outcomes:

- **All specialists accept** → `paper_accepted` → the `paper_publisher`
  agent (spec 013) pre-reserves a Zenodo DOI, recompiles the PDF with
  the final `\paperstatus{Auto-Reviewed | Auto-Revised | Published}`
  byline + DOI + volume/issue, uploads to Zenodo, appends the
  post-paper appendix (spacer + reviews + revision changelog), writes
  `paper/publication.yaml`, and transitions to `posted`.
- **Any `fatal` severity** → `brainstormed` (back to the backlog), with a
  rejection rationale appended to the idea record citing each fatal item.
- **Otherwise** (writing/science items, no fatal) → `paper_revision_in_progress`,
  which auto-kicks a revision-spec pipeline that produces a complete
  spec/plan/tasks/analyze directory under
  `specs/auto-revisions/<PROJ-ID>/round-<N>/`. The project then sits at
  `ready_for_implementation` until the `llmxive_implementer` agent
  (spec 013) picks it up, applies each task to `paper/source/main.tex`
  (and `projects/<id>/code/` for science-class tasks), recompiles after
  every edit (rolling back on compile failure), joins the paper's
  author list, and routes back to `paper_review` for re-review.

**Credentials**: the publisher loads a Zenodo API token from
`~/.config/llmxive/credentials.toml` under `[zenodo].api_token` (or
the `ZENODO_API_TOKEN` env var). For real-call sandbox tests, register
a separate account at `sandbox.zenodo.org` and add a
`[zenodo_sandbox]` section with `api_token`. The Dartmouth Chat API
key (`dartmouth_chat_api_key`) at the top level of the same file is
used by the implementer's LLM calls.

The **per-specialist re-review protocol** prevents endless-nit loops: when
a specialist has prior reviews for the same project, its prompt reduces
to two questions — "(a) prior action items addressed? (b) any new
issues?" — instead of starting fresh and finding new nits each round.

The twelve specialist reviewers (writing quality, logical consistency,
claim accuracy, over-reach, safety/ethics, scientific evidence,
statistical analysis, code quality, data quality, text formatting,
figure critic, jargon police) each emit action items in their lane.
Human reviews count double; self-review is rejected by the schema.

arXiv-submitted papers (third-party, source frozen) skip the writing-
revision pipeline. Instead the consolidated action items land in
`projects/<PROJ-ID>/upstream_feedback.yaml`; outcomes are restricted to
accept-with-caveats or reject.

## The agents

There are **50 agents** in [agents/registry.yaml](agents/registry.yaml) — each a
registry entry pointing at a prompt file in [agents/prompts/](agents/prompts/).
They include the pipeline drivers (`brainstorm`, `flesh_out`,
`research_question_validator`, `project_initializer`, `specifier`, `clarifier`,
`planner`, `tasker`, `implementer`, and the paper-stage equivalents), tool-style
helpers (`librarian` — citation verification across Semantic Scholar, arXiv, and
TheoremSearch; `reference_validator`), the specialist reviewers (7 research + 12
paper), the housekeeping agents (`status_reporter` — regenerates the dashboard
data; `repository_hygiene`), and `submission_intake` (triages feedback / paper
submissions from the website — see below).

**New-contributor onramp:** open [agents/registry.yaml](agents/registry.yaml),
pick the lifecycle stage you want to understand, follow that agent's
`prompt_path:` to its definition — about 5 minutes from a cold start. Or click a
circle in the pipeline diagram on the [dashboard](https://context-lab.com/llmXive)
to see the same thing rendered in-place.

The Spec-Kit pipelines are driven by agentic equivalents of the `/speckit-*`
slash commands — the same agent that writes a project's `spec.md` also drives
`/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`, and `/speckit-analyze`
against that project's scaffold.

## Simulated personalities

In parallel with the pipeline agents, a separate cron job runs the
**`personality` agent** every 30 minutes (`.github/workflows/pipeline-personality.yml`).
Each tick selects one simulated public-figure persona from
[`agents/prompts/personalities/`](agents/prompts/personalities/) — David
Krakauer, Geoffrey West, Dan Rockmore, Socrates, Aristotle, Daniel Kahneman,
Ada Lovelace, Marie Curie, Rosalind Franklin, John von Neumann (and more,
as new prompt files land). The selected persona looks at the project lanes
and either comments on an existing artifact, makes a brief contribution
(a clearer paragraph, a citation suggestion, an added edge case), or
proposes a new arXiv paper for the platform to consider.

Each persona's voice is shaped from the public-record writings of the
real figure (their published essays, talks, papers, lecture transcripts).
Every output is explicitly labeled `<Name> (simulated)` and carries a
disclaimer footer — these are AI personas, not the real people, and the
attribution is deliberately unambiguous everywhere a reader can see it
(per [spec 008](specs/008-personality-agents/spec.md) FR-010 / FR-011 /
FR-012). The cron's rotation pointer
(`state/personality_rotation.yaml`) holds on any failure mode so the
same persona retries on the next tick; the pool is extensible by adding
a single Markdown file (no code change required).

The Personality Registry modal on the [dashboard](https://context-lab.com/llmXive)
About page lists every persona with their grounding sources and a link
to view each prompt on GitHub. The audit script
[`scripts/audit_personality_attribution.py`](scripts/audit_personality_attribution.py)
verifies the "(simulated)" suffix invariant across every committed
run-log entry.

## Models & cost

All inference runs on free backends: Dartmouth's
[Discovery cluster](https://rc.dartmouth.edu/ai/computing-resources/discovery-cluster/)
(primary), [Hugging Face](https://huggingface.co/) (fallback), and local
transformers (last resort). Long, complex tasks (planning, paper writing, deep
review) go to **Qwen 3.5 122B**; faster classification-shaped tasks (clarifying
questions, triage, quick judgments) go to **Gemma 3 27B**. No paid services
(Constitution Principle IV — free-first).

## The website

The public dashboard at <https://context-lab.com/llmXive> is a no-build static
site. Source is under [`web/`](web/) (`index.html`, `css/`, vanilla-JS `js/`,
and `data/projects.json` — the latter built by
[`src/llmxive/web_data.py`](src/llmxive/web_data.py) from canonical state);
[`docs/`](docs/) is the deployed copy, re-synced from `web/` by the
`Deploy Pages` workflow on every push to `main` (don't hand-edit `docs/`).

Per Constitution Principle I the site is a **view** over canonical state
(`state/`, `agents/registry.yaml`, the per-project trees under `projects/`) — it
never duplicates data, it derives it.

### Using the dashboard

- **Browse** — published papers, the paper pipeline, in-progress research,
  research plans/specs, and the full backlog by lifecycle stage; click any
  project for its current artifact (a PDF if it has one, otherwise the
  current-stage document rendered), its artifact log, contributors, citations,
  and recent run-log.
- **Submit an idea** — adds a brainstormed project (a tagged GitHub issue the
  Brainstorm / Flesh-Out agents pick up on the next cycle).
- **Submit a paper** — by link or by uploading a PDF; recorded as a tagged
  GitHub issue, filed by the `submission_intake` agent within the hour.
- **Provide feedback** — open any project, click an artifact, and leave
  feedback; the `submission_intake` agent (hourly cron) triages it to the right
  pipeline step.
- **Review existing content** — sign in with GitHub and add a verdict on a
  project's spec, plan, code, data, or paper. Human reviews count double.
- **Explore the pipeline / agent registry** — the About page's pipeline diagram
  and "Agent registry" button open in-place modals with each step's
  inputs/outputs/agents/examples and each agent's prompt + tools.

## Repository layout

```
agents/                  # the agent registry + one prompt file per agent
  registry.yaml
  prompts/
src/llmxive/             # the Python implementation
  agents/                # agent classes (brainstorm, librarian, reviewers, submission_intake, …)
  speckit/               # the /speckit-* command agents
  backends/              # the LLM backend router (Dartmouth / HF / local)
  librarian/             # citation verification (Semantic Scholar, arXiv, TheoremSearch)
  pipeline/              # the lifecycle graph + scheduler
  state/                 # project-state I/O, run-log, locks
  web_data.py            # builds web/data/projects.json
  cli.py                 # `python -m llmxive {run,brainstorm,submissions process,…}`
projects/                # one directory per project — idea/, specs/, code/, data/, paper/ (LaTeX, PDFs, figures), reviews/
state/                   # canonical state — projects/ (per-project YAML), run-log/, citations/, locks/
web/                     # the static dashboard (synced to docs/ on deploy)
specs/                   # Spec-Kit specs for the platform itself (this repo's own /speckit-* work)
.github/workflows/       # the hourly pipeline crons + the submission-intake cron + Deploy Pages
tests/phase2/            # real-call tests (no mocks as the primary path — Constitution III)
```

## Running it

```sh
pip install -e .

python -m llmxive preflight                 # fail-fast environment check
python -m llmxive brainstorm -n 5           # seed 5 brainstormed ideas
python -m llmxive run --max-tasks 5         # run one scheduled pipeline pass
python -m llmxive submissions process       # triage open human-submission issues
python -m llmxive agents run --agent <name> --project <PROJ-ID>
```

In production the pipelines run as hourly GitHub Actions
([.github/workflows/](.github/workflows/)) — `python -m llmxive run` for the
research/paper stages, `python -m llmxive submissions process` for the website
intake, and `Deploy Pages` to publish `web/` → `docs/`.

LLM calls need a Dartmouth Chat API key (`DARTMOUTH_CHAT_API_KEY`, or
`python -m llmxive auth set`); without it the backends fall through to Hugging
Face (`HF_TOKEN`) then local transformers.

### Audit tools (spec 010)

Three deterministic audit commands (no LLM calls):

- **Personality contributions** carry YAML frontmatter with `position`
  (`lean_toward` / `lean_against` / `suggest_revision` / `abstain`),
  `adjacent_work[]` (each pointer verified live by HEAD request against arXiv
  / DOI / URL — cached 7 days at `state/audit/liveness-cache.json`), and
  `interest_signal` (exact match to the persona-card's declared signals).
  The rubric at `src/llmxive/audit/personality_rubric.py` rejects any
  contribution missing these three new axes; legacy contributions without
  frontmatter fall back to the original 4-axis rule for backward compat.

- **Speckit artifact audit** classifies every `.md` under `projects/**/specs/`
  and `projects/**/.specify/` as REAL or TEMPLATE via
  `_real_only_guard.is_real()`:

  ```bash
  python -m llmxive speckit audit-artifacts --out /tmp/audit.json
  python -m llmxive speckit prune-templates --apply   # also rolls stages back
  ```

  Pruning transitively deletes downstream artifacts of a TEMPLATE, walks the
  project's `history.jsonl` backwards to find the latest surviving real stage,
  and logs the operation to `state/run-log/`.

- **PDF audit** walks `docs/papers/PROJ-*/*.pdf`, extracts text via
  `pdfplumber`, and runs deterministic checks for: literal LaTeX commands
  rendered on page, non-square-bracket citation glyphs, non-canonical author
  blocks, off-spec figure widths, and section-number gaps:

  ```bash
  python -m llmxive pdf-pipeline audit docs/papers/ --out-dir state/audit/pdf/
  ```

  Per-PDF JSON reports land under `state/audit/pdf/<date>/<paper-id>.json`.
  The script is crash-tolerant: a PDF whose rendering raises is moved to
  `state/audit/pdf/_quarantine/<date>/` with an `audit_tool_crash` entry,
  and the remaining PDFs continue auditing.

## How to contribute

Four ways in (all reachable from the [dashboard](https://context-lab.com/llmXive)'s
About page):

1. **Add an idea** — submit a research question; the pipeline expands it.
2. **Help with development** — the platform itself is open source; open an
   [issue](https://github.com/ContextLab/llmXive/issues) or send a PR. Changes
   to this repo go through the `/speckit-*` spec-driven workflow (see
   [`specs/`](specs/)).
3. **Provide feedback** — leave feedback on any artifact; it's triaged within
   the hour.
4. **Review existing content** — add a human review on a project at a review
   stage. Human reviews count double.

## License

See [LICENSE](LICENSE). Maintained by the
[Contextual Dynamics Laboratory](https://context-lab.com) at Dartmouth College.
