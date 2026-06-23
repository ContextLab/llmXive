---
action_items:
- id: 5f89a55a1361
  severity: science
  text: "Provide statistical significance testing (e.g., confidence intervals or p\u2011\
    values) for all quantitative results (image editing, Sudoku, and text reasoning).\
    \ Without these, the reported improvements cannot be judged robustly."
- id: 5e469f1c4bf4
  severity: science
  text: "Report the number of random seeds, variance across runs, and any hyper\u2011\
    parameter search procedures used. This is essential to assess reproducibility\
    \ and to rule out p\u2011hacking."
- id: 4ed2f2f53e30
  severity: writing
  text: Include a detailed description of the test set construction for Sudoku (e.g.,
    number of boards, distribution of corruption levels) and for the text benchmarks
    (e.g., exact splits, whether validation was used).
- id: f1014c3380e2
  severity: science
  text: Add ablation studies that isolate the contribution of each component (Reflective
    Masking vs. History Reference vs. decay vs. HER) across all three task domains,
    not only Sudoku, to demonstrate that gains are not due to a single dominant factor.
- id: 8de1cd23d27a
  severity: science
  text: "Clarify whether the same random corruption distribution (top\u2011k proposal)\
    \ is used during training and evaluation, and quantify any distribution shift.\
    \ If there is a shift, report its magnitude and its impact on performance."
- id: f769cc48b200
  severity: writing
  text: "Report computational cost (e.g., FLOPs, wall\u2011clock time) for the multi\u2011\
    turn revision process compared to standard baselines, to substantiate the claim\
    \ of test\u2011time scaling efficiency."
artifact_hash: 7fece54febe808e7b8d966174edf071d45cfb2bebbcbdcb010a99fdaf0b84671
artifact_path: projects/PROJ-765-multi-turn-reflective-masking-elicits-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:22:26.087754Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents an intriguing post‑training method—Reflective Masking (RM)—that enables mask diffusion models (MDMs) to iteratively revise their outputs, and introduces a parameter‑free History Reference (HR) mechanism. The theoretical sections (Appendix A) are mathematically sound, showing that minimizing the per‑position cross‑entropy recovers the Bayes‑optimal revision policy and that HR cannot increase Bayes risk. However, the empirical evidence supporting the central claims is insufficiently rigorous from a scientific‑evidence standpoint.

**Sample sizes and controls**  
- **Image editing**: The authors train on 85 k examples and evaluate on 1 700 held‑out images. While the test set size is reasonable, no variance measures (e.g., standard deviations, confidence intervals) are reported for the metrics (Edit Precision, Coverage, MAE‑RGB, etc.). It is unclear whether the reported gains (e.g., Precision 99.73 % vs. 71.84 %) are statistically significant or could be due to random fluctuations in the test split. Moreover, the baselines (Lumina, Lumina+SFT) are not re‑trained under identical random seeds, raising concerns about uncontrolled confounds.

- **Sudoku revision**: The experiments use a tiny 0.81 M‑parameter model, but the paper does not disclose how many Sudoku boards were used for testing, nor the distribution of corruption levels (4–20 cells). Without this information, the reported Exact Accuracy improvements (82.4 % → 93.4 %) cannot be evaluated for robustness. No error bars or repeated‑run statistics are provided.

- **Text reasoning**: Benchmarks (MATH500, MBPP, ARC‑Challenge) are evaluated with single‑run scores. The training split for MBPP is described as “30 % for training, 70 % for testing,” but the exact number of examples, random seed handling, and whether validation was used are omitted. The lack of variance reporting makes it impossible to assess whether the observed Δ = 2.4 % (MATH) or Δ = 8.8 % (MBPP) are meaningful.

**Risk of p‑hacking / over‑fitting**  
The paper does not describe any hyper‑parameter search or early‑stopping criteria. Given the multiple design choices (decay factor γ, HER rotation, number of revision steps T, top‑k = 50, etc.), the possibility of tuning these components to the test sets cannot be ruled out. An explicit ablation across all three domains (beyond the Sudoku table) would help demonstrate that each component contributes independently rather than being over‑fitted to a particular task.

**Effect size and practical significance**  
The image‑editing results show dramatic relative improvements, but absolute numbers (e.g., PSNR 34.8 dB vs. 23.9 dB) need contextualization: are these differences perceptually significant? A user‑study is mentioned, yet the methodology (number of participants, statistical analysis) is absent. For Sudoku, the “Replay Mistake” metric drops from 0.57 % to 0.03 %, but the absolute impact on downstream downstream utility (e.g., solving time) is not quantified.

**Recommendations**  
To strengthen the scientific evidence, the authors should (1) report confidence intervals or p‑values for all quantitative tables, (2) disclose the number of random seeds and variance across runs, (3) provide full details of test‑set construction for Sudoku and text tasks, (4) conduct comprehensive ablations of RM, HR, decay, and HER across all modalities, (5) quantify any distribution shift between the training corruption proposal and inference‑time errors, and (6) include computational cost analyses for multi‑turn revision versus standard baselines.

Addressing these points will make the empirical claims more robust and the paper’s contributions clearer to the community.
