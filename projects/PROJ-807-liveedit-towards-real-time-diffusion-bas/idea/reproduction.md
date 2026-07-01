# Reproduce & validate: LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-807-liveedit-towards-real-time-diffusion-bas/external/author-kit/   (clone of https://github.com/cvpr-org/author-kit)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing

**Abstract:** Streaming video editing has made rapid progress, yet practical deployment is still limited by two core issues: maintaining stable backgrounds and non-edited regions over time, and achieving the low latency required for real-time interactive scenarios. Meanwhile, recent streaming video generation methods are mostly developed for synthesis and cannot be directly applied to editing due to the strict preservation requirement and region-specific control. In this work, we present a novel streaming video editing framework that performs causal, frame-by-frame editing with strong content preservation and real-time responsiveness. Our key design is a three-stage distillation pipeline that progressively transfers editing capability from a powerful bidirectional foundation model to an efficient unidirectional streaming editor, enabling stable long-horizon edits without sacrificing visual fidelity. To further support real-time deployment, we introduce an AR-oriented mask cache that reuses region-related computation across frames, substantially reducing redundant processing and accelerating inference. Finally, we establish a dedicated benchmark for streaming video editing. Extensive evaluations demonstrate that our method achieves state-of-the-art visual quality among streaming baselines while drastically boosting inference speed to 12.66 FPS, making it suitable for interactive and augmented reality applications.

## Shipped code — file tree (`projects/PROJ-807-liveedit-towards-real-time-diffusion-bas/external/author-kit/`)

```
.github/workflows/latex-build.yml
.gitignore
README.md
cvpr.sty
fig/teaser.tex
ieeenat_fullname.bst
main.bib
main.tex
preamble.tex
rebuttal.tex
sec/0_abstract.tex
sec/1_intro.tex
sec/2_formatting.tex
sec/3_finalcopy.tex
sec/X_suppl.tex
```

## Detected entry points

- (no .py entry scripts auto-detected; see README usage)

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `author-kit` — not re-implementing it.
