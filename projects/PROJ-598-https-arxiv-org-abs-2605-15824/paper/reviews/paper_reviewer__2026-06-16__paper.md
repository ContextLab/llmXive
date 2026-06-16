---
action_items:
- id: f422e9b5d9ea
  severity: science
  text: "Replace or verify all citations that reference works from future years (e.g.,\
    \ 2025, 2026). Ensure every bibliography entry corresponds to an existing, peer\u2011\
    reviewed source with a verifiable verification_status."
- id: 786395e8218d
  severity: science
  text: Provide a complete, reproducible description of the dataset curation pipeline,
    including exact numbers of videos per class, annotation formats, and any filtering
    thresholds used. Release the curated dataset or a detailed script to reconstruct
    it.
- id: 4e172dce12b8
  severity: writing
  text: Clarify the definitions and computation procedures for the evaluation metrics
    HGC, LGC, and NTP (currently only listed in tables). Include equations or references
    so readers can reproduce the scores.
- id: cbec5ce7442d
  severity: writing
  text: "Add explicit hardware and software environment details for the reported 23.8\u202F\
    FPS figure (GPU model, driver version, batch size, precision, any optimizations).\
    \ Provide a reproducibility checklist."
- id: e11122073050
  severity: science
  text: "Expand the description of the Training\u2011Free KV Cache Rescheduling algorithm:\
    \ provide pseudo\u2011code or a clear algorithmic flow, and discuss computational\
    \ overhead and memory usage."
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: scientific concerns about unverifiable citations and insufficient reproducibility
  details
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T01:50:16.489799Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

## Strengths
- Addresses a high‑impact problem: real‑time, interactive garment‑level video customization.
- Proposes a novel combination of (i) teacher model with in‑context learning, (ii) streaming distillation with gradient‑reweighted DMD, and (iii) training‑free KV‑cache rescheduling.
- Shows strong quantitative results, notably 23.8 FPS generation and superior scores on several custom metrics.
- Includes extensive experiments: main results, multiple ablations, and a user study.
- Provides a detailed data‑curation pipeline and a sizable curated dataset (≈ 62 K triplets).

## Concerns
- **Citation integrity**: Numerous references cite works from future years (2025, 2026) that cannot be verified, violating the “all citations verified” requirement.
- **Reproducibility gaps**: The dataset construction lacks precise statistics, annotation formats, and filtering thresholds; no public release or reconstruction script is provided.
- **Metric definitions**: Custom metrics (HGC, LGC, NTP) are presented without formal definitions or computation formulas, hindering independent replication.
- **Hardware reporting**: The reported 23.8 FPS speed lacks a complete hardware/software specification (GPU model, driver, CUDA version, precision mode, batch size, any optimizations).
- **Algorithmic detail**: KV‑cache rescheduling is described only conceptually; pseudo‑code or a step‑by‑step algorithm, as well as analysis of computational overhead, is missing.

## Recommendation
The manuscript presents an innovative approach with promising results, but the scientific foundation is weakened by unverifiable citations and insufficient reproducibility information. I recommend a **major revision (science)** and ask the authors to address the action items above to ensure the work is trustworthy, reproducible, and ready for publication.
