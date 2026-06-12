# Revision Specification: Paper Science Revision — PROJ-604-https-arxiv-org-abs-2605-18739 round 1

**Generated**: 2026-06-12T04:36:21.844484+00:00
**Kind**: paper_science
**Project**: PROJ-604-https-arxiv-org-abs-2605-18739
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[4335f87f407e] (severity: writing)** Teaser Figure caption claims memory reduction from 35.4 GB, but Table 3 (tab:inference_progressive) shows 36.4 GB for BF16 baseline. Please align these numbers or specify the exact configuration for the 35.4 GB figure.
- **[f8e911468406] (severity: writing)** Section 2.2 states NVFP4 provides 'approximately 1.8x training speedup' without explicitly stating the baseline (BF16 Balanced SP). This conflicts with the Abstract's 2.15x claim (vs BF16 w/ SP). Clarify the baseline to avoid confusion.
- **[0b8fbbaf32af] (severity: writing)** The FPS claim (45.7 FPS) and E2E latency (36.3s for 64s video) imply different real-time factors depending on output frame rate. Clarify if FPS refers to model throughput or E2E system throughput to ensure accuracy.
- **[ea3ee48e1351] (severity: writing)** Code artifacts (repository, scripts, configs) not provided for review. Access to github.com/NVlabs/LongLive is required to evaluate code quality, modularity, tests, and reproducibility from scratch.
- **[8bf3c15ad90c] (severity: writing)** Paper mentions custom CUDA/Triton kernels for NVFP4 but does not provide kernel source or build instructions. Reproducibility of the core infrastructure cannot be verified without code access.
- **[b6b577fbdd77] (severity: writing)** Implementation Details (Appendix E) lists hyperparameters but omits dependency versions (PyTorch, DeepSpeed, CUDA). Add a requirements.txt or environment.yml for reproducibility.
- **[5ad768df760b] (severity: writing)** Dataset license is not specified. The Appendix describes a 120K video dataset but omits usage rights, hindering reproducibility and legal compliance.
- **[b8e390504004] (severity: writing)** Dataset access path is unclear. Only a general project GitHub link is provided; specific data download instructions or repository paths are missing.
- **[cf9eea9f410f] (severity: writing)** Data filtering thresholds are vague. The Appendix mentions MANIQA scoring for quality control but does not report the specific threshold values used for retention.
- **[90c9ec5e7350] (severity: writing)** Caption schema is undefined. The text describes 'structured captions' but does not provide a schema definition or example format for the annotations.
- **[32ecdae931c4] (severity: writing)** Simplify the teaser figure caption (Fig. 1) by moving detailed metric comparisons (e.g., 2.15x speedup) to the main text or a dedicated table to improve readability at print scale.
- **[685a19f7add3] (severity: writing)** Ensure internal legends and axis labels in composite figures (e.g., Fig. A.1, Fig. A.5) are legible at 100% zoom; consider increasing font size for sub-figure annotations.
- **[3d833baf343e] (severity: writing)** Define all acronyms at first use, especially in the Abstract (e.g., NVFP4, VAE, LoRA, GEMM, W4A4, KV cache).
- **[5324790d7556] (severity: writing)** Reduce jargon density in the Abstract; explain 'Balanced SP' and 'loss-bearing tokens' in plain English.
- **[04d3bbd33a5a] (severity: writing)** Define informal abbreviations like 'OOM' (Table 1) and framework-specific terms like 'FSDP', 'EMA', 'RoPE' in the Appendix.
- **[bad4f003a750] (severity: writing)** Teaser Figure caption states training latency is '1372.9 ms' per iteration, while Table 1 lists '1372.9' in seconds. This unit mismatch creates a logical contradiction between the abstract/teaser and the experimental data.
- **[5820d61e7274] (severity: writing)** Introduction claims SP inference on non-Blackwell GPUs 'matches the speed on Blackwell GPUs', but Appendix Table 1 shows 54.8s (H100 SP) vs 36.3s (GB200 NVFP4) for 64s videos. The evidence does not support the 'match' claim; it shows improvement over single-GPU but not parity with Blackwell.
- **[b78e19ddcb6e] (severity: writing)** The '45.7 FPS' metric is defined as model throughput (ms/frame) in the Teaser, but 'real-time generation' typically implies video duration vs generation time. Clarify if FPS refers to model throughput or effective video generation rate to ensure logical alignment with 'real-time' claims.
- **[1afa26cb9d53] (severity: writing)** Clarify the role of DMD in the Abstract to avoid overclaiming a 'clean pipeline'. Section 2 states DMD is used for distillation, but Abstract (Line 15-18) contrasts against methods relying on DMD, implying DMD is not used. Rephrase to specify DMD is only for distillation, not AR training.
- **[99bb5e822075] (severity: writing)** The Broader Impacts section (Conclusion) states the infrastructure 'involves no negative social implications,' which is inadequate for a video generation system. Expand to explicitly discuss dual-use risks (deepfakes, misinformation) and mitigation strategies.
- **[53dcee6f7971] (severity: writing)** No discussion of training data provenance or consent. The dataset section (Appendix) describes 120K videos but does not address whether subjects consented to inclusion or if copyrighted material was used. Add data sourcing and privacy considerations.
- **[fa805b309554] (severity: writing)** No content safety measures are described. Video generation models require safeguards against harmful content generation. Include discussion of safety filters or content moderation approaches in deployment.
- **[d77d61dcd791] (severity: science)** Provide standard deviations for VBench scores (Tables 2, 3) to establish statistical significance of quality gains.
- **[ef5966277535] (severity: science)** Control for resolution differences in Table 2 (1280x720 vs 832x480) to isolate model performance from resolution effects.
- **[85eca87e8137] (severity: science)** Quantify PTQ vs Pre-trained NVFP4 quality gap in Appendix with metrics like LPIPS/FID rather than qualitative descriptions.
- **[ecf997d27e38] (severity: science)** Report standard deviations or confidence intervals for VBench scores in Tables 2 and 3 to quantify variance across seeds.
- **[801dcb36a8e8] (severity: science)** Explicitly state the number of evaluation samples (N) and inference random seeds used for benchmark metrics.
- **[813f820d116e] (severity: science)** Apply statistical significance tests (e.g., t-tests) to validate performance claims over baselines.
- **[b840c5f7d5ea] (severity: writing)** In sec/04_algo.tex and sec/05_experiment.tex, move all \caption commands inside their respective \begin{table} environments. LaTeX requires captions to be within float environments to function correctly (e.g., line 10 of sec/04_algo.tex).
- **[36e304f92d6d] (severity: writing)** In sec/05_experiment.tex, move the \section{Experimental Results} header to precede the tables it introduces. Currently, tables appear before the section title (line 1 vs line 100), breaking document flow.
- **[6330e835a43a] (severity: writing)** Correct the article error in the Conclusion: change 'a algorithm-infrastructure co-design system' to 'an algorithm-infrastructure co-design system'.
- **[4d7fc05b0e0a] (severity: writing)** Break down the first sentence of the Abstract, which is overly complex. It currently combines method name, instantiation, rationale, and mechanism into one clause.
- **[fd4634775a13] (severity: writing)** Improve formality in Section 5.1 and Introduction. Use 'yields/achieves' and 'In this work' respectively.
- **[48a311efc27f] (severity: writing)** Fix formatting in Section 2.2: Variable definitions following Equation (2) are separated by a blank line. Remove the break to maintain mathematical context.
- **[deeb4f4aca56] (severity: writing)** Reduce repetition in the Abstract and Introduction. Avoid repeating 'model' and 'AR training' in close proximity.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 35 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
