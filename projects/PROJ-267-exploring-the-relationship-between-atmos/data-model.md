# Data Model

## AR Event
- **date**: ISO 8601 date string
- **peak_intensity**: Float (Integrated Water Vapor Transport in kg/m/s)
- **footprint**: List of [lat, lon] coordinates (bounding box)

## Gravity Anomaly
- **date**: ISO 8601 date string (monthly)
- **anomaly_value**: Float (Geoid height anomaly at satellite altitude in meters)
- **uncertainty**: Float (Standard deviation of the anomaly in meters)
- **region**: String (Study region identifier)

**Frame of Reference Definition**:
The `anomaly_value` represents the perturbation in the gravitational potential at the GRACE-FO satellite altitude (approx. 450-500 km, low Earth orbit), NOT the geoid height at the Earth's surface. This quantity is derived from spherical harmonic coefficients of the Earth's gravity field. It is explicitly a coordinate-dependent quantity; the analysis assumes a static, non-rotating frame for the duration of the monthly aggregation window. This acknowledges the coordinate artifact nature of "static" anomalies in a dynamic gravitational field, consistent with the covariant description required by the 1915 field equations where gravitational potential is frame-relative.

## Correlation Result
- **lag**: Integer (Months)
- **correlation_coefficient**: Float (Pearson r)
- **raw_p_value**: Float
- **corrected_p_value**: Float
- **confidence_interval_lower**: Float
- **confidence_interval_upper**: Float
- **significance_flag**: Boolean (Informational only, p < 0.05 corrected)
- **region_type**: String ('target' or 'control')
- **signal_to_noise_ratio**: Float (Correlation coefficient / uncertainty)