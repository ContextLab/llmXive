# Reproduce & validate: EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic Environments

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/   (clone of https://github.com/Aiden0526/EvoArena)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** EvoArena: Tracking Memory Evolution for Robust LLM Agents in Dynamic Environments

**Abstract:** Large language model (LLM) agents have achieved strong performance on a wide range of benchmarks, yet most evaluations assume static environments. In contrast, real-world deployment is inherently dynamic, requiring agents to continually align their knowledge, skills, and behavior with changing environments and updated task conditions. To address this gap, we introduce EvoArena, a benchmark suite that models environment changes as sequences of progressive updates across terminal, software, and social domains. We further propose EvoMem, a patch-based memory paradigm that records memory evolution as structured update histories, enabling agents to reason about environmental evolution through changes in their memory. Experiments show that current agents struggle on EvoArena, achieving an average accuracy of 39.6% across evolving terminal, software, and social-preference domains. EvoMem consistently improves performance, yielding an average gain of 1.5% on EvoArena and also improving standard benchmarks such as GAIA and LoCoMo by 6.1% and 4.8%. Beyond individual tasks, EvoMem further improves chain-level accuracy by 3.7% on EvoArena, where success requires completing a consecutive sequence of related evolutionary subtasks. Mechanistic analysis shows that EvoMem improves evidence capture in the memory, indicating better preservation of complete evolving environment states. Our results highlight the importance of modeling evolution in both evaluation and memory for reliable agent deployment.

## Shipped code — file tree (`projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/`)

```
.gitignore
EvoMem-PersonaMem-Evo/.env.example
EvoMem-PersonaMem-Evo/.gitignore
EvoMem-PersonaMem-Evo/LICENSE
EvoMem-PersonaMem-Evo/README.md
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260316_065208_persona0.json
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260316_065208_persona1.json
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260316_065208_persona10.json
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260316_065208_persona11.json
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260316_065208_persona20.json
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260316_065208_persona21.json
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260316_065208_persona40.json
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260321_062008_persona18.json
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260321_062008_persona30.json
EvoMem-PersonaMem-Evo/data/chat_history_32k/chat_history_260321_062008_persona41.json
EvoMem-PersonaMem-Evo/data/personamem-evo-10p.csv
EvoMem-PersonaMem-Evo/llm_text_parsers.py
EvoMem-PersonaMem-Evo/locomo_eval_utils.py
EvoMem-PersonaMem-Evo/memory_layer.py
EvoMem-PersonaMem-Evo/memory_layer_patch.py
EvoMem-PersonaMem-Evo/memory_layer_robust.py
EvoMem-PersonaMem-Evo/patch_prompts.py
EvoMem-PersonaMem-Evo/patch_store.py
EvoMem-PersonaMem-Evo/requirements.txt
EvoMem-PersonaMem-Evo/scripts/evaluate_persona_chain_acc.py
EvoMem-PersonaMem-Evo/scripts/run_persona_baseline_patch.sh
EvoMem-PersonaMem-Evo/test_persona_patch.py
EvoMem-PersonaMem-Evo/test_persona_robust.py
EvoMem-PersonaMem-Evo/test_persona_robust_logic.py
EvoMem-PersonaMem-Evo/utils.py
EvoMem-TerminalBench-Evo/.gitignore
EvoMem-TerminalBench-Evo/.gitmodules
EvoMem-TerminalBench-Evo/README.md
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/__init__.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/agents/__init__.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/agents/terminus2_baseline.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/agents/terminus2_evomem.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/agents/terminus2_git_capture.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/agents/terminus2_llm_sync.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/chain_id.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/family_trace_memory.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/memory/__init__.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/memory/summarizer.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/memory_bridge.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/patch_capture.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/pyproject.toml
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/_dispatch.sh
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/_ensure_terminus2_llm_env.sh
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/kill_runs.sh
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/launch_runs.sh
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/launch_terminus2_baseline.sh
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/launch_terminus2_evomem.sh
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/list_chains.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/run_chain.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/status.py
EvoMem-TerminalBench-Evo/harbor_EvoMem/scripts/terminus2_llm.env.example
README.md
assets/evoarena_dataset_composition.png
assets/evoarena_domain_double_pie.pdf
assets/evoarena_fig1.png
assets/evoarena_overview.png
assets/evoarena_step_chain_scatter.png
assets/evomem_framework.png
assets/persona-mem-example.png
assets/swe-evo.png
assets/terminal-bench.png
docs/index.html
docs/static/css/style.css
docs/static/images/evoarena_benchmark_overview.png
docs/static/images/evoarena_domain_stats.png
docs/static/images/evoarena_fig1.png
docs/static/images/evoarena_overall_performance.png
docs/static/images/evomem_architecture.png
docs/static/images/hf-logo.png
docs/static/images/persona-mem-example.png
docs/static/images/swe-evo.png
docs/static/images/terminal-bench.png
docs/static/images/token_efficiency_combined.png
docs/static/js/main.js
```

## Detected entry points

- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/llm_text_parsers.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/locomo_eval_utils.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/memory_layer.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/memory_layer_patch.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/memory_layer_robust.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/patch_prompts.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/patch_store.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/test_persona_patch.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/test_persona_robust.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/test_persona_robust_logic.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/utils.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-PersonaMem-Evo/scripts/evaluate_persona_chain_acc.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/chain_id.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/family_trace_memory.py`
- `projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/external/EvoArena/EvoMem-TerminalBench-Evo/harbor_EvoMem/harbor_EvoMem/memory_bridge.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `EvoArena` — not re-implementing it.
