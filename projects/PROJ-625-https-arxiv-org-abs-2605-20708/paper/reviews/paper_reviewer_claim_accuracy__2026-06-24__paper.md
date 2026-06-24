---
action_items: []
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T18:00:23.537551Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.5
verdict: accept
---

The manuscript’s factual claims are well‑aligned with the presented evidence and the cited literature.

1. **Empirical gains of DAR** – The paper states that Diffusion‑Adaptive Routing (DAR) improves SiT‑XL/2 by 2.11 FID (7.56 vs 9.67) on ImageNet 256×256 and reaches comparable or better quality with ≈8.75× fewer training iterations. Table 1 (lines ≈ 560‑620) directly reports these numbers for the static‑c4 variant (600 K iterations) against the SiT baseline (1.75 M iterations), confirming the claim.

2. **Three diagnostic “symptoms”** – The authors identify forward‑magnitude inflation, backward‑gradient decay, and block‑wise redundancy. Figure 2 (lines ≈ 210‑240) visualises each metric across depth, and the accompanying description matches the observed trends. The cited works on PreNorm dilution (xiong2020layer; team2026attention; li2026siamesenorm) indeed discuss analogous phenomena, so the attribution is appropriate.

3. **Compatibility with REPA** – Experiments combining DAR with REPA (Table 2, lines ≈ 720‑750) show consistent FID improvements over REPA alone, supporting the claim of orthogonal benefits. The citation to REPA (yu2025repa) correctly references the representation‑alignment method.

4. **Timestep‑aware routing** – The paper contrasts static, explicit‑timestep, and dynamic query designs. Ablation results (Table 3, lines ≈ 770‑795) demonstrate that both timestep‑aware variants outperform the timestep‑blind baseline, and the linear‑probe analysis (Figure 4, lines ≈ 800‑820) confirms that timestep information is recoverable from the router inputs. The discussion accurately reflects the experimental evidence.

5. **Chunk‑size analysis** – The U‑shaped performance curve for chunk sizes (Table 4, lines ≈ 845‑870) is theoretically justified by Proposition 1, whose proof is supplied in Appendix C. The derivation matches the cited rate‑distortion intuition, and the empirical optimum (S = 4) aligns with the predicted \(S^\star\).

6. **Citation relevance** – All major statements are backed by appropriate references. For example, the description of U‑Net‑like skip routing cites Bao 2023 and Tian 2024, which indeed propose long‑skip connections for diffusion Transformers. The background on diffusion models correctly references Ho 2020, Song 2020, and related works.

No factual inconsistencies or mis‑attributed citations were found. The claims are proportionate to the presented data, and the paper does not overstate its contributions beyond what the experiments demonstrate. Consequently, the manuscript meets the standards for claim accuracy.
