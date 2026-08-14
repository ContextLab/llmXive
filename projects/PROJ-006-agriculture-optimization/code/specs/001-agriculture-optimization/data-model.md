# Data Model Documentation

## Entities

### Household
- household_id (str): Unique identifier
- country (str): Country code (MW/TZ)
- village_id (str): Village identifier
- latitude (float): Plot center latitude
- longitude (float): Plot center longitude
- survey_year (int): Survey year

### Remote Sensing Pixel
- pixel_id (str): Unique pixel identifier
- latitude (float): Pixel center latitude
- longitude (float): Pixel center longitude
- ndvi_values (list): Time series of NDVI values
- cloud_mask (list): Cloud cover flags

### Analysis Dataset
- household_id (str): Foreign key
- CSA_Index (float): Composite practice adoption score
- Stability_Score (float): Yield stability metric
- HFIAS (float): Food insecurity score
- controls (dict): Additional covariates

## Relationships
- Household 1:1 Remote Sensing Pixel (via spatial join)
- Household 1:N Survey Responses

## Provenance
- LSMS-ISA: World Bank Microdata Library
- Sentinel-2: Copernicus Data Space Ecosystem
