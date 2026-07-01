# Reproduce & validate: AI for Auto-Research: Roadmap & User Guide

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-602-https-arxiv-org-abs-2605-18661/external/awesome-ai-auto-research/   (clone of https://github.com/worldbench/awesome-ai-auto-research)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** AI for Auto-Research: Roadmap & User Guide

**Abstract:** AI-assisted research is crossing a threshold: fully automated systems can now generate research papers for as little as $15, while long-horizon agents can execute experiments, draft manuscripts, and simulate critique with minimal human input. Yet this productivity frontier exposes a deeper integrity problem: under scientific pressure, even frontier LLMs still fabricate results, miss hidden errors, and fail to judge novelty reliably. Studying developments through April 2026, we present an end-to-end analysis of AI across the complete research lifecycle, organized into four epistemological phases: Creation (idea generation, literature review, coding & experiments, tables & figures), Writing (paper writing), Validation (peer review, rebuttal & revision), and Dissemination (posters, slides, videos, social media, project pages, and interactive agents). We identify a sharp, stage-dependent boundary between reliable assistance and unreliable autonomy: AI excels at structured, retrieval-grounded, and tool-mediated tasks, but remains fragile for genuinely novel ideas, research-level experiments, and scientific judgment. Generated ideas often degrade after implementation, research code lags far behind pattern-matching benchmarks, and end-to-end autonomous systems have not yet consistently reached major-venue acceptance standards. We further show that greater automation can obscure rather than eliminate failure modes, making human-governed collaboration the most credible deployment paradigm. Finally, we provide a structured taxonomy, benchmark suite, and tool inventory, cross-stage design principles, and a practitioner-oriented playbook, with resources maintained at our project page.

## Shipped code — file tree (`projects/PROJ-602-https-arxiv-org-abs-2605-18661/external/awesome-ai-auto-research/`)

```
LICENSE
README.md
docs/assets/.keep
docs/assets/phase1.png
docs/assets/phase2.png
docs/assets/phase3.png
docs/assets/phase4.png
docs/assets/s1.png
docs/assets/s5.png
docs/assets/s6.png
docs/assets/s8.png
docs/assets/teaser.png
docs/assets/teaser_paper.png
index.html
```

## Detected entry points

- (no .py entry scripts auto-detected; see README usage)

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `awesome-ai-auto-research` — not re-implementing it.
