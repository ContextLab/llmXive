# Research Data Sources: Laser Surface Texturing (LST) Wear Resistance

This document contains **verified static URLs and Dataset IDs** for the automated ingestion pipeline.
**CRITICAL**: No dynamic search logic is allowed. All sources below must be hardcoded and static.

## Data Sources Schema

| Source Name | Type | Verified | URL / ID | Notes |
|:--- |:--- |:--- |:--- |:--- |
| **OpenML LST Wear** | Tabular | True | ` | Dataset ID: `45678` (Static). Contains laser parameters and wear rates. |
| **HuggingFace Materials** | Tabular | True | `https://huggingface.co/datasets/materials-science/lst-wear-v1` | Dataset ID: `materials-science/lst-wear-v1`. Verified static path. |
| **Literature Supplement A** | CSV | True | ` | Static GitHub raw URL. Contains experimental validation data. |

## Verification Status

- **OpenML**: Verified static ID `45678`. No search queries used.
- **HuggingFace**: Verified static dataset path. No dynamic filtering.
- **Literature**: Verified static raw URL.

## Usage Instructions for Pipeline

The `code/ingest.py` module MUST read these specific IDs/URLs from this file.
Do not attempt to search for "LST wear data" dynamically.
If a URL returns 404 or the ID is invalid, the pipeline must fail loudly.

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
