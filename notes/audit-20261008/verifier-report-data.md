# Verify reports against their underlying data (2026-10-09)

The fresh canary's task-verifier cache accepted T013 because `docs/research.md` contained a methods section, a supposedly reproduced CSV excerpt, and a figure caption. Its table actually claimed 2002 zero residues for N=10000,p=5 while the CSV contained 3452. `gather_evidence` only supplied the report named by the task, so it could not substantiate its own measurements.

Report/document and directory-output tasks now receive the same bounded CSV/JSON/TSV data context used by implementation. The verifier explicitly compares reported values/trends with underlying evidence; report prose does not prove execution or test success. Data content hashes participate in the existing evidence cache, invalidating accepted reports when backing data changes. Plain source-library tasks do not acquire unrelated data dependencies.

Validation: 32 focused checks pass, including report-data delivery, cache invalidation, absence of data, and isolation of plain library tasks. A live GPT-OSS review of the actual unchanged canary report rejects it in 5.237 seconds and names the exact 2002-vs-3452 contradiction (`verifier-report-live.json`). The probe did not modify scientific artifacts, task statuses, or verification caches.

Related to #1139. This corrects an observed false task acceptance; it is not full scientific or paper acceptance.
