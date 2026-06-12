---
action_items:
- id: 75cdc0b6687e
  severity: writing
  text: Add an explicit license declaration for the benchmark dataset and verifier
    code in the main text or repository README.
- id: 08afd595343f
  severity: writing
  text: Clarify the provenance and licensing of seed files (e.g., piano_sketch.mscz)
    in the methodology section to ensure redistribution rights.
- id: 688b895a9756
  severity: writing
  text: Include a version tag or commit hash for the released repository to ensure
    reproducibility and link stability.
artifact_hash: 0d09bbe6836d7c3ba38dc0386a722fbaec7b727145cadfcb8e187e60eeb63fee
artifact_path: projects/PROJ-607-https-arxiv-org-abs-2605-19769/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-12T11:26:45.973685Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive benchmark for computer-use agents, but the **data quality metadata** requires clarification to ensure long-term reproducibility and legal compliance.

**License and Provenance:** The paper states in `sections/conclusion.tex` that \ours is released as an "extensible infrastructure," yet no explicit license (e.g., MIT, Apache 2.0, CC-BY) is declared in `main.tex` or the `sections/methodology.tex`. Without a clear license, users cannot legally determine if they can reuse the 1,000 tasks or 33 verifiers. Additionally, `sections/methodology.tex` mentions that the system "generates and packages the required files" for tasks (e.g., `piano_sketch.mscz` in `Appendix/task_example.tex`). It is critical to specify whether these seed files are fully synthetic or derived from existing copyrighted material. If they are synthetic, this should be explicitly stated to avoid ambiguity regarding intellectual property rights.

**Version Control and Stability:** The GitHub repository `https://github.com/echo0715/OpenComputer` is cited in `main.tex`, but no specific commit hash, tag, or version number is provided. For a benchmark claiming 1,000 tasks, a versioned release (e.g., v1.0) is necessary to prevent "link rot" or schema drift where the code evolves away from the results reported in the paper. Future readers must be able to retrieve the exact code state used for the evaluation in `sections/experiment.tex`.

**Schema Documentation:** While `sections/methodology.tex` defines the task instance conceptually as $\tau=(x,e,c)$ and mentions `task.json`, there is no reference to a formal schema definition (e.g., JSON Schema) or a data card (e.g., Datasheets for Datasets). Including a link to a schema file or datasheet would improve the usability of the benchmark for downstream developers.

Addressing these metadata gaps will ensure the benchmark is not only scientifically robust but also legally and technically sustainable for the community.
