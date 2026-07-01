# Reproduce & validate: SWE-Explore: Benchmarking How Coding Agents Explore Repositories

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/   (clone of https://github.com/Qiushao-E/SWE-Explore-Bench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** SWE-Explore: Benchmarking How Coding Agents Explore Repositories

**Abstract:** Repository-level coding benchmarks such as SWE-bench have driven a rapid surge in the capabilities of coding agents. Yet they usually treat coding tasks as a holistic, binary prediction problem (e.g., resolved or unresolved), neglecting fine-grained agent capabilities such as repository understanding, context retrieval, code localization, and bug diagnosis. In this paper, we introduce SWE-Explore, a benchmark that isolates the evaluation of repository exploration, a critical capability of coding agents. Given a repository and an issue, SWE-Explore asks an explorer to return a ranked list of relevant code regions under a fixed line budget. SWE-Explore covers 848 issues across 10 programming languages and 203 open-source repositories. For each instance, we derive line-level ground truth from independent agent trajectories that successfully solved the same issue, distilling the specific code regions their solution paths actually consulted. We evaluate exploration along coverage, ranking, and context-efficiency dimensions, showing that these metrics strongly track downstream repair behavior. Across a broad set of retrieval methods, general coding agents, and specialized localizers, we find that agentic explorers form a clear tier above classical retrieval. While file-level localization is already strong for modern methods, line-level coverage and efficient ranking remain the key axes differentiating state-of-the-art explorers.

## Shipped code — file tree (`projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/`)

```
.env.example
.gitignore
.gitmodules
.python-version
LICENSE
README.md
bench_build.py
build_commit_map.py
configs/litellm_proxy.yaml
eval.py
eval_runner.py
explorers/__init__.py
explorers/_locagent_shim.py
explorers/_paths.py
explorers/autocr_explorer.py
explorers/awe_agent_explorer.py
explorers/base.py
explorers/baselines.py
explorers/bm25.py
explorers/chunking.py
explorers/claude_code.py
explorers/cosil_explorer.py
explorers/cursor_agent.py
explorers/locagent_explorer.py
explorers/mini_swe_agent_explorer.py
explorers/orcaloca_explorer.py
explorers/parsing.py
explorers/rag.py
explorers/rag_embed.py
explorers/rag_potion.py
explorers/rag_tfidf.py
explorers/subprocess_utils.py
explorers/swerank.py
explorers/utils/environment.py
fetch_repos.py
figures/comparison.png
figures/framework.png
figures/instance.png
figures/main-results.png
figures/motivation.png
figures/overview.png
line_refine.py
main.py
models/__init__.py
models/azure_openai_client.py
models/base.py
models/default_agent.py
models/openai_client.py
models/openrouter_client.py
models/ref_to_langchain.py
pyproject.toml
quality/__init__.py
quality/analyze.py
quality/bench_metrics.py
quality/build_context.py
quality/configs/mini_swe_agent.yaml
quality/gen_patches.py
quality/gen_patches_agent.py
quality/models/__init__.py
quality/run_mini_swe_agent.py
quality/run_swebench.py
quality/run_swebench_pro.py
quality/stats.py
quality/tests/test_patch_diagnostics.py
quality/tests/test_run_mini_swe_agent_config.py
quality/tools/__init__.py
quality/tools/submit_patch.py
quality/tools/think.py
repos.txt
run_line_refine_call.py
stats.py
traj_datasets/README.md
traj_datasets/__init__.py
traj_datasets/coderforge_loader.py
traj_datasets/existing_adapter.py
traj_datasets/models.py
traj_datasets/nebius_loader.py
traj_datasets/scaleswe_distilled_loader.py
traj_datasets/scaleswe_loader.py
traj_datasets/swe_agent_loader.py
uv.lock
```

## Detected entry points

- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/main.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/eval.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/bench_build.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/build_commit_map.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/eval_runner.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/fetch_repos.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/line_refine.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/run_line_refine_call.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/stats.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/explorers/autocr_explorer.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/explorers/awe_agent_explorer.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/explorers/base.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/explorers/baselines.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/explorers/bm25.py`
- `projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/external/SWE-Explore-Bench/explorers/chunking.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `SWE-Explore-Bench` — not re-implementing it.
