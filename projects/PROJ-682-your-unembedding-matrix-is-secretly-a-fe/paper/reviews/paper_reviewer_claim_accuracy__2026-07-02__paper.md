---
action_items:
- id: c3a37952473a
  severity: writing
  text: 'The review focuses on the accuracy of factual claims and the validity of
    the mathematical derivations supporting the paper''s central hypotheses. Mathematical
    Validity of the "Average Token" Derivation (Section 3.2.2): The paper claims to
    reverse-engineer an "average" token embedding $\hat{\vh}$ using the formula $\hat{\vh}
    = \log(\hat{\vp}) \, \mW_{\mathcal{U}}^+$ (Eq. 4). This derivation is mathematically
    flawed. The starting point is the logit equation $\vh \, \mW_\mathcal{U}^\top
    = \log(\vq)'
artifact_hash: 23484ba7b10cc08665875915717095ae222ff4767aae24d46926097ffc583ae4
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:54:36.693147Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the validity of the mathematical derivations supporting the paper's central hypotheses.

**Mathematical Validity of the "Average Token" Derivation (Section 3.2.2):**
The paper claims to reverse-engineer an "average" token embedding $\hat{\vh}$ using the formula $\hat{\vh} = \log(\hat{\vp}) \, \mW_{\mathcal{U}}^+$ (Eq. 4). This derivation is mathematically flawed. The starting point is the logit equation $\vh \, \mW_\mathcal{U}^\top = \log(\vq) + \vb$. The authors treat $\vb$ as a scalar bias that can be "omitted for analytical simplicity." However, in the context of the softmax and log-likelihood, the bias term $\vb$ is a vector where every element is identical (the log-sum-exp term). When inverting the equation to solve for $\vh$, the term $\vb \, \mW_{\mathcal{U}}^+$ does not vanish; it projects the constant bias vector onto the pseudo-inverse of the unembedding matrix. Since $\mW_{\mathcal{U}}$ is typically rectangular ($|\mathcal{V}| \times d$) and rank-deficient (or at least not full row rank), the pseudo-inverse does not simply cancel the bias. The claim that $\hat{\vh}$ is accurately recovered by ignoring this term is unsupported. The resulting $\hat{\vh}$ is likely a distorted representation that does not truly correspond to the "frequency-weighted average embedding" as claimed. This undermines the entire "Logit Spectroscopy into Average Token" analysis in Section 3.2.3, as the input to that analysis is mathematically suspect.

**Causal Link Between Edge Spectrum and Frequent Tokens (Section 3.2.3):**
The paper asserts that the "edge spectrum" (singular vectors with smallest and largest singular values) is responsible for encoding frequent tokens based on the observation that filtering these dimensions causes large logit shifts ($\Delta \pi$). While the observation of high $\Delta \pi$ at the edges is reported, the leap to the conclusion that this subspace *is* the "average token" subspace is not rigorously supported. High sensitivity ($\Delta \pi$) indicates that a dimension is important for the *current* logit distribution, but it does not prove that the dimension *encodes* the average token specifically. The paper fails to demonstrate that the projection of the *true* average token (if one could be defined independently) lies primarily in the edge spectrum. The argument relies on the circular logic that the edge spectrum is the average token subspace because filtering it changes the logits of frequent tokens, which are assumed to be the average token. A more robust claim would require showing that the edge spectrum components of *random* or *semantic* tokens are negligible, or that the edge spectrum components of the *actual* average token (derived via a different, valid method) are dominant.

**Accuracy of Baseline Comparison (Section 4.2):**
The paper claims that the comparison with BERT-whitening is unfair because whitening "requires supervision of NLI dataset" (Section 4.2, paragraph 2). This is factually incorrect regarding the cited work (Su et al., 2021). The paper "Whitening Sentence Representations for Better Semantics and Faster Retrieval" explicitly details an *unsupervised* whitening procedure that uses only the statistics of the input data (mean and covariance) without any labeled NLI data. The authors of the current paper appear to have conflated the supervised variant of whitening with the method as a whole. By comparing their zero-shot method only against a supervised version of the baseline, the paper misrepresents the baseline's capabilities and potentially inflates the perceived advantage of their method. The claim that "whitening... requires supervision" is false and misleads the reader about the nature of the comparison.

These issues suggest that the core mechanistic interpretation (the "average token" and "edge spectrum" hypothesis) rests on a mathematically unsound derivation and a potentially biased experimental comparison. While the empirical performance gains of the proposed method are interesting, the *explanation* provided for *why* it works is not supported by the evidence presented.
