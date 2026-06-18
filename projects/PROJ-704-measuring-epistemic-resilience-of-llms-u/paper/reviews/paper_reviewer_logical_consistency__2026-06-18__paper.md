---
action_items: []
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:46:12.418577Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.5
verdict: accept
---

The manuscript presents a well‑structured argument that clean benchmark performance does not guarantee “epistemic resilience” of large language models (LLMs) when faced with misleading medical context. The logical flow from problem statement to methodology, results, and conclusions is coherent and free of contradictions.

1. **Definition and Motivation (Abstract & Introduction, lines 1‑30)** – The authors clearly define “epistemic resilience” and motivate its importance by contrasting clean exam‑style benchmarks with real‑world clinical interactions. The claim that high clean scores “encourage the assumption that high scores imply safe medical judgment” is directly challenged by the subsequent empirical findings, establishing a logical premise‑conclusion relationship.

2. **Benchmark Construction (Section 3, lines 120‑210)** – The two‑dimensional taxonomy (content corruption × provenance) is logically justified: each dimension captures a distinct source of misinformation. The pipeline (applicability filtering → injection generation) ensures that injected context does not alter the ground‑truth answer, which is essential for a valid resilience test. No logical gaps appear between the taxonomy description (Table 2) and the generation procedure (Appendix A.3).

3. **Experimental Design (Section 4.1, lines 260‑300)** – The authors’ definition of “epistemic resilience” (clean‑correct → injected‑correct) is precise, and the metrics (clean accuracy, Type 1/2 accuracy, ASR, TASR) are logically derived from this definition. The distinction between focused (Type 1) and mixed (Type 2) delivery is consistently applied throughout the results.

4. **Results Consistency (Section 4.2, Figures 2‑6, Tables 3‑5)** – The reported numbers support the central claim: models with the highest clean accuracy (e.g., Gemini‑3.1‑pro high reasoning, 83.5 % clean) suffer the greatest drop under focused injection (29.9 % Type 1 accuracy, 65.0 % ASR). The taxonomy analysis (Figure 6) aligns with the quantitative tables (Appendix B.5), confirming that authority‑framed and rule‑like corruptions are the most damaging. No contradictory statements are observed.

5. **Mitigation Case Studies (Section 4.5, lines 420‑460)** – The authors present two interventions (search‑based verification and defensive prompting) and report modest improvements. The logical inference that “search helps only when the model can adjudicate between evidence and the injected claim” follows directly from the observed differential impact on Gemini‑3.1‑pro versus Gemini‑3.1‑flash‑lite. The discussion appropriately qualifies the scope of these findings.

6. **Conclusion (Section 5, lines 470‑490)** – The final statements accurately summarize the empirical evidence without overstating the results. The authors acknowledge limitations (e.g., multiple‑choice format, synthetic injections) in Appendix E.1, which maintains logical honesty.

Overall, the manuscript’s arguments are internally consistent, the experimental methodology faithfully operationalizes the defined concepts, and the conclusions are logically entailed by the presented data. No logical fallacies, circular reasoning, or unsupported causal claims were detected.
