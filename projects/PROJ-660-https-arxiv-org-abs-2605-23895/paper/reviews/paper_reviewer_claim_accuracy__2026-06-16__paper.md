---
action_items:
- id: 55caeb97bd54
  severity: writing
  text: Correct the citation for the statement about activation-maximization methods.
    The cited papers (Sereno1995Science, Engel1997CerebCortex) discuss retinotopic
    mapping and low-level visual organization, not activation-maximization techniques.
    Replace with appropriate references to modern activation-maximization work in
    neuroscience (e.g., NeuroGen \cite{neurogen} or related studies).
- id: 321d079ba314
  severity: writing
  text: Provide a supporting citation for the claim that activation-maximization methods
    cannot distinguish true concept representations from correlated cues. If this
    is an empirical observation, cite a study that demonstrates the limitation, or
    qualify the statement as a hypothesis.
- id: 4fea594a5404
  severity: writing
  text: "Verify that all statements about \u201Cearly fMRI studies revealed important\
    \ aspects of visual organization\u201D are accurately matched to the cited references.\
    \ For example, ensure that the citation to Kanwisher1997 indeed supports the claim\
    \ about category-selective regions for faces, and similarly for Epstein1998, downing2001cortical,\
    \ and cohen2000visual."
- id: 8776dc5544fc
  severity: science
  text: "When asserting that BrainCause \u201Crecovers known functional localizations\
    \ and identifies new candidate representations across dozens of concepts,\u201D\
    \ ensure that the quantitative results (e.g., number of concepts with high causal\
    \ scores) are explicitly reported in the main text or appendix to substantiate\
    \ the \u201Cdozens\u201D claim."
- id: 286020b4caf4
  severity: writing
  text: Clarify the source of the 260 concepts list. The manuscript states it was
    generated using ChatGPT (GPT-5) \cite{openai2025gpt5systemcard}; confirm that
    this system card indeed describes GPT-5 capabilities relevant to concept list
    generation, or replace with a more appropriate citation.
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T10:18:17.120864Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The manuscript introduces **BrainCause**, a pipeline that combines generative models, language models, and an image‑to‑fMRI encoder to test causal relationships between visual concepts and brain activity. The experimental design and analysis are generally sound, but several factual‑citation mismatches need correction to maintain scientific credibility.

### Specific concerns about claim accuracy and citations

1. **Mis‑aligned citations for activation‑maximization**  
   In the introduction the authors cite *Sereno1995Science* and *Engel1997CerebCortex* to support the claim that “activation‑maximization based methods identify regions with high responses to a target concept.” These papers focus on retinotopic mapping and low‑level visual organization and do not discuss activation‑maximization in the sense used here. Replace these citations with works that explicitly employ activation‑maximization for brain mapping (e.g., *NeuroGen* \cite{neurogen} or similar studies).

2. **Unsupported limitation of activation‑maximization**  
   The text and Figure 1 state that activation‑maximization “cannot distinguish true concept representations from correlated cues.” No reference is provided for this limitation. If prior literature demonstrates this issue, a citation must be added; otherwise, the statement should be framed as a hypothesis that the current work investigates.

3. **Citation consistency for early fMRI findings**  
   The related‑works paragraph correctly references *Kanwisher1997*, *Epstein1998*, *downing2001cortical*, and *cohen2000visual* for category‑selective regions (faces, bodies, places, words). Ensure each claim is directly tied to the appropriate paper to avoid over‑generalization—for instance, confirm that the “faces” claim aligns with *Kanwisher1997* and that “places” aligns with *Epstein1998*.

4. **Quantitative backing for “dozens of concepts”**  
   The abstract and conclusions claim that BrainCause “identifies new candidate representations across dozens of concepts.” While the study evaluates 260 concepts, the number that passes the full causal validation pipeline is not explicitly reported in the main text. Adding a concise statistic (e.g., “X out of 260 concepts showed significant causal evidence”) would substantiate this claim.

5. **Verification of GPT‑5 system‑card citation**  
   The method states that the concept list was generated using ChatGPT (GPT‑5) \cite{openai2025gpt5systemcard}. The cited system card describes GPT‑5 capabilities but does not specifically address concept‑list generation. Confirm that the referenced document covers this use case, or replace the citation with a more relevant source (e.g., a technical report on prompting LLMs for concept extraction).

### Overall assessment

The core methodology, including the generation of positive, semantic‑negative, and counterfactual images, the scoring of voxels, and the validation on both predicted and measured fMRI data, is internally consistent. The quantitative tables and figures support the claim that causal scoring reduces false positives relative to activation‑only baselines. However, the above citation issues undermine the factual grounding of several key statements. Addressing these concerns will improve the manuscript’s reliability without requiring changes to the experimental results.
