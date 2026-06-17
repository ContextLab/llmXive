---
action_items:
- id: 9d256e0d06ef
  severity: writing
  text: 'Ensure that every bibliography entry listed in references.bib has verification_status:
    verified in the citation verification system.'
- id: 17495cfa0b64
  severity: writing
  text: "Add a detailed reproducibility appendix that lists all hyperparameters (e.g.,\
    \ \u03BB for KL loss, warmup steps, learning rate schedule, block size, k, optimizer\
    \ settings) and provides links to the released training and inference kernels."
- id: 55d2a796c6da
  severity: writing
  text: Include a comparative analysis (both quantitative and qualitative) against
    closely related adaptive sparse attention methods such as NSA, MoBA, and DSA,
    using the same 109B model scale if possible.
- id: 091cf98017ae
  severity: writing
  text: "Clarify the notation in equations\u202F(1)\u2013(4) (e.g., explicitly define\
    \ d_idx, the dimensions of Q_idx and K_idx, and the handling of causal masking\
    \ in the block\u2011max pooling step)."
- id: 14b17cb867db
  severity: writing
  text: "Provide a public repository link for the custom Top\u2011k and KV\u2011outer\
    \ kernels, and include a short benchmark script to reproduce the latency numbers\
    \ in Table\u202F1."
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: "minor issues \u2013 citation verification, reproducibility details, and\
  \ minor clarity improvements"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T16:26:16.403496Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

## Strengths
- **Clear architectural contribution**: Introduces a concise two‑branch sparse attention design (Index Branch + Main Branch) that integrates cleanly with Grouped‑Query Attention and operates at block granularity, enabling substantial FLOP reductions.
- **Comprehensive empirical evaluation**: Experiments span from a 10 B pilot model to a 109 B MoE model, covering a wide range of text, code, multimodal, and long‑context benchmarks. Results show competitive or superior performance to the dense GQA baseline while delivering up to 28.4× FLOP savings and significant wall‑clock speedups.
- **Thorough ablation studies**: The appendix explores gradient sources, KL‑gradient detachment, indexer warm‑up, block size, forced sink/local selection, and the optional index value head, providing solid evidence for the design choices.
- **Kernel‑level engineering**: Co‑designed efficient GPU kernels (exp‑free Top‑k, KV‑outer iteration, two‑phase combine) and demonstrated concrete latency improvements over baseline implementations.
- **Open‑source artifacts**: The inference kernel and model checkpoints are released, facilitating reproducibility and adoption.

## Concerns
- **Citation verification**: The bibliography contains many recent works (e.g., NSA, MoBA, FlashSparseAttention) but the review material does not indicate that all entries have been verified. Unverified citations violate the acceptance criteria.
- **Reproducibility details**: While the main text mentions training budget, block size, and selection budget, exact hyperparameters (learning‑rate schedule, λ for the KL loss, optimizer settings, warm‑up duration, random seeds) are not enumerated in a dedicated reproducibility section.
- **Comparison to closely related adaptive sparse methods**: The paper cites NSA, MoBA, DSA, etc., but does not provide direct empirical comparisons at the same scale. A side‑by‑side evaluation would better position the contribution.
- **Notation clarity**: Some equations (e.g., Eq 1–4) introduce symbols such as `d_idx` and the block‑max pooling operation without explicit dimensional explanations, which can hinder readers unfamiliar with the block‑wise formulation.
- **Kernel release details**: The custom Top‑k and KV‑outer kernels are described, yet the repository link and a minimal benchmark script to reproduce the latency tables are missing from the main paper.

## Recommendation
The manuscript presents a solid, well‑executed contribution to long‑context efficient Transformers. The methodology is sound, the experiments are extensive, and the engineering effort is commendable. However, to meet full publication standards, the authors should address the minor issues listed above—particularly citation verification, detailed reproducibility information, clearer comparisons to related work, and explicit notation clarifications. After these straightforward revisions, the paper will be ready for acceptance.
