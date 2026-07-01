# Reproduce & validate: Toward Generalist Autonomous Research via Hypothesis-Tree Refinement

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/   (clone of https://github.com/RUC-NLPIR/Arbor)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Toward Generalist Autonomous Research via Hypothesis-Tree Refinement

**Abstract:** Scientific progress depends on a repeated loop of exploration, experimentation, and abstraction. Researchers test candidate directions, interpret the evidence, and carry the resulting lessons into later attempts. We study how an AI agent can run this loop autonomously over long horizons. We introduce Arbor, a general framework for autonomous research that combines a long-lived coordinator, short-lived executors, and Hypothesis Tree Refinement (HTR), a persistent tree that links hypotheses, artifacts, evidence, and distilled insights across time. The coordinator manages global research strategy over the tree, while executors implement and test individual hypotheses in isolated worktrees. As results return, Arbor updates the tree, propagates reusable lessons, refines the search frontier, and admits verified improvements. This design turns autonomous research from a sequence of local attempts into a cumulative process in which strategy, execution, and evidence are carried across time. We evaluate Arbor under Autonomous Optimization (AO), an operational setting where an agent improves an initial research artifact through iterative experimentation without step-level human supervision. Across six real research tasks in model training, harness engineering, and data synthesis, Arbor achieves the best held-out result on all six tasks, attaining more than 2.5x the average relative held-out gain of Codex and Claude Code under the same task interface and resource budget. On MLE-Bench Lite, Arbor reaches 86.36% Any Medal with GPT-5.5, the strongest result in our comparison.

## Shipped code — file tree (`projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/`)

```
.claude-plugin/marketplace.json
.claude-plugin/plugin.json
.github/ISSUE_TEMPLATE/bug_report.yml
.github/ISSUE_TEMPLATE/config.yml
.github/ISSUE_TEMPLATE/feature_request.yml
.github/pull_request_template.md
.github/release.yml
.github/workflows/ci.yml
.github/workflows/pages.yml
.github/workflows/publish.yml
.gitignore
CONTRIBUTING.md
LICENSE
README.md
README.zh-CN.md
RELEASING.md
arbor-tree-demo.html
arbor-zoo/README.md
arbor-zoo/_template/PROVENANCE.md
arbor-zoo/_template/README.md
arbor-zoo/_template/data/.gitkeep
arbor-zoo/_template/eval.py
arbor-zoo/_template/eval.sh
arbor-zoo/_template/requirements.txt
arbor-zoo/_template/solution.py
arbor-zoo/_template/task.py
arbor-zoo/algotune_knn/PROVENANCE.md
arbor-zoo/algotune_knn/README.md
arbor-zoo/algotune_knn/eval.py
arbor-zoo/algotune_knn/eval.sh
arbor-zoo/algotune_knn/requirements.txt
arbor-zoo/algotune_knn/solution.py
arbor-zoo/algotune_knn/task.py
assets/arbor_paper.pdf
assets/arbor_teaser.pdf
assets/demo-poster.png
assets/demo.mp4
assets/framework.png
assets/hero.svg
assets/logo.png
assets/logo_black.png
assets/logo_white.png
docs/assets/logo.png
docs/assets/logo_black.png
docs/cli.md
docs/cli.zh.md
docs/configuration.md
docs/configuration.zh.md
docs/contributing.md
docs/contributing.zh.md
docs/dev/benchmark-add.md
docs/dev/benchmark-backlog.md
docs/dev/quicker-start.md
docs/dev/trajectory-export.md
docs/how-it-works.md
docs/how-it-works.zh.md
docs/index.md
docs/index.zh.md
docs/installation.md
docs/installation.zh.md
docs/interaction-modes.md
docs/interaction-modes.zh.md
docs/outputs-and-resume.md
docs/outputs-and-resume.zh.md
docs/plugins.md
docs/plugins.zh.md
docs/preparing-a-benchmark.md
docs/preparing-a-benchmark.zh.md
docs/quickstart.md
docs/quickstart.zh.md
docs/roadmap.md
docs/roadmap.zh.md
docs/search.md
docs/search.zh.md
docs/self-evolution.md
docs/skills.md
docs/skills.zh.md
docs/web-ui.md
docs/web-ui.zh.md
docs/zoo-overview.md
docs/zoo-overview.zh.md
docs/zoo.md
docs/zoo.zh.md
examples/algotune_knn/.gitignore
examples/algotune_knn/README.md
examples/algotune_knn/eval.py
examples/algotune_knn/eval.sh
examples/algotune_knn/requirements.txt
examples/algotune_knn/research_config.yaml
examples/algotune_knn/solution.py
examples/algotune_knn/task.py
examples/dashboard_demo.py
examples/full_demo.py
examples/kaggle_config.example.yaml
examples/research_config.example.yaml
examples/subscribe_demo.py
mkdocs.yml
project_page/.gitignore
project_page/README.md
project_page/index.html
project_page/package-lock.json
project_page/package.json
project_page/public/assets/demo/browsecomp/dashboard.html
project_page/public/assets/demo/browsecomp/idea_tree.html
project_page/public/assets/demo/dashboard.html
project_page/public/assets/demo/demo.mp4
project_page/public/assets/images/arbor-logo.png
project_page/public/assets/images/arbor-mark.png
project_page/public/assets/images/arbor-wordmark.png
project_page/public/assets/images/fig-case-study.png
project_page/public/assets/images/fig-framework.png
project_page/public/assets/images/fig-overview.png
project_page/public/assets/paper/arbor.pdf
project_page/src/App.jsx
project_page/src/bits/Magnet.jsx
project_page/src/bits/RotatingText.css
project_page/src/bits/RotatingText.jsx
project_page/src/bits/SpotlightCard.css
project_page/src/bits/SpotlightCard.jsx
project_page/src/bits/Threads.css
project_page/src/bits/Threads.jsx
project_page/src/components/Counter.jsx
project_page/src/components/ErrorBoundary.jsx
project_page/src/components/IdeaTree.jsx
project_page/src/components/Intro.jsx
project_page/src/components/Reveal.jsx
project_page/src/components/icons.jsx
project_page/src/components/useReducedMotion.js
project_page/src/i18n.jsx
project_page/src/main.jsx
project_page/src/sections/CaseStudy.jsx
project_page/src/sections/Demo.jsx
project_page/src/sections/Footer.jsx
project_page/src/sections/Header.jsx
project_page/src/sections/Hero.jsx
project_page/src/sections/Method.jsx
project_page/src/sections/Problem.jsx
project_page/src/sections/ProofStrip.jsx
project_page/src/sections/Resources.jsx
project_page/src/sections/Results.jsx
project_page/src/sections/WhyItMatters.jsx
project_page/src/styles/theme.css
project_page/vite.config.js
pyproject.toml
scripts/generate_demo_recording.py
skills/README.md
skills/__init__.py
skills/arbor-agent-coordinator/SKILL.md
skills/arbor-agent-coordinator/agents/openai.yaml
skills/arbor-agent-executor/SKILL.md
skills/arbor-agent-executor/agents/openai.yaml
skills/arbor-agent-ideate/SKILL.md
skills/arbor-agent-ideate/agents/openai.yaml
skills/arbor-agent-merge-eval/SKILL.md
skills/arbor-agent-merge-eval/agents/openai.yaml
skills/arbor-agent-orchestrator/SKILL.md
skills/arbor-agent-orchestrator/agents/openai.yaml
skills/arbor-agent-orchestrator/references/compatibility.md
skills/arbor-agent-orchestrator/references/source-map.md
skills/arbor-agent-plugins-hitl-budget/SKILL.md
skills/arbor-agent-plugins-hitl-budget/agents/openai.yaml
skills/arbor-agent-resume-report/SKILL.md
skills/arbor-agent-resume-report/agents/openai.yaml
skills/arbor-agent-search/SKILL.md
skills/arbor-agent-search/agents/openai.yaml
skills/arbor-agent-setup-intake/SKILL.md
skills/arbor-agent-setup-intake/agents/openai.yaml
skills/arbor-agent-tools/SKILL.md
skills/arbor-agent-tools/agents/openai.yaml
skills/arbor-agent-tools/references/tool-mapping.md
skills/arbor-agent-tools/scripts/arbor_state.py
skills/arbor-research-agent/SKILL.md
skills/arbor-research-agent/agents/openai.yaml
src/__init__.py
src/_app.py
src/cli/__init__.py
src/cli/_autodetect.py
src/cli/_constants.py
src/cli/app.py
src/cli/assets/demo_session/events.jsonl
src/cli/assets/demo_session/tree.json
src/cli/assets/tree_template.html
src/cli/branch_guard.py
src/cli/chart.py
src/cli/commands/__init__.py
src/cli/commands/benchmark_cmd.py
src/cli/commands/config_cmd.py
src/cli/commands/doctor_cmd.py
src/cli/commands/export_cmd.py
src/cli/commands/idea_check_cmd.py
src/cli/commands/install_cmd.py
src/cli/commands/login_cmd.py
src/cli/commands/mcp_cmd.py
src/cli/commands/replay_cmd.py
src/cli/commands/report_cmd.py
src/cli/commands/run.py
src/cli/commands/setup_cmd.py
src/cli/commands/web_cmd.py
src/cli/companion.py
src/cli/i18n.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/src/coordinator/main.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/src/executor/main.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/src/search_agent/main.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/src/run.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/src/cli/commands/run.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/arbor-zoo/_template/eval.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/arbor-zoo/algotune_knn/eval.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/examples/algotune_knn/eval.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/examples/dashboard_demo.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/examples/full_demo.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/examples/subscribe_demo.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/scripts/generate_demo_recording.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/src/dashboard.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/src/distill.py`
- `projects/PROJ-698-toward-generalist-autonomous-research-vi/external/Arbor/src/experience.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Arbor` — not re-implementing it.
