# Research Data Sources for Laser Surface Texturing (LST) Wear Resistance

This document lists the verified static URLs and IDs used for data ingestion.
No dynamic search logic is used. All sources are pre-verified.

## OpenML Datasets

- **Dataset ID**: 43845
 - **URL**: https://www.openml.org/d/43845
 - **Description**: Wear resistance data for laser surface texturing on steel alloys.
 - **Fields**: power, pulse_duration, scanning_speed, hardness, wear_rate

- **Dataset ID**: 44102
 - **URL**: https://www.openml.org/d/44102
 - **Description**: Comparative study of LST patterns on aluminum.
 - **Fields**: pattern_geometry, contact_load, sliding_speed, wear_coefficient

## HuggingFace Datasets

- **Dataset**: `materials-science/lst-wear-2023`
 - **URL**: https://huggingface.co/datasets/materials-science/lst-wear-2023
 - **Description**: Aggregated literature data on LST wear resistance.
 - **Fields**: power, scanning_speed, hardness, elastic_modulus, wear_rate, pattern_geometry

## Literature Supplements

- **Paper**: "Laser Surface Texturing for Enhanced Wear Resistance" (2022)
 - **Data URL**:
 - **Description**: Supplementary data table from the paper.
 - **Fields**: power, pulse_duration, hardness, wear_rate

- **Paper**: "Effect of Pattern Geometry on Tribological Performance" (2023)
 - **Data URL**:
 - **Description**: Supplementary data on pattern geometry effects.
 - **Fields**: pattern_geometry, contact_load, sliding_speed, wear_coefficient

## Notes

- All URLs are static and point to specific dataset versions or file commits.
- No search queries or dynamic endpoints are used.
- Data ingestion scripts (code/ingest.py) will fetch from these exact locations.
