# Gate external reference availability where its behavior changes

On 2026-10-09, unrelated PRs #1532, #1533 and #1534 hit the same live Zenodo 30-second ReadTimeout. In #1534 the first attempt failed two real-call assertions, then the purported offline suite also failed `test_dataset_sources.py::test_datacite_resolves_doi` (7,423 other unit tests passed). One unchanged-head retry again failed only the mixed-reference Zenodo assertion, while the standalone DOI and 24 other live tests passed. Two targeted local real checks (Zenodo reference + DataCite dataset DOI) passed in 40.56s. This is observed availability coupling, not evidence to loosen citation verification.

## Policy

- Primary Dartmouth runtime calls and live source contracts remain required for relevant runtime PRs.
- Existing external reference/citation assertions run in their own required job when reference dependencies, their tests, schemas/fixtures, shared configuration or dependency manifests change. Unknown paths, incomplete/truncated change lists and relevant renames select the external job conservatively. Manual dispatch selects all jobs.
- Known unrelated runtime changes and reviewed CI routing/audit files do not require external registrar uptime. CI routing changes instead retain offline selection/import/collection regressions and actual primary Dartmouth calls. This exception validates the changed routing; it never bypasses a changed reference implementation's live gate.
- The full nightly suite remains unchanged and includes every external check.

The dependency guard walks static local imports (including function-local `agents.tools.citation_fetcher` and package initialization) of the selected external test modules. This exposed additional grounding/fill/results/backend dependencies beyond the obvious librarian/reference files; their changes still select the external gate. `web/about.html` is also covered because `config.py` reads the citation-overlap threshold there. Conservative directory prefixes include more code than the observed import closure.

Six existing dataset-service tests were misplaced under `tests/unit/` and made real HF/Figshare/Zenodo/DataCite/OpenML calls even with `LLMXIVE_REAL_TESTS` unset. They move intact to `tests/real_call/test_dataset_source_services.py`: AST comparison verifies all six bodies/assertions unchanged. Four deterministic dataset-intent/aggregation tests remain in the unit suite. No resolver, citation gate, status classification, timeout, endpoint, identifier or success assertion changes.

## Validation

94 focused offline tests pass, covering CI selection, actual pytest collection, citation guards, positive reference gates, repair behavior, dataset intent extraction and format sniffing. The actual workflow commands partition all 37 fast real-call cases exactly into 16 runtime + 21 external cases, without overlap or loss; the configured primary-model test and live contracts stay in the runtime job. Full nightly command remains `pytest tests/real_call -v`. Empty/truncated metadata, renamed reference code, unknown paths and dependency manifests retain the external gate. Actionlint, Ruff and diff checks pass. Remote exact-head CI remains pending.
