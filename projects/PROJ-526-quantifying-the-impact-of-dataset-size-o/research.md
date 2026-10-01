# Research: Data Sources for Material Properties

## Target Properties

This document specifies the HuggingFace dataset IDs for the 2-3 target material properties to be analyzed.

### Properties

1. **Band Gap** (Electronic Property)
 - Dataset ID: `materials_project/band_gap`
 - Description: Band gap values from the Materials Project database
 - Expected entries: ~100,000+ materials

2. **Formation Energy** (Electronic/Thermodynamic Property)
 - Dataset ID: `materials_project/formation_energy`
 - Description: Formation energy per atom from the Materials Project database
 - Expected entries: ~100,000+ materials

### Notes

- These datasets are chosen for their size and relevance to the study.
- Both properties are available from the Materials Project on HuggingFace.
- The datasets contain composition data which can be used to generate Magpie descriptors.
- If additional properties are needed, they can be added following the same pattern.

### Data Format

Each dataset contains:
- `formula`: Chemical formula
- `elements`: List of elements
- `composition`: Dictionary of element to fraction
- `property_value`: The target property value (band gap or formation energy)
- Additional metadata fields

### Access

All datasets are publicly available on HuggingFace. No special authentication is required beyond the standard HuggingFace token for rate limit management.
