# Manual Curation Guide for Heusler Alloy Hysteresis Data

## Purpose
This guide provides step-by-step instructions for researchers to manually extract magnetic hysteresis data from scientific PDFs and format it into `data/raw/manual_curated.csv`. This manual path is critical when automated fetchers (T016, T017) fail to retrieve data from NIST or journal supplements.

## Prerequisites
- Access to scientific PDFs containing Heusler alloy magnetic hysteresis data (e.g., from Acta Materialia, Journal of Alloys and Compounds).
- A text editor or spreadsheet application to edit the CSV file.
- Knowledge of the required schema (see `specs/001-predict-heusler-hysteresis/contracts/alloy_entry.schema.yaml`).

## Step 1: Identify Relevant Data
1. Open the PDF and locate tables or figures reporting:
 - **Composition**: The chemical formula of the Heusler alloy (e.g., `Co2MnGa`, `Ni2MnSn`).
 - **Coercivity**: Magnetic coercivity (usually in Oe or A/m).
 - **Saturation Magnetization**: Saturation magnetization (usually in emu/g or A·m²/kg).
 - **Synthesis Method**: How the alloy was prepared (e.g., Arc Melting, Sputtering).
2. Ensure the data is **experimental** (not DFT/simulation). Discard entries labeled "Calculated", "Simulated", or "DFT".

## Step 2: Extract and Normalize Data
1. **Composition**: Write the formula exactly as it appears (e.g., `Co2MnGa`). Do not convert to atomic fractions; this will be done automatically by the pipeline.
2. **Coercivity**: Convert to **Oe** if necessary.
 - If in A/m: `Oe = A/m / 79.5775`
 - If in mT: `Oe = mT / 0.1`
3. **Saturation Magnetization**: Convert to **emu/g** if necessary.
 - If in A·m²/kg: `emu/g = A·m²/kg` (1:1 conversion)
 - If in emu/cm³: `emu/g = (emu/cm³) / density` (estimate density ~8 g/cm³ if unknown, but note this limitation).
4. **Synthesis Method**: Use standard terms: `Arc Melting`, `Sputtering`, `Evaporation`, `Melt Spinning`, `Annealed`.

## Step 3: Populate the CSV
1. Open `data/raw/manual_curated.csv` in a spreadsheet editor or text editor.
2. Add a new row for each data point with the following columns:
 - `composition`: String (e.g., `Co2MnGa`)
 - `coercivity_oe`: Number (float)
 - `saturation_magnetization_emu_g`: Number (float)
 - `source_type`: Must be `Manual`
 - `synthesis_method`: String (e.g., `Arc Melting`)
 - `doi`: Optional (if available, e.g., `10.1016/j.actamat.2020.01.001`)
 - `crystal_structure`: Optional (e.g., `L2_1`, `B2`, `A2`)
3. **Example Row**:
 ```csv
 Co2MnGa,45.5,110.2,Manual,Arc Melting,10.1016/j.actamat.2020.01.001,L2_1
 ```

## Step 4: Validate Before Ingestion
1. Ensure no empty rows or missing required fields (`composition`, `coercivity_oe`, `saturation_magnetization_emu_g`, `source_type`, `synthesis_method`).
2. Run the validation script (see Step 5) to check for schema compliance.
3. Save the file as `data/raw/manual_curated.csv` (UTF-8 encoding, no BOM).

## Step 5: Run Validation
Execute the following command to validate the CSV against the schema:
```bash
python code/tests/unit/test_manual_curation_validation.py
```
- If validation passes, the data is ready for ingestion (T018).
- If validation fails, correct the errors in the CSV and re-run.

## Important Notes
- **Do not** include DFT or simulated data.
- **Do not** fabricate data. Only enter values explicitly reported in the source.
- If a value is missing in the source, leave the field empty (the pipeline will handle imputation per FR-002).
- Ensure `source_type` is exactly `Manual` (case-sensitive).

## Troubleshooting
- **Error: "Invalid composition format"**: Ensure the composition string contains only element symbols and integers (e.g., `Co2MnGa` is valid; `Co2 Mn Ga` is not).
- **Error: "Missing required field"**: Check that all required columns are present and non-empty.
- **Error: "Unit mismatch"**: Verify that coercivity is in Oe and saturation magnetization is in emu/g.

## References
- Schema Definition: `specs/001-predict-heusler-hysteresis/contracts/alloy_entry.schema.yaml`
- Task T018: Manual Curator Implementation
- Task T063: Enhanced Manual Curation Workflow
