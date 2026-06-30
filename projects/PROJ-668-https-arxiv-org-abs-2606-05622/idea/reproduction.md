# Reproduce & validate: AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Agents under World and User Constraints

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/   (clone of https://github.com/JiayuJeff/AdaPlanBench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Agents under World and User Constraints

**Abstract:** Planning for real-world problems by language models often involves both world and user constraints, which may not be fully specified upfront and are progressively disclosed through interaction. However, existing benchmarks still underexplore adaptive planning under such progressively revealed dual constraints. To address this gap, we introduce AdaPlanBench, a dynamic interactive benchmark for evaluating whether Large Language Model (LLM) agents can adaptively plan and re-plan under progressively revealed world and user constraints. AdaPlanBench is built on 307 household tasks, with a scalable constraint construction pipeline that augments each task with dual constraints. At runtime, agents interact with the environment in a multi-turn protocol where hidden constraints are revealed only when the agent proposes a plan that violates them, requiring iterative plan revision under accumulating feedback. This makes planning challenging, as agents must infer and track constraints from feedback while re-planning effectively. Experiments on ten leading LLMs show that adaptive planning under dual constraints remains challenging, with the best model reaching only 67.75% accuracy. We further observe that performance degrades as more constraints accumulate, with user constraints posing a particularly large challenge and failures often stemming from weaker physical grounding and reduced effectiveness. These results establish AdaPlanBench as a testbed for dual-constrained interactive planning and highlight the challenge of reliable adaptation to dynamically revealed constraints in LLM agents.

## Shipped code — file tree (`projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/`)

```
.gitignore
README.md
domain_metadata/housing/final/query_housing_macgyver_resample.json
env/.env.example
env/__init__.py
env/construction/__init__.py
env/construction/cons_utils/__init__.py
env/construction/cons_utils/constraint_check.py
env/construction/cons_utils/dedupe.py
env/construction/cons_utils/reasoning.py
env/construction/prompts.py
env/eval_main_table.py
env/run.py
env/run_config.yaml
env/run_utils/__init__.py
env/run_utils/dataworker.py
env/run_utils/judgers/BaseJudger.py
env/run_utils/judgers/HousingJudger.py
env/run_utils/judgers/__init__.py
env/run_utils/llm.py
env/run_utils/model_metadata.yaml.example
env/run_utils/run_merge.py
env/run_utils/run_prompts.py
env/run_utils/run_scripts/run_deepseek-v3.2.sh
env/run_utils/run_scripts/run_deepseek-v4-flash.sh
env/run_utils/run_scripts/run_gemini-3-flash.sh
env/run_utils/run_scripts/run_gemini-3.1-pro.sh
env/run_utils/run_scripts/run_gpt-5-mini.sh
env/run_utils/run_scripts/run_gpt-5-nano.sh
env/run_utils/run_scripts/run_gpt-5.2.sh
env/run_utils/run_scripts/run_gpt-5.sh
env/run_utils/run_scripts/run_llama3-3-70b.sh
env/run_utils/run_scripts/run_minimax-m2.5.sh
env/run_utils/run_scripts/run_qwen3-14b.sh
env/run_utils/run_scripts/run_qwen3-32b.sh
env/run_utils/run_scripts/run_qwen3-8b.sh
env/run_utils/run_scripts/run_temp_analysis_suite.sh
env/run_utils/run_scripts/run_temp_ban_only_suite.sh
env/run_utils/run_scripts/run_temp_refine_rubrics_suite.sh
env/run_utils/run_scripts/run_temp_tabulation_suite.sh
env/run_utils/runner.py
env/run_utils/timer.py
env/run_utils/token_count.py
env/run_utils/tracker.py
figures/accuracy_valid_plan_rate_iterationbar.pdf
figures/main_table.png
figures/pipeline_1.pdf
figures/pipeline_1.png
```

## Detected entry points

- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/eval_main_table.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/construction/prompts.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run_utils/dataworker.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run_utils/llm.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run_utils/run_merge.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run_utils/run_prompts.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run_utils/runner.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run_utils/timer.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run_utils/token_count.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run_utils/tracker.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/construction/cons_utils/constraint_check.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/construction/cons_utils/dedupe.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/construction/cons_utils/reasoning.py`
- `projects/PROJ-668-https-arxiv-org-abs-2606-05622/external/AdaPlanBench/env/run_utils/judgers/BaseJudger.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `AdaPlanBench` — not re-implementing it.
