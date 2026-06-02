---
action_items: []
artifact_hash: 6787a87df841d43fd2785f288cbdae2d1c09b5ec14bf84bfd0cf81559d785c80
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: Comprehensive benchmark with clear methodology, reproducible experiments,
  and well-documented contributions suitable for publication.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T11:07:39.577197Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.5
verdict: accept
---

# Free-form review body

## Strengths
- **Comprehensive benchmark design**: MulTaBench introduces 40 datasets (20 image-tabular, 20 text-tabular) with clear acceptance criteria for joint signal and task-awareness
- **Methodological rigor**: Well-defined curation pipeline with formal mathematical criteria (δ=0.001, ρ=3/5) and 5-fold cross-validation across 5 learners
- **Extensive ablation studies**: Systematic analysis across encoder scale (small/large), embedding dimension (15/30/60/384), and task type (classification/regression)
- **Strong reproducibility**: Complete NeurIPS checklist, detailed hyperparameters in appendix, compute cost documentation, and Kaggle dataset repository
- **Qualitative validation**: Attention map visualizations demonstrate TAR shifts encoder focus to task-relevant regions (lung in CheXpert, optic disc in Glaucoma)
- **Clear limitations**: Authors acknowledge curation entanglement, selection bias, and computational overhead of TAR

## Concerns
- **Computational cost**: TAR adds ~10x overhead for text encoders (e5-small TAR: 2,417s vs frozen: 223s), which may limit practical adoption
- **Limited SOTA comparison**: Excludes autoregressive generative models (LLMs/VLMs) due to cost; TIME and MultimodalTabPFN baselines unavailable
- **Future-dated citations**: Several references cite 2025-2026 publications (expected for arXiv preprints, but requires verification at final publication)
- **Dataset reproducibility**: Some original dataset links broken (e.g., Seattle Airbnb, KARD); authors mitigated by re-uploading to Kaggle

## Recommendation
This paper presents a significant contribution to multimodal tabular learning through the MulTaBench benchmark. The methodology is sound, experiments are comprehensive with proper statistical significance reporting (95% CIs), and the findings generalize across learners, modalities, and encoder scales. The TAR approach addresses a genuine gap in existing tabular foundation models that rely on frozen embeddings. While computational overhead is a valid concern, the authors transparently document costs and the benchmark itself enables future architecture research. The paper meets publication standards for a benchmark/resource paper and is ready for acceptance with minor clarifications in the final version (citation verification, broken link remediation).
