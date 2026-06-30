# Revision Specification: Research Revision (writing) — PROJ-261-evaluating-the-impact-of-code-duplicatio round 3

**Generated**: 2026-06-30T16:49:25.807177+00:00
**Kind**: research_writing
**Project**: PROJ-261-evaluating-the-impact-of-code-duplicatio
**Round**: 3

## Input

Address the following reviewer-raised action items:

- **[00aa12e5c68e] (severity: writing)** Split code/bug_detection.py: Refactor projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/bug_detection.py into code/bug_detection/evaluator.py (logic) and code/bug_detection/results.py (output formatting) to reduce file size below 200 lines and prevent truncation.
- **[d80bfbb9db99] (severity: writing)** Fix code/model_metrics.py: Ensure projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/model_metrics.py actually computes and writes data/processed/perplexity_scores.csv. Remove any logic that generates simulated/fabricated data.
- **[af4a725d7cda] (severity: writing)** Align File Structure: Rename projects/PROJ-261-evaluating-the-impact-of-code-duplication/visualization/plotting.py to projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/visualization.py to match plan.md, or update plan.md to reflect the new directory structure.
- **[ba483ebff310] (severity: writing)** Add Missing Tests: Create the projects/PROJ-261-evaluating-the-impact-of-code-duplication/tests/ directory and implement the unit and integration tests listed in tasks.md (T012-T052) to verify the pipeline's correctness.
- **[ae428a7017f7] (severity: writing)** Reduce code/config.py: Move logic and hardcoded data out of projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/config.py into appropriate modules (e.g., code/data_loader.py, code/ast_cloner.py) to ensure it remains a pure configuration file.
- **[fb2076cdf3e1] (severity: writing)** Implement Semantic Distance Calculation: Create code/semantic_cloner.py (or extend code/model_metrics.py as per T053) to compute embedding-based similarity for AST nodes or token sequences. Update data/processed/clone_metrics.csv schema to include a semantic_distance column and ensure the pipeline actually computes this for the 500MB corpus, not just syntactic clone density.
- **[46948685e4f4] (severity: writing)** Generate Structural Heat Map: Implement the logic in code/visualization.py to map perplexity spikes to specific AST node types (e.g., function headers vs. bodies) and generate the required heat map/confusion matrix. Save this artifact to data/analysis/figures/structural_heatmap.png (and PDF) as required by User Story 3.
- **[e66548df57f8] (severity: writing)** Execute Real Pipeline: Re-run the full pipeline on the 500MB subset to replace the "fabricated" results with real measurements. Ensure data/processed/perplexity_scores.csv and data/analysis/correlation_results.csv contain actual data (not just headers) derived from the Salesforce/codegen-350M-mono model inference.
- **[b40a00e03f45] (severity: writing)** Re-run the full data processing pipeline (main.py) to ensure data/processed/perplexity_scores.csv is generated with at least 1000 rows of valid perplexity scores corresponding to the code segments.
- **[87039b63ddf6] (severity: writing)** Re-run the clone detection module (ast_cloner.py) to populate data/processed/clone_metrics.csv with at least 1000 rows of valid clone density metrics, ensuring the file size reflects actual data content (not just headers).
- **[6ad4a0e2b923] (severity: writing)** Execute the PII scanning task (pii_scanner.py) against data/raw/ and data/processed/ directories, and generate a log file (e.g., data/pii_scan_results.csv or update data/parse_failures.csv) explicitly documenting any PII patterns found or confirming a clean scan, as required by FR-009.
- **[0b65cd15ecca] (severity: writing)** Verify and re-compute checksums for all newly generated data files using checksum_manifest.py to ensure the artifact_hashes state manifest reflects the actual content of the real, non-fabricated output files.
- **[ad310aad5a64] (severity: writing)** Re-run the correlation analysis (correlation_analysis.py) only after valid input files are confirmed, ensuring data/analysis/correlation_results.csv contains statistically valid Spearman coefficients and p-values derived from the real data.
- **[2b5a9fba6b2d] (severity: writing)** Create projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/processed/perplexity_scores.csv containing the actual token-level perplexity measurements for the processed code segments, ensuring it is checksummed and recorded in the artifact_hashes manifest.
- **[ed49b56020a3] (severity: writing)** Replace projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/analysis/bug_detection_summary.json with projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/processed/bug_detection_results.csv containing the pass@1 accuracy results, ensuring the file is checksummed and recorded in the artifact_hashes manifest.
- **[7db535065ecf] (severity: writing)** Update projects/PROJ-261-evaluating-the-impact-of-code-duplication/docs/reproducibility/hyperparameters.md to explicitly list the random seeds, clone detection thresholds (0.7, 0.8, 0.9), and all configuration parameters used in config.py to satisfy SC-005.
- **[be08cf678847] (severity: writing)** Consolidate projects/PROJ-261-evaluating-the-impact-of-code-duplication/utils/checksum_visualizations.py and projects/PROJ-261-evaluating-the-impact-of-code-duplication/visualization/plotting.py into the single file projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/visualization.py as defined in plan.md, removing the redundant files.
- **[3b6b91934262] (severity: writing)** specs/001-evaluate-code-duplication-llm-understanding/spec.md: Revise FR-006 and FR-007 to explicitly define the unit of analysis. Either:
- **[2525d24e62f5] (severity: writing)** specs/001-evaluate-code-duplication-llm-understanding/spec.md: In FR-003, replace the vague "embedding similarity of AST nodes" with a specific, reproducible method (e.g., "Use CodeBERT to generate embeddings for the tokenized text of each AST node, then compute cosine similarity").
- **[070a7fb7fa22] (severity: writing)** specs/001-evaluate-code-duplication-llm-understanding/spec.md: Add a "Data Joining Strategy" section in the Requirements or User Stories that explicitly describes the key (e.g., problem_id) and the aggregation logic used to merge segment-level metrics with problem-level accuracy scores.
- **[d82f08dee349] (severity: writing)** Complete the data processing pipeline in projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/main.py and code/model_metrics.py to successfully stream the 500MB corpus, compute perplexity for at least 1000 segments, and generate data/processed/perplexity_scores.csv with valid numeric data (not just headers).
- **[ef6eb5628750] (severity: writing)** Implement and execute the bug detection module in projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/bug_detection.py to process the HumanEval subset and generate data/processed/bug_detection_results.csv with pass@1 accuracy metrics.
- **[ff82005c2334] (severity: writing)** Verify and populate data/processed/clone_metrics.csv by ensuring code/ast_cloner.py successfully parses the corpus and computes clone density for the required number of segments, resulting in a file with >25 bytes of actual data rows.
- **[2af65c9d2998] (severity: writing)** Re-run the correlation analysis in projects/PROJ-261-evaluating-the-impact-of-code-duplication/code/correlation_analysis.py using the newly generated valid input files to produce a non-empty data/analysis/correlation_results.csv with actual Spearman coefficients and p-values.
- **[ac53e7e70886] (severity: writing)** Remove all simulated/fabricated result signals from the execution logs and ensure the data/ directory contains only real, reproducible measurements derived from the actual code execution.
- **[ecc6e3b36831] (severity: writing)** "Execute the full pipeline on the 500MB corpus and verify that data/processed/clone_metrics.csv contains at least 1000 rows of valid data (matching SC-003) and data/processed/perplexity_scores.csv is generated with corresponding perplexity values."
- **[062b03068b60] (severity: writing)** "Debug and fix the silent failure in code/main.py or code/ast_cloner.py that results in empty output files, ensuring that the data loading (T018) and clone detection (T019) steps actually process the streamed dataset."
- **[f874f3777708] (severity: writing)** "Implement and verify the perplexity calculation logic in code/model_metrics.py to ensure it loads the Salesforce/codegen-350M-mono model and writes valid log-probability outputs to data/processed/perplexity_scores.csv."
- **[58ce92d05c6b] (severity: writing)** "Run the PII scanner (code/pii_scanner.py) on the generated data files and ensure data/parse_failures.csv and the checksum manifest (code/checksum_manifest.py) are updated with valid entries for all non-empty output files."


## Success Criterion

After the implementer applies this revision, the project returns to
``research_review`` and the per-specialist re-review protocol confirms
each of the 29 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
