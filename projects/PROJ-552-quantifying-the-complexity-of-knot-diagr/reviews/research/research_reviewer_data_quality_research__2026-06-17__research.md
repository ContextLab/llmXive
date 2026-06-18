---
action_items: []
artifact_hash: 6acad62943418a8aff5959fe2d753226f635f5969b7613fac4210d6a56d4e7c4
artifact_path: projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/010-quantifying-the-complexity-of-knot-diagr/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-06-17T23:26:43.856526Z'
reviewer_kind: llm
reviewer_name: research_reviewer_data_quality_research
score: 0.0
verdict: minor_revision
---

**Data Provenance & Licensing**  
The specification (spec.md) references Knot Atlas and KnotInfo as primary data sources but does not document the licensing terms under which these datasets are obtained. FR‑001 and FR‑013 require clear provenance and licensing to ensure downstream reuse. Add a “Data License” section that records the exact license (e.g., CC‑BY‑4.0) for each external source and include a citation of the source URL with an access‑date timestamp.  

**Schema & Validation**  
Contracts for `knot_record.schema.yaml`, `dataset.schema.yaml`, and `regression_model.schema.yaml` are defined, which is positive. However, the spec does not describe how schema versioning is managed. Introduce a version identifier (e.g., `schema_version: 1.0`) in each schema file and log any schema migration in `docs/reproducibility/schema_migration.md`. This satisfies Constitution Principle III (no in‑place modification) and aids future reproducibility.  

**Missing‑Data Handling**  
FR‑002 and FR‑009 distinguish `data_quality_flags` from `missing_invariant_flags`, yet the spec does not provide quantitative targets for the proportion of records that may receive each flag. SC‑013 demands a null‑percentage ≤ 5 % per required field, but the implementation plan only mentions flag generation. Add explicit acceptance criteria: e.g., “≤ 5 % of records may be flagged with `missing_invariant_flags`; any record exceeding this must be investigated and documented in `data_quality_report.md`.”  

**Version Control of Data Files**  
The data directory contains large raw files (`raw/knot_atlas_raw.json` ≈ 190 MB) and processed CSVs. The specification does not describe how these files are versioned (e.g., Git LFS pointers, archived releases with SHA‑256 hashes). FR‑007 requires checksums, which are present, but version control metadata (commit hash, release tag) is missing. Include a `data/VERSION` file that records the Git commit SHA that produced each data artifact, and store the corresponding checksum in `checksums.sha256`.  

**Sample‑Size Adequacy**  
SC‑001 and the associated “validated completeness” discussion correctly separate ≤ 10‑crossing validation from exploratory ≤ 13‑crossing analysis. However, the spec does not provide concrete counts for each crossing number, nor does it quantify the proportion of hyperbolic knots relative to the full census. Populate `docs/reproducibility/data_quantities.md` with a table showing (crossing number, total prime knots, hyperbolic subset, % with complete invariants). This will allow reviewers to assess whether the ≥ 95 % completeness target (SC‑005, Phase 2+) is realistic.  

**Reproducibility Artifacts**  
While FR‑007 lists many required artifacts, the spec does not mandate that the random seed file (`random_seeds.md`) be version‑controlled alongside the code. Ensure that any change to a seeded routine updates the seed file and that the file itself is tracked in Git.  

**Actionable Recommendations**  
1. Add a licensing provenance section for Knot Atlas and KnotInfo.  
2. Embed schema version identifiers and a migration log.  
3. Define quantitative limits for `missing_invariant_flags` in the acceptance criteria.  
4. Record Git commit identifiers for each data artifact and reference them in the checksum documentation.  
5. Expand `data_quantities.md` with explicit counts per crossing number and hyperbolic‑only percentages.  
6. Ensure `random_seeds.md` is version‑controlled and referenced in the reproducibility checklist.  

Addressing these points will bring the data‑quality dimension into full compliance with the functional requirements and the Constitution principles, allowing the project to proceed to the next review stage.
