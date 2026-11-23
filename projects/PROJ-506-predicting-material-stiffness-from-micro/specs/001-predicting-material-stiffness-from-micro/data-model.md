# Data Model: Predicting Material Stiffness from Microstructure

## Dataset Schema

Each entry in the dataset consists of:
- `image_path`: Path to the PNG image (128x128 pixels).
- `stiffness_tensor`: 6x6 effective stiffness tensor (Voigt notation).
- `inclusion_density`: Float (0.0 to 1.0).
- `topology_type`: String (e.g., "spherical", "ellipsoidal").
- `shape_factor`: Float.
- `connectivity`: Float.
- `seed`: Integer.

## Metadata

Metadata is stored in JSON format, linking image paths to their ground truth tensors and generation parameters.
