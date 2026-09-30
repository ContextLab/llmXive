# Data Model Specification

## Entities

### QuantumState
Represents a quantum many-body state.
- **id**: Unique identifier (UUID)
- **system_size**: Integer (N)
- **wavefunction**: Array of complex numbers (can be sparse)
- **metadata**: Dictionary containing generation parameters (e.g., Hamiltonian type, coupling constants)

## Data Formats

### Raw Data (HDF5)
- **Path**: `data/raw/<dataset_name>.h5`
- **Structure**:
 - `/wavefunctions`: Dataset of complex arrays
 - `/metadata`: Attributes or datasets containing generation parameters

### Processed Data (CSV)
- **Path**: `data/processed/<metric_type>.csv`
- **Columns**:
 - `system_size`: N
 - `entanglement_entropy`: Float
 - `complexity_ncd`: Float
 - `bond_dimension`: Integer (if applicable)

## Schemas
Validation schemas are defined in `code/validators/data_schema.py`.
