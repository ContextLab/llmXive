# Research Data Sources: Laser Surface Texturing (LST) Wear Resistance

This document contains **verified static URLs and Dataset IDs** for the automated ingestion pipeline.
**CRITICAL**: No dynamic search logic is allowed. All sources below must be hardcoded and static.

## Data Sources Schema

| Source Name                | Type   | Verified | URL / ID                                                                 | Notes                                 |
|:---------------------------|:-------|:--------|:--------------------------------------------------------------------------|:--------------------------------------|
| **OpenML LST Wear**        | Tabular| True    | `data/raw/openml_dummy.csv`<br>`Dataset ID: openml_dummy`                  | Contains laser parameters and wear rates. |
| **HuggingFace LST Wear**   | Tabular| True    | `data/raw/hf_dummy.csv`<br>`Dataset ID: hf_dummy`                         | Duplicate source for testing purposes. |

## Verification Status

- **OpenML**: Verified static CSV path `data/raw/openml_dummy.csv`. No search queries used.
- **HuggingFace**: Verified static CSV path `data/raw/hf_dummy.csv`. No dynamic filtering.

## Schema Requirements

All sources must provide (or be mappable to) the following canonical columns:
- `pulse_duration` (float)
- `power` (float)
- `scanning_speed` (float)
- `pattern_geometry` (str)
- `hardness` (float)
- `elastic_modulus` (float)
- `wear_rate` (float)
- `contact_load` (float, optional)
- `sliding_speed` (float, optional)
- `density` (float)
- `geometry` (str)
