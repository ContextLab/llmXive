---
action_items: []
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T10:17:56.014517Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.5
verdict: accept
---

The manuscript presents a coherent logical chain from problem statement to proposed solution and empirical validation. Below I outline the key points where the reasoning is internally consistent, as well as minor clarifications that would further strengthen the logical flow.

### 1. Problem Definition and Motivation (Section 1, Abstract)
- The authors correctly distinguish **activation** (high response to a concept) from **causal representation** (response that persists only when the concept is present).  
- The claim that “activation alone is insufficient evidence of representation” is supported by prior literature (e.g., [Kanwisher 1997], [Epstein 1998]) and by the intuitive example of correlated cues (color, pose). No logical gap is introduced here.

### 2. Formalization of Causal Scores (Section 3.2, Eq. 1‑4)
- The three scores (activation, semantic‑negative, counterfactual‑edit) are defined mathematically and each captures a distinct aspect of causal specificity.  
- The **semantic‑negative score** subtracts the average response to the *hardest* 10 negatives, which aligns with the goal of testing the worst‑case confound.  
- The **counterfactual score** compares each positive image to its hardest edited counterpart, ensuring that the only manipulated variable is the target concept.  
- The **causal score** is the simple average of the two specificity scores (Eq. 4). This averaging is a logical choice because both types of negatives are intended to control for different confounds; treating them equally avoids bias toward either visual or semantic distractors.

### 3. Candidate Region Selection (Section 3.2, end)
- Selecting voxels with **positive causal scores** (or the top‑K when needed) follows directly from the definition: a positive causal score guarantees that the voxel’s response to the target exceeds its response to the strongest confounds.  
- The subsequent region‑level aggregation (averaging voxel activations) is a logical extension that preserves the per‑voxel guarantees at the set level.

### 4. Decision Rule for Final Verdict (Section 3.3)
- The two‑criterion rule (causal evidence *and* measured‑data coverage) is logically sound: high causal evidence on generated data is only compelling if the measured dataset can meaningfully test the same hypothesis.  
- When coverage is low, the authors correctly downgrade the confidence and request follow‑up experiments rather than over‑claiming discovery. This conditional reasoning avoids the classic “false positive” pitfall.

### 5. Empirical Validation Aligns with the Logical Claims
- **Figure 4** (Causal vs Correlation) demonstrates the predicted reduction in false positives (≈70 % → ≈23 %) when ranking by causal score, directly confirming the logical expectation that causal filtering discards voxels that only respond to correlated cues.  
- **Table 1** shows that BrainCause maintains activation levels comparable to Max‑Activation (2.05 vs 2.76 on generated positives) while substantially improving causal scores (0.62 vs 0.08 on generated negatives). This matches the claim that causal ranking “preserves high activation while improving causality.”  
- The **sanity‑check** in Table 2 (alignment with known ROIs) provides logical triangulation: if the causal method were mis‑specified, it would likely mis‑localize known categories, which it does not (≥90 % alignment for faces, bodies, etc.).

### 6. Acknowledged Limitations Do Not Contradict Core Claims
- Section 6 explicitly notes that failures in semantic‑negative generation (e.g., “sky”, “reflection”) can leave some confounds untested. This admission is consistent with the earlier conditional decision rule and does not undermine the central logical argument; it simply bounds the scope of the claim (“causal with respect to the alternatives considered”).

### Minor Clarifications (non‑critical)
- **Section 3.2**: The notation \(N_v^{\mathrm{hard}}\) (top‑10 negatives) could be clarified that the set size is fixed to 10 for all voxels, ensuring comparability across voxels.  
- **Section 3.3**: The phrase “confidence score is measured using statistical tests … see Appendix A” could briefly mention the test (one‑sided empirical p‑value) for completeness, but this does not affect logical soundness.  

Overall, the manuscript presents a logically consistent framework: premises are clearly stated, definitions follow naturally from those premises, and conclusions are directly supported by both mathematical formulation and empirical evidence. No internal contradictions were found.
