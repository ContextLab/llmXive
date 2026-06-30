# Reproduce & validate: AutoResearchClaw: Self-Reinforcing Autonomous Research with Human-AI Collaboration

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/   (clone of https://github.com/aiming-lab/AutoResearchClaw)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** AutoResearchClaw: Self-Reinforcing Autonomous Research with Human-AI Collaboration

**Abstract:** Automating scientific discovery requires more than generating papers from ideas. Real research is iterative: hypotheses are challenged from multiple perspectives, experiments fail and inform the next attempt, and lessons accumulate across cycles. Existing autonomous research systems often model this process as a linear pipeline: they rely on single-agent reasoning, stop when execution fails, and do not carry experience across runs. We present AutoResearchClaw, a multi-agent autonomous research pipeline built on five mechanisms: structured multi-agent debate for hypothesis generation and result analysis, a self-healing executor with a \textsc{Pivot}/\textsc{Refine} decision loop that transforms failures into information, verifiable result reporting that prevents fabricated numbers and hallucinated citations, human-in-the-loop collaboration with seven intervention modes spanning full autonomy to step-by-step oversight, and cross-run evolution that converts past mistakes into future safeguards. On ARC-Bench, a 25-topic experiment-stage benchmark, AutoResearchClaw outperforms AI Scientist v2 by 54.7%. A human-in-the-loop ablation across seven intervention modes reveals that precise, targeted collaboration at high-leverage decision points consistently outperforms both full autonomy and exhaustive step-by-step oversight. We position AutoResearchClaw as a research amplifier that augments rather than replaces human scientific judgment. Code is available at https://github.com/aiming-lab/AutoResearchClaw.

## Shipped code — file tree (`projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/`)

```
.claude/skills/a-evolve/SKILL.md
.claude/skills/biology-biopython/SKILL.md
.claude/skills/chemistry-rdkit/SKILL.md
.claude/skills/hypothesis-formulation/SKILL.md
.claude/skills/literature-search/SKILL.md
.claude/skills/researchclaw/SKILL.md
.claude/skills/scientific-visualization/SKILL.md
.claude/skills/scientific-writing/SKILL.md
.claude/skills/statistical-reporting/SKILL.md
.gitignore
CONTRIBUTING.md
LICENSE
README.md
RESEARCHCLAW_AGENTS.md
RESEARCHCLAW_CLAUDE.md
config.researchclaw.example.yaml
docs/CHANGELOG_ANTHROPIC_ADAPTER.md
docs/DOMAIN_INTEGRATION_GUIDE.md
docs/HITL_GUIDE.md
docs/README_AR.md
docs/README_CN.md
docs/README_DE.md
docs/README_ES.md
docs/README_FR.md
docs/README_JA.md
docs/README_KO.md
docs/README_PT.md
docs/README_RU.md
docs/TESTER_GUIDE.md
docs/TESTER_GUIDE_CN.md
docs/TESTER_GUIDE_JA.md
docs/integration-guide.md
docs/showcase/SHOWCASE.md
docs/showcase/papers/paper_III_sir_seir_identifiability.pdf
docs/showcase/papers/paper_II_weak_iv_estimators.pdf
docs/showcase/papers/paper_IV_krylov_preconditioners.pdf
docs/showcase/papers/paper_I_random_matrix.pdf
docs/showcase/papers/paper_VIII_craft_distillation.pdf
docs/showcase/papers/paper_VII_fame_token_merging.pdf
docs/showcase/papers/paper_VI_lace_exploration.pdf
docs/showcase/papers/paper_V_gard_lora.pdf
docs/showcase/thumbnails/framework_III_sir_seir_identifiability.png
docs/showcase/thumbnails/framework_II_weak_iv_estimators.png
docs/showcase/thumbnails/framework_IV_krylov_preconditioners.png
docs/showcase/thumbnails/framework_I_random_matrix.png
docs/showcase/thumbnails/framework_VIII_craft_distillation.png
docs/showcase/thumbnails/framework_VII_fame_token_merging.png
docs/showcase/thumbnails/framework_VI_lace_exploration.png
docs/showcase/thumbnails/framework_V_gard_lora.png
docs/showcase/thumbnails/paper_III_sir_seir_identifiability-01.png
docs/showcase/thumbnails/paper_II_weak_iv_estimators-01.png
docs/showcase/thumbnails/paper_IV_krylov_preconditioners-01.png
docs/showcase/thumbnails/paper_I_random_matrix-01.png
docs/showcase/thumbnails/paper_VIII_craft_distillation-01.png
docs/showcase/thumbnails/paper_VII_fame_token_merging-01.png
docs/showcase/thumbnails/paper_VI_lace_exploration-01.png
docs/showcase/thumbnails/paper_V_gard_lora-01.png
experiments/arc_bench/EXPERIMENT_DESIGN.md
experiments/arc_bench/README.md
experiments/arc_bench/RUN_GUIDE.md
experiments/arc_bench/baseline/README.md
experiments/arc_bench/baseline/adapters/__init__.py
experiments/arc_bench/baseline/adapters/_aide_runner.py
experiments/arc_bench/baseline/adapters/agent_lab_adapter.py
experiments/arc_bench/baseline/adapters/ai_scientist_v2_adapter.py
experiments/arc_bench/baseline/adapters/aide_adapter.py
experiments/arc_bench/baseline/adapters/base.py
experiments/arc_bench/baseline/adapters/researchclaw_adapter.py
experiments/arc_bench/baseline/interventions/T01.json
experiments/arc_bench/baseline/interventions/T02.json
experiments/arc_bench/baseline/interventions/T03.json
experiments/arc_bench/baseline/interventions/T04.json
experiments/arc_bench/baseline/interventions/T05.json
experiments/arc_bench/baseline/interventions/T06.json
experiments/arc_bench/baseline/interventions/T07.json
experiments/arc_bench/baseline/interventions/T08.json
experiments/arc_bench/baseline/interventions/T09.json
experiments/arc_bench/baseline/interventions/T10.json
experiments/arc_bench/baseline/interventions/T11.json
experiments/arc_bench/baseline/interventions/T12.json
experiments/arc_bench/baseline/interventions/T13.json
experiments/arc_bench/baseline/interventions/T14.json
experiments/arc_bench/baseline/interventions/T15.json
experiments/arc_bench/baseline/interventions/T16.json
experiments/arc_bench/baseline/interventions/T17.json
experiments/arc_bench/baseline/interventions/T18.json
experiments/arc_bench/baseline/interventions/T19.json
experiments/arc_bench/baseline/interventions/T20.json
experiments/arc_bench/baseline/interventions/T21.json
experiments/arc_bench/baseline/interventions/T22.json
experiments/arc_bench/baseline/interventions/T23.json
experiments/arc_bench/baseline/interventions/T24.json
experiments/arc_bench/baseline/interventions/T25.json
experiments/arc_bench/config/_meta_paper_quality.json
experiments/arc_bench/config/base_config.yaml
experiments/arc_bench/config/biology/manifests/B01.yaml
experiments/arc_bench/config/biology/manifests/B02.yaml
experiments/arc_bench/config/biology/manifests/B03.yaml
experiments/arc_bench/config/biology/manifests/B04.yaml
experiments/arc_bench/config/biology/manifests/B05.yaml
experiments/arc_bench/config/biology/manifests/B06.yaml
experiments/arc_bench/config/biology/manifests/B07.yaml
experiments/arc_bench/config/biology/rubrics/B01.json
experiments/arc_bench/config/biology/rubrics/B02.json
experiments/arc_bench/config/biology/rubrics/B03.json
experiments/arc_bench/config/biology/rubrics/B04.json
experiments/arc_bench/config/biology/rubrics/B05.json
experiments/arc_bench/config/biology/rubrics/B06.json
experiments/arc_bench/config/biology/rubrics/B07.json
experiments/arc_bench/config/biology/topics.yaml
experiments/arc_bench/config/credentials.example.env
experiments/arc_bench/config/credentials_loader.py
experiments/arc_bench/config/ml/manifests/ML01.yaml
experiments/arc_bench/config/ml/manifests/ML02.yaml
experiments/arc_bench/config/ml/manifests/ML03.yaml
experiments/arc_bench/config/ml/manifests/ML04.yaml
experiments/arc_bench/config/ml/manifests/ML05.yaml
experiments/arc_bench/config/ml/manifests/ML06.yaml
experiments/arc_bench/config/ml/manifests/ML07.yaml
experiments/arc_bench/config/ml/manifests/ML08.yaml
experiments/arc_bench/config/ml/manifests/ML09.yaml
experiments/arc_bench/config/ml/manifests/ML10.yaml
experiments/arc_bench/config/ml/manifests/ML11.yaml
experiments/arc_bench/config/ml/manifests/ML12.yaml
experiments/arc_bench/config/ml/manifests/ML13.yaml
experiments/arc_bench/config/ml/manifests/ML14.yaml
experiments/arc_bench/config/ml/manifests/ML15.yaml
experiments/arc_bench/config/ml/manifests/ML16.yaml
experiments/arc_bench/config/ml/manifests/ML17.yaml
experiments/arc_bench/config/ml/manifests/ML18.yaml
experiments/arc_bench/config/ml/manifests/ML19.yaml
experiments/arc_bench/config/ml/manifests/ML20.yaml
experiments/arc_bench/config/ml/manifests/ML21.yaml
experiments/arc_bench/config/ml/manifests/ML22.yaml
experiments/arc_bench/config/ml/manifests/ML23.yaml
experiments/arc_bench/config/ml/manifests/ML24.yaml
experiments/arc_bench/config/ml/manifests/ML25.yaml
experiments/arc_bench/config/ml/rubrics/ML01.json
experiments/arc_bench/config/ml/rubrics/ML02.json
experiments/arc_bench/config/ml/rubrics/ML03.json
experiments/arc_bench/config/ml/rubrics/ML04.json
experiments/arc_bench/config/ml/rubrics/ML05.json
experiments/arc_bench/config/ml/rubrics/ML06.json
experiments/arc_bench/config/ml/rubrics/ML07.json
experiments/arc_bench/config/ml/rubrics/ML08.json
experiments/arc_bench/config/ml/rubrics/ML09.json
experiments/arc_bench/config/ml/rubrics/ML10.json
experiments/arc_bench/config/ml/rubrics/ML11.json
experiments/arc_bench/config/ml/rubrics/ML12.json
experiments/arc_bench/config/ml/rubrics/ML13.json
experiments/arc_bench/config/ml/rubrics/ML14.json
experiments/arc_bench/config/ml/rubrics/ML15.json
experiments/arc_bench/config/ml/rubrics/ML16.json
experiments/arc_bench/config/ml/rubrics/ML17.json
experiments/arc_bench/config/ml/rubrics/ML18.json
experiments/arc_bench/config/ml/rubrics/ML19.json
experiments/arc_bench/config/ml/rubrics/ML20.json
experiments/arc_bench/config/ml/rubrics/ML21.json
experiments/arc_bench/config/ml/rubrics/ML22.json
experiments/arc_bench/config/ml/rubrics/ML23.json
experiments/arc_bench/config/ml/rubrics/ML24.json
experiments/arc_bench/config/ml/rubrics/ML25.json
experiments/arc_bench/config/ml/topics.yaml
experiments/arc_bench/config/physics/manifests/P01.yaml
experiments/arc_bench/config/physics/manifests/P02.yaml
experiments/arc_bench/config/physics/manifests/P03.yaml
experiments/arc_bench/config/physics/manifests/P04.yaml
experiments/arc_bench/config/physics/manifests/P05.yaml
experiments/arc_bench/config/physics/manifests/P06.yaml
experiments/arc_bench/config/physics/manifests/P07.yaml
experiments/arc_bench/config/physics/manifests/P08.yaml
experiments/arc_bench/config/physics/manifests/P09.yaml
experiments/arc_bench/config/physics/manifests/P10.yaml
experiments/arc_bench/config/physics/rubrics/P01.json
experiments/arc_bench/config/physics/rubrics/P02.json
experiments/arc_bench/config/physics/rubrics/P03.json
experiments/arc_bench/config/physics/rubrics/P04.json
experiments/arc_bench/config/physics/rubrics/P05.json
experiments/arc_bench/config/physics/rubrics/P06.json
experiments/arc_bench/config/physics/rubrics/P07.json
experiments/arc_bench/config/physics/rubrics/P08.json
experiments/arc_bench/config/physics/rubrics/P09.json
experiments/arc_bench/config/physics/rubrics/P10.json
experiments/arc_bench/config/physics/topics.yaml
experiments/arc_bench/config/quantum/README.md
experiments/arc_bench/config/quantum/manifests/Q01.yaml
experiments/arc_bench/config/quantum/manifests/Q02.yaml
experiments/arc_bench/config/quantum/manifests/Q03.yaml
experiments/arc_bench/config/quantum/manifests/Q04.yaml
experiments/arc_bench/config/quantum/manifests/Q05.yaml
experiments/arc_bench/config/quantum/manifests/Q06.yaml
experiments/arc_bench/config/quantum/manifests/Q07.yaml
experiments/arc_bench/config/quantum/manifests/Q08.yaml
experiments/arc_bench/config/quantum/manifests/Q09.yaml
experiments/arc_bench/config/quantum/manifests/Q10.yaml
experiments/arc_bench/config/quantum/rubrics/Q01.json
experiments/arc_bench/config/quantum/rubrics/Q02.json
experiments/arc_bench/config/quantum/rubrics/Q03.json
experiments/arc_bench/config/quantum/rubrics/Q04.json
experiments/arc_bench/config/quantum/rubrics/Q05.json
… (truncated)
```

## Detected entry points

- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/experiments/arc_bench/scripts/evaluate.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/adapters.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/cli.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/config.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/evolution.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/evolution_aevolve.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/hardware.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/health.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/quality.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/report.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/researchclaw/writing_guide.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/scripts/plot_iteration_showcase.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/scripts/test_beast_mode_e2e.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/scripts/test_code_agent_live.py`
- `projects/PROJ-608-autoresearchclaw-self-reinforcing-autono/external/AutoResearchClaw/scripts/test_code_agent_sandbox.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `AutoResearchClaw` — not re-implementing it.
