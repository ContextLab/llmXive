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

## Step 4: Handling Ambiguous Data Points (CRITICAL)
When extracting data, you may encounter ambiguous or missing values. Follow these strict rules to ensure data integrity:

### Ambiguous Value: "Not Measurable" or "N/A"
- **Action**: Leave the cell **empty** (do not write "N/A", "null", or "0").
- **Reasoning**: The pipeline's imputation logic (T024) handles missing data. Writing "0" or "N/A" as a string will cause parsing errors or incorrect imputation.
- **CSV Example**: `Co2MnGa,,110.2,Manual,Arc Melting,,L2_1` (Note the empty field between commas for coercivity).

### Ambiguous Value: "Zero" or "< Limit"
- **Action**: If the text explicitly states "zero" or "unmeasurable" (implying no magnetic hysteresis), enter `0.0`.
- **Action**: If the text states "< 5 Oe" (below detection limit), enter `2.5` (the midpoint) or `5.0` (the limit) and add a comment in a separate log if possible. For this CSV, use the limit value `5.0` and ensure `synthesis_method` is accurate.
- **CSV Example**: `Ni2MnSn,0.0,95.0,Manual,Sputtering,,`

### Ambiguous Value: "Variable Thickness" or "Range"
- **Action**: If the data reports a range (e.g., "Coercivity: 50-100 Oe"), enter the **average** of the range (`75.0`).
- **Action**: If the data depends on thickness and no single value is given, **do not include this entry** unless the thickness is specified in a separate column (which this schema does not support). Skip the entry.
- **CSV Example**: `CoFeAl,75.0,100.0,Manual,Evaporation,,` (Assuming 50-100 Oe range).

### Ambiguous Value: Missing Unit
- **Action**: If the unit is not specified, assume the standard unit for the journal (usually Oe for coercivity, emu/g for magnetization in materials science).
- **Action**: If you cannot determine the unit, **do not include the entry**.
- **Verification**: Check the figure caption or table header in the PDF.

## Step 5: Specific Examples of Valid CSV Entries
The following examples demonstrate correct formatting for various scenarios based on the schema.

### Example 1: Standard Entry
```csv
composition,coercivity_oe,saturation_magnetization_emu_g,source_type,synthesis_method,doi,crystal_structure
Co2MnGa,45.5,110.2,Manual,Arc Melting,10.1016/j.actamat.2020.01.001,L2_1
```

### Example 2: Entry with Missing Coercivity (Not Measurable)
```csv
composition,coercivity_oe,saturation_magnetization_emu_g,source_type,synthesis_method,doi,crystal_structure
Ni2MnSn,,95.0,Manual,Sputtering,10.1016/j.jallcom.2019.05.001,B2
```
*Note: The empty field between commas represents a missing value.*

### Example 3: Entry with Zero Coercivity
```csv
composition,coercivity_oe,saturation_magnetization_emu_g,source_type,synthesis_method,doi,crystal_structure
Fe3Al,0.0,85.0,Manual,Melt Spinning,,A2
```

### Example 4: Entry with Range Averaged
```csv
composition,coercivity_oe,saturation_magnetization_emu_g,source_type,synthesis_method,doi,crystal_structure
CoMnSi,75.0,130.0,Manual,Evaporation,,B2
```
*Note: Original text said "Coercivity 50-100 Oe". Average is 75.0.*

### Example 5: Entry with Limit Value
```csv
composition,coercivity_oe,saturation_magnetization_emu_g,source_type,synthesis_method,doi,crystal_structure
NiMnSb,5.0,105.0,Manual,Arc Melting,10.1016/j.jmmm.2018.03.002,L2_1
```
*Note: Original text said "< 5 Oe". Using 5.0 as the limit value.*

## Step 6: Validate Before Ingestion
1. Ensure no empty rows or missing required fields (`composition`, `coercivity_oe`, `saturation_magnetization_emu_g`, `source_type`, `synthesis_method`).
 - **Exception**: `coercivity_oe` may be empty if "Not Measurable" (see Step 4).
2. Run the validation script (see Step 7) to check for schema compliance.
3. Save the file as `data/raw/manual_curated.csv` (UTF-8 encoding, no BOM).

## Step 7: Run Validation
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
- **Critical**: Do not write "N/A", "null", or "NaN" in the CSV. Use an empty field (e.g., `,,`) for missing values.

## Troubleshooting
- **Error: "Invalid composition format"**: Ensure the composition string contains only element symbols and integers (e.g., `Co2MnGa` is valid; `Co2 Mn Ga` is not).
- **Error: "Missing required field"**: Check that all required columns are present and non-empty (except for allowed missing coercivity).
- **Error: "Unit mismatch"**: Verify that coercivity is in Oe and saturation magnetization is in emu/g.
- **Error: "Invalid value for coercivity_oe"**: Ensure the value is a number or empty. Do not use strings like "N/A".

## References
- Schema Definition: `specs/001-predict-heusler-hysteresis/contracts/alloy_entry.schema.yaml`
- Task T018: Manual Curator Implementation
- Task T063: Enhanced Manual Curation Workflow
- Spec FR-002: Imputation Strategy (Mean Imputation/Listwise Deletion)