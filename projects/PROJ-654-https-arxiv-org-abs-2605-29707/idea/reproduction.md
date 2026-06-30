# Reproduce & validate: Domino: Decoupling Causal Modeling from Autoregressive Drafting in Speculative Decoding

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-654-https-arxiv-org-abs-2605-29707/external/Domino/   (clone of https://github.com/jianuo-huang/Domino)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Domino: Decoupling Causal Modeling from Autoregressive Drafting in Speculative Decoding

**Abstract:** Speculative decoding accelerates LLM inference by drafting multiple tokens and verifying them in parallel with the target model. However, its practical speedup is constrained by the trade-off between draft quality and drafting cost: autoregressive drafters model causal dependencies among draft tokens but incur sequential overhead, while parallel drafters reduce drafting cost but weaken intra-block dependency modeling. In this paper, we propose Domino, a speculative decoding framework that decouples causal dependency modeling from expensive autoregressive draft execution. Domino first uses a parallel draft backbone to produce preliminary draft distributions for the entire block, and then applies a lightweight Domino head to refine them with prefix-dependent causal information. To stabilize teacher-forced causal encoding, we further introduce a base-anchored training curriculum that first strengthens the parallel backbone and then gradually shifts optimization toward the causally corrected final distribution. Experiments on Qwen3 models show that Domino achieves up to \(5.49\times\) end-to-end speedup under the Transformers backend and up to \(5.8\times\) throughput speedup under SGLang serving.

## Shipped code — file tree (`projects/PROJ-654-https-arxiv-org-abs-2605-29707/external/Domino/`)

```
.gitignore
README.md
asset/DFlash_demo.gif
asset/DFlash_demo.mp4
asset/overhead.pdf
asset/pipeline.pdf
asset/pipeline.png
asset/speedup.pdf
code/benchmark.py
code/benchmark_sglang.py
code/benchmark_sglang_tasks.py
code/dflash.py
code/distributed.py
code/kernel/__init__.py
code/kernel/domino.py
code/model/__init__.py
code/model/utils.py
requirements-hf.txt
run_hf_benchmark.sh
run_sglang_benchmark.sh
```

## Detected entry points

- `projects/PROJ-654-https-arxiv-org-abs-2605-29707/external/Domino/code/benchmark.py`
- `projects/PROJ-654-https-arxiv-org-abs-2605-29707/external/Domino/code/benchmark_sglang.py`
- `projects/PROJ-654-https-arxiv-org-abs-2605-29707/external/Domino/code/benchmark_sglang_tasks.py`
- `projects/PROJ-654-https-arxiv-org-abs-2605-29707/external/Domino/code/dflash.py`
- `projects/PROJ-654-https-arxiv-org-abs-2605-29707/external/Domino/code/distributed.py`
- `projects/PROJ-654-https-arxiv-org-abs-2605-29707/external/Domino/code/kernel/domino.py`
- `projects/PROJ-654-https-arxiv-org-abs-2605-29707/external/Domino/code/model/utils.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Domino` — not re-implementing it.
