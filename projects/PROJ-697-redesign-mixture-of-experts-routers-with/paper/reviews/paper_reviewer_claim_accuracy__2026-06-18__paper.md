---
action_items: []
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:38:47.874629Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.5
verdict: accept
---

The manuscript’s factual claims are, for the most part, well‑supported by the cited literature and by the authors’ own experimental evidence.

**Citation correctness**
- The claim that aligning router rows with the principal singular direction is a principled design is correctly supported by classic linear‑algebra references: Eckart & Young (1936) for the optimal low‑rank approximation, Golub & Van Loan (1996) for power‑iteration theory, and Halko et al. (2010) for practical approximate SVD methods. These citations accurately reflect the mathematical background.
- References to Mixture‑of‑Experts scaling (e.g., \cite{deepseekv4,k2}) are appropriate and correspond to the cited works that discuss trillion‑parameter models.
- All other citations (e.g., \cite{adamw}, \cite{muon}, \cite{hyperball}) correctly point to the described optimizers and their properties.

**Strength of evidence**
- The theoretical section (Sec. 3.1–3.2) derives the update rule (Eq. 10) and shows its equivalence to a constrained ascent on the Rayleigh quotient. The derivation is mathematically sound and matches the cited matrix‑computation literature.
- Empirical results (Figs. 1‑4, Tables 2‑5) consistently demonstrate modest but reproducible gains in pre‑training loss, perplexity, and downstream accuracy across multiple model scales and optimizers. The reported numbers are internally consistent and the experimental setup is described in sufficient detail to be reproducible.
- The ablation studies correctly attribute performance improvements to the power‑iteration step rather than to simple row‑wise normalization, confirming the core claim of the paper.

**Potential over‑statements**
- The statement that “the principal singular direction provides the most expressive mathematical description of a matrix” is somewhat strong; the singular vector captures the dominant mode but does not fully describe the matrix. However, within the context of compressing an expert’s weight matrix into a single router vector, the claim is justified and does not mislead.
- The claim of “zero communication overhead” is accurate for the forward pass (router weights can be pre‑computed), but the runtime power‑iteration does add a small amount of compute, which the authors acknowledge (0.2 % slowdown). This nuance is properly disclosed.

**Conclusion**
All major factual statements are either directly supported by the cited literature or by the authors’ own experimental data. No citation misrepresents the source material, and no claim exceeds what the presented evidence can substantiate. Consequently, the paper meets the standards for claim accuracy.
