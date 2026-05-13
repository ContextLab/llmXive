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

Paper review needs both a points threshold and an accept verdict from **twelve**
specialist reviewers: writing quality, logical consistency, claim accuracy,
over-reach, safety/ethics, scientific evidence, statistical analysis, code
quality, data quality, text formatting, figure critic, jargon police.

Human reviews count double; self-review is rejected by the schema.

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
