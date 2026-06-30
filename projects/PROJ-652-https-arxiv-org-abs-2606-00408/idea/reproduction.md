# Reproduce & validate: Masking Stale Observations Helps Search Agents -- Until It Doesn't: A Regime Map and Its Mechanism

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/   (clone of https://github.com/i-DeepSearch/observation-masking)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Masking Stale Observations Helps Search Agents -- Until It Doesn't: A Regime Map and Its Mechanism

**Abstract:** Long-horizon search agents accumulate large amounts of retrieved content across many tool calls, making context-budget efficiency increasingly important. A minimal intervention is to mask stale observations from the context as the trajectory progresses, but it remains unclear when this form of context management helps and why. We study observation masking through a systematic sweep over various agent backbones (4B to 284B parameters) and three retrievers on offline and live-web agentic search benchmarks. We find that the accuracy gain from masking follows an asymmetric inverted-U shape when plotted against the model's accuracy without context management: a plateau under weak retrievers, a peak when a strong retriever meets a mid-capacity model, and a sharp collapse when the model is saturated. This pattern reflects the interaction between retriever recall and the model's implicit filtering capacity, rather than either factor in isolation. Mechanistically, masking implements a token-for-turn trade-off: it removes observations the model has largely stopped attending to and pages the agent rarely re-opens. The added turns help when they convert failures into successes, but they fail when masking removes evidence the model would otherwise have used. We therefore reframe context management as a regime-dependent intervention and provide a holistic perspective for analyzing context use in agentic deep search. We release our scaffold and trajectories here (https://github.com/i-DeepSearch/observation-masking) to support future research.

## Shipped code — file tree (`projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/`)

```
.env.template
.gitignore
README.md
agents/__init__.py
agents/deepseek_agent.py
agents/gptoss_agent.py
assets/docs/benchmarks.md
assets/docs/deployment.md
assets/docs/parameter.md
assets/fig/attn_map2.png
assets/fig/main-table.png
assets/fig/open-cursor.png
assets/fig/scaffold.png
assets/fig/snr_auc.png
assets/fig/teaser.gif
assets/fig/teaser.png
assets/logos/claude.png
assets/logos/deepseek.png
assets/logos/gpt.png
assets/logos/log.svg
assets/logos/nvidia.png
assets/logos/or-logo1.png
assets/logos/patrick.png
assets/logos/tamu.svg
assets/logos/tongyi.png
assets/logos/ucb.png
assets/logos/ucsd.svg
assets/logos/uiuc.png
assets/logos/vllm-color.png
deploy_agent.py
eval/__init__.py
eval/eval_analysis.py
eval/eval_recall.py
eval.py
pyproject.toml
run_agent.sh
scripts/cache_env.sh
scripts/deploy_search_service.py
scripts/deploy_vllm_service.py
scripts/start_deepseek_flash.sh
scripts/start_gptoss_servers.sh
scripts/start_nemotron_servers.sh
scripts/start_qwen_servers.sh
scripts/start_search_service.sh
scripts/stop_servers.sh
setup.sh
tools/__init__.py
tools/backend.py
tools/browser.py
tools/context_management.py
utils/__init__.py
utils/data_setup.py
utils/data_utils.py
utils/eval_parsers.py
utils/openai_generator.py
utils/prompts.py
utils/tool_parsers.py
utils/vllm_generator.py
```

## Detected entry points

- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/eval.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/deploy_agent.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/agents/deepseek_agent.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/agents/gptoss_agent.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/eval/eval_analysis.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/eval/eval_recall.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/scripts/deploy_search_service.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/scripts/deploy_vllm_service.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/tools/backend.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/tools/browser.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/tools/context_management.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/utils/data_setup.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/utils/data_utils.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/utils/eval_parsers.py`
- `projects/PROJ-652-https-arxiv-org-abs-2606-00408/external/observation-masking/utils/openai_generator.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `observation-masking` — not re-implementing it.
