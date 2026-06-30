# Reproduce & validate: Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnesses on Coding Tasks

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/   (clone of https://github.com/opensquilla/claw-swe-bench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnesses on Coding Tasks

**Abstract:** General-purpose agents such as OpenClaw are increasingly used as autonomous tool users, but their coding ability is difficult to measure under SWE-bench: a generic agent does not by itself satisfy the clean Docker workspace, patch, and prediction contract required for scoring. We introduce Claw-SWE-Bench, a multilingual SWE-bench-style benchmark and adapter protocol that makes heterogeneous agent harnesses, or claws, comparable under fair settings including a fixed prompt, runtime budget, workspace contract, patch extraction procedure, and evaluator. The full benchmark contains 350 GitHub issue-resolution instances across 8 languages and 43 repositories, drawn from SWE-bench-Multilingual and SWE-bench-Verified-Mini after future-commit cleanup. We also release Claw-SWE-Bench Lite for faster validation, which is an 80-instance subset selected by a cost-aware, rank-aware procedure over 17 calibration columns. On the full benchmark, OpenClaw with a minimal direct-diff adapter scores only $19.1\%$ Pass@1, whereas the full adapter reaches $73.4\%$ with the same GLM 5.1 backbone, showing that adapter design is essential for enabling OpenClaw-style harnesses to perform coding tasks effectively. Across an OpenClaw $\times$ nine-model sweep and a five-claw $\times$ two-model sweep, model choice changes Pass@1 by $29.4$ pp and harness choice by $27.4$ pp under fixed models; systems with similar accuracy can differ substantially in total API cost. Claw-SWE-Bench therefore treats harness and cost accounting as first-class axes of SWE-style coding-agent evaluation, providing both a full benchmark and a low-cost reference set for reproducible comparison. The data is available at https://github.com/opensquilla/claw-swe-bench and https://huggingface.co/datasets/TokenRhythm/Claw-SWE-Bench.

## Shipped code — file tree (`projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/`)

```
.gitignore
LICENSE
README.md
claw_configs/generic/mykey.py.example
claw_configs/hermes/config.yaml.example
claw_configs/nanobot/config.json.example
claw_configs/zeroclaw/config.toml.example
claw_configs/zeroclaw/tool_filter_proxy.py
claw_swebench/__init__.py
claw_swebench/claws/__init__.py
claw_swebench/claws/base.py
claw_swebench/claws/generic.py
claw_swebench/claws/hermes.py
claw_swebench/claws/nanobot.py
claw_swebench/claws/openclaw.py
claw_swebench/claws/zeroclaw.py
claw_swebench/config.py
claw_swebench/dataset.py
claw_swebench/evaluate.py
claw_swebench/orchestrator.py
claw_swebench/patch.py
claw_swebench/prediction.py
claw_swebench/prompt.py
claw_swebench/types.py
claw_swebench/workspace.py
config/multilingual.yaml
config/multilingual_300_instances.txt
config/verified.yaml
config/verified_mini_50.txt
prompts/default.txt
prompts/generic.txt
proxies/dashscope_cache_proxy.py
requirements.txt
run_eval.py
run_infer.py
```

## Detected entry points

- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/evaluate.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/run_eval.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/run_infer.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/config.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/dataset.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/orchestrator.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/patch.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/prediction.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/prompt.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/types.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/workspace.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/proxies/dashscope_cache_proxy.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_configs/zeroclaw/tool_filter_proxy.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/claws/base.py`
- `projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/external/claw-swe-bench/claw_swebench/claws/generic.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `claw-swe-bench` — not re-implementing it.
