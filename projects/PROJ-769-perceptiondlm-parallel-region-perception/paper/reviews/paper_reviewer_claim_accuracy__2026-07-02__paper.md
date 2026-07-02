---
action_items:
- id: 09c1e52973a3
  severity: writing
  text: The claim of being the 'first to achieve parallel region caption' (Abstract)
    is overstated. The authors must distinguish their work from prior non-autoregressive
    or parallel decoding attempts in vision-language models that may have touched
    on similar concepts, even if not explicitly for 'region' tasks.
- id: b51e3e7747f4
  severity: science
  text: The citation 'gpt5.2' (Section 4) refers to a model version that does not
    exist in the public domain. Citing a non-existent model as a judge for benchmark
    evaluation undermines the reproducibility and factual accuracy of the experimental
    claims. Use a publicly available model or provide a verifiable source.
- id: 725d287f1ddc
  severity: writing
  text: The claim that PerceptionDLM-Base 'outperforms LLaDA-V on 15 of 16 benchmarks'
    (Intro) is technically accurate but misleading without explicitly highlighting
    the specific benchmark (MMMU) where it fails, as the text implies near-universal
    superiority.
- id: 1527975763e1
  severity: science
  text: The citation 'carion2025sam' (Section 3) refers to 'SAM 3', a 2025 arXiv preprint.
    If this model is not publicly available, the claim that the authors used it to
    construct the dataset is unverifiable. Clarify the exact version and availability
    of this tool.
artifact_hash: c2fe12c2ed011a24b223e04bd3ecaeef100189d2028034fd68b96cae705b806b
artifact_path: projects/PROJ-769-perceptiondlm-parallel-region-perception/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:20:58.013422Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the factual accuracy of claims and the validity of their supporting citations.

**1. Overstated Novelty Claims**
In the Abstract and Introduction, the authors claim: "To the best of our knowledge, we are the first to achieve parallel region caption and perception by leveraging the advantages of diffusion language models." While the specific combination of *region-level* parallelism with *diffusion* language models may be novel, the claim of being the "first" to achieve "parallel region caption" is too broad. There are prior works exploring parallel decoding in vision-language tasks (e.g., non-autoregressive image captioning or parallel grounding) that are not sufficiently distinguished. The claim should be refined to specify "parallel region captioning using *diffusion language models*" to avoid ambiguity and potential inaccuracy regarding the broader field of parallel generation.

**2. Non-Existent or Unverifiable Citations**
The paper relies heavily on `GPT-5.2` as a judge model for the ParaDLC-Bench evaluation (e.g., Section 4, line 138; Appendix, line 102). The citation `gpt5.2` in the bibliography points to a URL for "OpenAI-GPT-5.2" with a 2025 date. As of the current public knowledge, GPT-5.2 is not a released or publicly documented model version. Using an unreleased or non-existent model as a primary evaluation metric (the "judge") severely compromises the reproducibility and factual validity of the benchmark results. The authors must either switch to a publicly available, verifiable model (e.g., GPT-4o, Llama-3.1-70B) or provide a clear, accessible link to the specific model weights/API used.

**3. Data Construction Pipeline Dependencies**
The training data engine section (Section 3, line 168) cites `carion2025sam` (SAM 3) for re-predicting masks. The bibliography lists this as a 2025 arXiv preprint. If this model is not yet publicly available or stable, the claim that the authors "obtained 334k images... from the COCONut dataset" using this specific tool is difficult to verify. The authors should clarify the exact version and availability of SAM 3 used in their pipeline to ensure the reproducibility of the ParaCaption-5.7M dataset construction.

**4. Precision of Comparative Claims**
The claim in the Introduction (line 108) that "PerceptionDLM-Base outperforms LLaDA-V on 15 of 16 benchmarks" is technically supported by Table 1 (where MMMU is the exception). However, the phrasing could be slightly misleading as it implies a dominant performance across the board without immediately highlighting the specific failure case (MMMU) where the baseline is superior. While not a factual error, it is a matter of precision in scientific communication. The text should explicitly mention the MMMU exception in the same sentence to provide a balanced view of the comparative results.

**5. Citation Consistency**
The citation `nielarge` (e.g., Section 3, line 10) refers to "Large Language Diffusion Models" (NeurIPS 2025). The bibliography entry `nielarge` is consistent, but the paper frequently cites `you2025llada` (LLaDA-V) as the primary baseline. The distinction between the base LLaDA model and the LLaDA-V variant should be clear in the text to avoid confusion about which specific architecture is being compared. The current text is generally clear, but ensuring that all citations to "LLaDA" explicitly refer to the correct variant (Base vs. V) would improve accuracy.

In summary, the paper makes strong claims about novelty and performance that are generally supported by the provided tables, but the reliance on unreleased models (GPT-5.2, SAM 3) for critical evaluation and data construction steps introduces significant risks to reproducibility and factual accuracy. The "first" claim also requires more precise wording to avoid overgeneralization.
