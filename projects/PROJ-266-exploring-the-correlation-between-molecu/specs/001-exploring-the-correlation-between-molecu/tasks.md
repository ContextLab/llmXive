# Tasks: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes  

**Inputs**: `spec.md`, `plan.md`, existing contracts in `specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/`  

**Goal**: End‑to‑end, reproducible research pipeline that satisfies every functional requirement (FR‑001 … FR‑010) and success criteria (SC‑001 … SC‑006).  

---

## Phase 1 – Project Infrastructure & Validation  

- [ ] **T001** [US0] Create the canonical project directory layout.  
  *Create `code/`, `tests/`, `data/raw/`, `data/processed/`, `specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/`, and `state/pending/` directories.*  
  *Verification:* Run the provided `scripts/setup_dirs.py` and assert that each directory exists (e.g., `assert os.path.isdir("data/raw")`).  

- [ ] **T002** [US0] Add linting and formatting configuration files.  
  *Create a `.flake8` file with reasonable defaults and a `pyproject.toml` that enables Black (line‑length 88) and is referenced by the CI runner.*  
  *Verification:* `flake8 --config .flake8 .` and `black --check .` must both exit with status 0.  

- [ ] **T003** [US0] Implement a checksum utility (`code/utils/checksum.py`).  
  *The script walks `data/` recursively, computes SHA‑256 for every file, and writes a YAML mapping to `state/pending/checksums.yaml`.*  
  *Verification:* After any data‑producing task runs, re‑execute the utility and confirm that the YAML file contains a key for the newly created file and that the stored hash matches a freshly computed hash.  

- [ ] **T004** [US0] Create the JSON‑schema contracts required by the specification.  
  *Write the following files (exact paths required):*  
  *`specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/dataset.schema.yaml`* (matches **FR‑001**, **FR‑010**)  
  *`specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/descriptor.schema.yaml`* (matches **FR‑004**)  
  *`specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/analysis_output.schema.yaml`* (matches **FR‑006**, **FR‑007**, **FR‑008**)  
  *`specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/correlation.schema.yaml`* (additional contract)  
  *`specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/flexibility.schema.yaml`* (additional contract)  
  *`specs/001‑exploring‑the‑correlation‑between‑molecu/contracts/output.schema.yaml`* (additional contract)  
  *Verification:* Run `pytest tests/contract/test_schema_validity.py` – the test loads **all** schema files and validates a minimal compliant instance for each.  

---

## Phase 2 – Data Acquisition & Pre‑processing  

- [ ] **T005** [US1] Implement the data‑retrieval script (`code/data/retrieval.py`).  
  *Fetch ≥ 600 Caco‑2 records from the ChEMBL REST API using the query parameters `assay_type=caco‑2` and `standard_type=MEASUREMENT`.*  
  *Save the raw CSV to `data/raw/chembl_caco2_raw.csv` (schema must conform to `dataset.schema.yaml`).*  
  *Implement exponential back‑off (max 3 retries, 5 s delay) for HTTP 429 responses.*  
  *After saving, invoke the checksum utility (T003).*  
  *Verification:* After execution, `data/raw/chembl_caco2_raw.csv` exists, contains ≥ 600 rows, and `state/pending/checksums.yaml` includes a hash entry for it.  

- [ ] **T006** [US1] Implement the preprocessing script (`code/data/preprocessing.py`).  
  *Read `data/raw/chembl_caco2_raw.csv`, filter out rows with NULL SMILES or NULL logPapp, and retain only records where `protocol_metadata.standard_type == "MEASUREMENT"`.*  
  *Report the pass‑rate (valid / raw) and the count of records excluded due to protocol heterogeneity.*  
  *Write the cleaned dataset to `data/processed/filtered_data.csv` (must still conform to `dataset.schema.yaml`).*  
  *Invoke the checksum utility (T003) after writing.*  
  *Verification:* `data/processed/filtered_data.csv` contains ≥ 500 rows; the script prints a pass‑rate ≥ 0.83 and the checksum file contains an entry for the filtered CSV.  

- [ ] **T007** [US1] Add a contract‑test for the filtered dataset.  
  *Create `tests/contract/test_dataset.py` with a single test function `test_schema_compliance` that loads `data/processed/filtered_data.csv` and validates each record against `dataset.schema.yaml` using `jsonschema.validate`.*  
  *Verification:* `pytest tests/contract/test_dataset.py` exits with status 0.  

- [ ] **T021** [US1] Measure total pipeline runtime (SC‑005).  
  *Wrap the full pipeline execution (tasks T005 → T020) in a timing script that writes total elapsed seconds to `data/processed/runtime_seconds.txt`.*  
  *Verification:* The script asserts that the recorded runtime ≤ 21600 seconds (6 h) and fails otherwise.  

---

## Phase 3 – Feature Engineering (Physicochemical & Flexibility Descriptors)  

- [ ] **T008** [US2] Compute physicochemical confounders and a complexity metric.  
  *Read `data/processed/filtered_data.csv`; for each SMILES compute:*  
  – LogP (`MolLogP`)  
  – Molecular weight (`MolWt`)  
  – Polar surface area (`CalcTPSA`)  
  – Number of rotatable bonds (`NumRotatableBonds`)  
  *Add these columns (`logP`, `mw`, `psa`, `rotatable_bonds`) and a derived `size_normalized_flexibility = dihedral_variance / rotatable_bonds` placeholder column (to be filled later).*  
  *Write the enriched table to `data/processed/enriched_data.csv` and invoke the checksum utility.*  
  *Verification:* The CSV contains the new columns with non‑null numeric values for every row; checksum entry exists.  

- [ ] **T009** [US2] Generate 3‑D conformer ensembles (`code/data/conformer_gen.py`).  
  *For each SMILES in `data/processed/enriched_data.csv`, generate up to 50 conformers with RDKit’s `EmbedMultipleConfs` (seed = 42 for determinism).*  
  *Retain only conformers whose MMFF94 energy is ≤ 10 kcal/mol above the minimum energy conformer for that molecule.*  
  *Store the full ensemble as a dictionary `{smiles: list_of_rdkit_mol_objects}` serialized with `pickle` to `data/processed/conformers.pkl`.*  
  *Invoke the checksum utility after writing.*  
  *Verification:* `data/processed/conformers.pkl` exists, can be un‑pickled, and contains ≥ 450 molecules each with **≥ 50** conformers after energy filtering.  

- [ ] **T022** [US2] Compute and record conformer‑generation success‑rate (SC‑002).  
  *After T009 completes, calculate the proportion of molecules that met the ≥ 50‑conformer criterion and write the percentage to `data/processed/conformer_success_rate.txt`.*  
  *Verification:* The file exists and the recorded rate is ≥ 90 % (the threshold implied by the specification).  

- [ ] **T010** [US2] Calculate flexibility descriptors (`code/data/descriptors.py`).  
  *Load `data/processed/conformers.pkl`.*  
  *For each molecule:*  
  1. Select the lowest‑energy conformer.  
  2. Export to XYZ and run `pyvib.analyze_molecule` (PyVib must be importable).  
  3. Extract dihedral‑angle eigenvalue variance → **dihedral_variance** (rad²).  
  4. Compute bond‑length variance (**bond_variance**) and angle‑variance (**angle_variance**) as diagnostics.  
  5. Record `conformer_count` and a boolean `converged` flag (variance change < 1 % between successive 10‑conformer subsets).  
  *Skip any molecule where PyVib fails; log the SMILES to `logs/descriptor_failures.log`.*  
  *Write a CSV `data/processed/descriptors_raw.csv` with columns:* `smiles, dihedral_variance, bond_variance, angle_variance, conformer_count, converged`.  
  *Enforce the **FR‑003** success threshold: if fewer than 450 valid descriptor rows are produced, abort with a clear error message.*  
  *Invoke the checksum utility.*  
  *Verification:* The CSV contains ≥ 450 rows, all numeric fields are non‑negative, and the checksum file records the new artifact.  

---

## Phase 4 – Statistical Analysis & Modeling  

- [ ] **T011** [US2] Perform diagnostic bivariate correlations (`code/data/analysis.py`).  
  *Read `data/processed/descriptors_raw.csv` and `data/processed/enriched_data.csv` (joined on SMILES).*  
  *Compute Pearson and Spearman correlation coefficients (and raw p‑values) between each flexibility descriptor (`dihedral_variance`, `bond_variance`, `angle_variance`) and the permeability outcome `logPapp`.*  
  *Save results to `data/processed/correlation_diagnostic.csv` with columns:* `descriptor, pearson_r, pearson_p, spearman_r, spearman_p`.  
  *Verification:* The CSV exists and contains exactly three rows (one per descriptor).  

- [ ] **T012** [US2] Apply Benjamini‑Hochberg FDR correction to the diagnostic correlations.  
  *Read `data/processed/correlation_diagnostic.csv`, compute q‑values for the six p‑values (three descriptors × two methods) using `statsmodels.stats.multitest.multipletests` (α = 0.05, method = "fdr_bh").*  
  *Append a `fdr_q` column to the CSV and overwrite the file.*  
  *Verification:* The updated CSV now contains a `fdr_q` column; all q‑values are ≤ 1.0.  

- [ ] **T013** [US2] Compute the controlled partial correlation (`code/data/analysis.py`).  
  *Using the enriched dataset, calculate the partial correlation between `dihedral_variance` and `logPapp` while controlling for `logP`, `mw`, and `psa` (e.g., via `pingouin.partial_corr`).*  
  *Write a single‑row CSV `data/processed/correlation_controlled.csv` with columns:* `method, r, p_value, q_value, associational_only` (the last column must be `true`).  
  *Verification:* File exists, contains the required columns, and `associational_only` is set to `true`.  

- [ ] **T014** [US3] Build and evaluate a multivariate linear regression model (`code/data/analysis.py`).  
  *Features:* `dihedral_variance`, `logP`, `mw`, `psa`.  
  *Target:* `logPapp`.  
  *Perform 5‑fold cross‑validation (scikit‑learn’s `KFold` with `shuffle=True, random_state=42`).*  
  *Record per‑fold R², RMSE, MAE and compute their means and standard deviation of R².*  
  *Save a JSON file `data/processed/model_results.json` matching the `analysis_output.schema.yaml` contract (includes `model_performance` object).*  
  *Verification:* The JSON validates against the schema; `mean_r2` and `std_r2` are present.  

- [ ] **T015** [US3] Generate the primary visualization (`code/data/visualize.py`).  
  *Create a scatter plot of `dihedral_variance` vs `logPapp` with a regression line and a 95 % confidence interval (use `seaborn.regplot` with `ci=95`).*  
  *Add a subtitle “Associational Relationship – not causal” as required by **FR‑009**.*  
  *Save the figure as `data/processed/flexibility_vs_permeability.png` with DPI ≥ 300.*  
  *Verification:* The PNG file exists, its metadata reports `dpi=300`, and grepping the source file finds the phrase “Associational Relationship”.  

- [ ] **T016** [US3] Write an integration test that runs the full pipeline end‑to‑end (`tests/integration/test_full_pipeline.py`).  
  *The test executes the scripts in order (T005 → T006 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015) using subprocess calls.*  
  *After execution it asserts the existence of the key output artifacts:* `filtered_data.csv`, `descriptors_raw.csv`, `correlation_diagnostic.csv`, `model_results.json`, `flexibility_vs_permeability.png`.  
  *Verification:* `pytest -q tests/integration/test_full_pipeline.py` passes with exit code 0.  

---

## Phase 5 – Reporting & Handoff  

- [ ] **T017** [US3] Generate the computational‑method transparency report and update `research.md`.  
  *Run `code/utils/generate_transparency_report.py` which reads the execution logs, extracts key parameters (conformer count, energy window, descriptor definitions, statistical methods, CV metrics, confidence intervals), and writes a markdown section into `research.md`.*  
  *The report must include the exact values of the regression coefficients, mean R², and, if present, the scaling‑law exponent (the pipeline does **not** perform scaling‑law analysis; that section is omitted).*  
  *Verification:* Run `pytest tests/verification/test_transparency_report.py` which checks that `research.md` contains a top‑level heading “## Computational Method Transparency” and that required items are present.  

- [ ] **T023** [US0] Validate all JSON‑schema contracts.  
  *Create `tests/contract/test_schema_validity.py` that loads each schema file (`dataset.schema.yaml`, `descriptor.schema.yaml`, `analysis_output.schema.yaml`, `correlation.schema.yaml`, `flexibility.schema.yaml`, `output.schema.yaml`) and validates a minimal compliant instance against it using `jsonschema`.*
  *Verification:* `pytest tests/contract/test_schema_validity.py` exits with status 0.  

- [ ] **T024** [US0] Verify checksums file integrity.  
  *Create `tests/contract/test_checksums.py` that loads `state/pending/checksums.yaml`, ensures the file exists, and asserts that every file under `data/` listed in the pipeline has a corresponding SHA‑256 entry.*  
  *Verification:* `pytest tests/contract/test_checksums.py` exits with status 0.  

- [ ] **T025** [US0] Automated verification of the transparency report.  
  *Create `tests/verification/test_transparency_report.py` that parses `research.md` for the “## Computational Method Transparency” heading and checks for presence of required fields (conformer count, energy window, regression coefficients, mean R², confidence‑interval note).*
  *Verification:* `pytest tests/verification/test_transparency_report.py` exits with status 0.  

---

### Dependency Summary  

| Task | Depends on |
|------|------------|
| T001 | – |
| T002 | T001 |
| T003 | T001 |
| T004 | – |
| T005 | T001, T003, T004 |
| T006 | T005, T003, T004 |
| T007 | T006, T004 |
| T008 | T006, T004 |
| T009 | T008, T003, T004 |
| T010 | T009, T003, T004 |
| T011 | T010, T008, T004 |
| T012 | T011, T004 |
| T013 | T010, T008, T004 |
| T014 | T010, T008, T004 |
| T015 | T014, T004 |
| T016 | T005, T006, T008, T009, T010, T011, T012, T013, T014, T015, T004 |
| T017 | T014, T015, T016, T004 |
| T021 | T016, T004 |
| T022 | T009, T004 |
| T023 | T004 |
| T024 | T003, T004 |
| T025 | T017, T004 |

---  

*All tasks are expressed as real, verifiable actions that produce concrete files under the project‑owned `code/`, `data/`, `tests/`, or `specs/` trees. No synthetic data or GPU‑only shortcuts are used; every step is CPU‑tractable and respects the ≤ 6‑hour runtime budget.*  