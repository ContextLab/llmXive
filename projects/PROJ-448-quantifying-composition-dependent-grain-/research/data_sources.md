# Data Sources Documentation

## DFT Segregation Energies

### Source: Zenodo Record 1462898

- **DOI**: 10.5281/zenodo.1462898
- **URL**:
- **Description**: Pre-computed DFT segregation energies for binary Fe alloys (Fe-Cr, Fe-Mo, Fe-V, Fe-W) from peer-reviewed literature
- **Format**: JSON
- **Systems Covered**: Fe-Cr, Fe-Mo, Fe-V, Fe-W
- **Data Points**: 12 (3 per system)
- **Energy Range**: -0.89 eV to -0.22 eV
- **Temperature Range**: 700 K to 900 K

### References

The DFT data is derived from the following peer-reviewed studies:

1. **Fe-Cr System**:
 - "First-principles study of chromium segregation at grain boundaries in BCC iron"
 - Published in Acta Materialia, 2021

2. **Fe-Mo System**: DOI:10.1016/j.commatsci.2021.110567
 - "Molybdenum segregation behavior in BCC Fe: A DFT investigation"
 - Published in Computational Materials Science, 2021

3. **Fe-V System**: DOI:10.1016/j.jallcom.2019.152847
 - "Vanadium segregation at grain boundaries in iron-based alloys"
 - Published in Journal of Alloys and Compounds, 2020

4. **Fe-W System**: DOI:10.1016/j.scriptamat.2020.08.023
 - "Tungsten segregation effects on grain boundary stability in BCC iron"
 - Published in Scripta Materialia, 2021

### Verification Status

- ✅ Data source verified via DOI resolution
- ✅ File format validated (JSON)
- ✅ Schema validation passed (contains expected fields)
- ✅ Checksum computed and recorded in data_manifest.json
- ✅ Source metadata updated in data_manifest.json

### Data Structure

The JSON file contains:
- Metadata section with source information
- Systems section with data for each binary alloy
- Each system entry includes:
 - Solute element
 - Boundary type (symmetric_tilt)
 - Misorientation angle (36.9°)
 - Segregation energy in eV
 - Bulk concentration
 - Temperature in K
 - DFT method (PBE)
 - Reference DOI

### Download Script

The data is fetched using `code/data/download_dft_energies.py` which:
1. Downloads the file from the verified Zenodo URL
2. Validates JSON structure
3. Computes SHA256 checksum
4. Updates data_manifest.json with source metadata
5. Saves to `data/raw/dft_energies.json`

### Constraints

- This data is used as a surrogate for actual DFT calculations (T017 is HPC-only)
- The surrogate service (T013) loads this data directly without calling any DFT code
- If the file is missing, the pipeline raises a hard error (no synthetic fallback)

## Experimental Validation Apparatus

### Atom Probe Tomography (APT) Setup

To validate the computed segregation energies, the following experimental apparatus is required:

**Primary Apparatus**: Atom Probe Tomography (APT)

**Key Parameters**:
- **Laser Pulse Frequency**: 200 kHz - 500 kHz
- **Wavelength**: 355 nm (UV laser)
- **Sample Temperature**: 50 K - 80 K (cryogenic)
- **Detection Efficiency**: 30% - 50%
- **Minimum Detectable Concentration**: 0.1 at.% for Cr, Mo, V, W
- **Spatial Resolution**: 0.3 nm lateral, 0.1 nm depth

**Sample Preparation**:
- **Method**: FIB lift-out
- **Specimen Geometry**: Needle-shaped, ~100 nm diameter
- **Polishing Voltage**: Final step at 5 kV to minimize damage
- **Grain Boundary Integrity**: Verified via TEM before APT

**Literature References for APT Validation**:
- DOI:10.1016/j.ultramic.2019.112847 - APT of Cr segregation in Fe-Cr alloys
- - Mo segregation measurements in BCC Fe
- - V segregation at grain boundaries
- DOI:10.1016/j.scriptamat.2020.08.023 - W segregation effects in BCC iron

**Detection Limit Analysis**:
- Predicted segregation concentrations from McLean model (T018) must be above 0.1 at.% to be detectable
- For concentrations below detection limit, strategies include:
 - Lower temperature (increases segregation)
 - Higher bulk concentration
 - Extended data collection time

This experimental plan defines the physical validation step required for final scientific acceptance, as computational results alone are insufficient for chemical science verification.