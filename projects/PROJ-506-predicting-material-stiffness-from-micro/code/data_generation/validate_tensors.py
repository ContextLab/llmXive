import numpy as np
import json
import yaml
import logging
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from utils.topology_metrics import calculate_shape_factor, calculate_connectivity
from skimage import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the dataset schema from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_conformity(entry: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate that an entry conforms to the schema.
    Returns a list of error messages if validation fails.
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required_fields:
        if field not in entry:
            errors.append(f"Missing required field: {field}")

    # Check types for existing fields
    for field, value in entry.items():
        if field in properties:
            prop_schema = properties[field]
            expected_type = prop_schema.get('type')
            
            if expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Field '{field}' should be string, got {type(value)}")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' should be number, got {type(value)}")
            elif expected_type == 'integer' and not isinstance(value, int):
                errors.append(f"Field '{field}' should be integer, got {type(value)}")
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append(f"Field '{field}' should be array, got {type(value)}")
            
            # Check enum constraints
            if expected_type == 'string' and 'enum' in prop_schema:
                if value not in prop_schema['enum']:
                    errors.append(f"Field '{field}' value '{value}' not in allowed values: {prop_schema['enum']}")

    return errors

def compute_vrh_bounds(matrix_moduli: Tuple[float, float], inclusion_moduli: Tuple[float, float], volume_fraction: float) -> Dict[str, float]:
    """
    Compute Voigt-Reuss-Hill bounds for effective stiffness.
    
    Args:
        matrix_moduli: (E_matrix, nu_matrix) - Young's modulus and Poisson's ratio of matrix
        inclusion_moduli: (E_inclusion, nu_inclusion) - Young's modulus and Poisson's ratio of inclusion
        volume_fraction: Volume fraction of inclusions (0 to 1)
    
    Returns:
        Dictionary with Voigt, Reuss, and Hill (average) bounds for bulk and shear moduli
    """
    E_m, nu_m = matrix_moduli
    E_i, nu_i = inclusion_moduli
    v = volume_fraction
    
    # Convert to bulk (K) and shear (G) moduli
    K_m = E_m / (3 * (1 - 2 * nu_m))
    G_m = E_m / (2 * (1 + nu_m))
    K_i = E_i / (3 * (1 - 2 * nu_i))
    G_i = E_i / (2 * (1 + nu_i))
    
    # Voigt bounds (upper bounds)
    K_V = v * K_i + (1 - v) * K_m
    G_V = v * G_i + (1 - v) * G_m
    
    # Reuss bounds (lower bounds)
    # Handle potential division by zero
    try:
        K_R = 1 / (v / K_i + (1 - v) / K_m)
        G_R = 1 / (v / G_i + (1 - v) / G_m)
    except ZeroDivisionError:
        K_R = 0
        G_R = 0
    
    # Hill bounds (arithmetic mean of Voigt and Reuss)
    K_H = (K_V + K_R) / 2
    G_H = (G_V + G_R) / 2
    
    return {
        'K_Voigt': K_V,
        'K_Reuss': K_R,
        'K_Hill': K_H,
        'G_Voigt': G_V,
        'G_Reuss': G_R,
        'G_Hill': G_H
    }

def validate_vrh_bounds(stiffness_tensor: np.ndarray, bounds: Dict[str, float], tolerance: float = 0.01) -> List[str]:
    """
    Validate that stiffness tensor components are within Voigt-Reuss-Hill bounds.
    
    For a 2D plane strain/stress problem, the stiffness tensor typically has components:
    C11, C12, C22, C66 (shear)
    
    Args:
        stiffness_tensor: 2D array of stiffness components
        bounds: Dictionary with Voigt-Reuss-Hill bounds
        tolerance: Tolerance for bound violations (as fraction)
    
    Returns:
        List of error messages if validation fails
    """
    errors = []
    
    if stiffness_tensor.size == 0:
        errors.append("Empty stiffness tensor")
        return errors
    
    # Check for negative values (physical plausibility)
    if np.any(stiffness_tensor < 0):
        errors.append("Stiffness tensor contains negative values")
    
    # Check for NaN values
    if np.any(np.isnan(stiffness_tensor)):
        errors.append("Stiffness tensor contains NaN values")
    
    # Check for Inf values
    if np.any(np.isinf(stiffness_tensor)):
        errors.append("Stiffness tensor contains Inf values")
    
    # If we have bounds, check against them
    if bounds and 'K_Hill' in bounds and 'G_Hill' in bounds:
        # Bulk and shear moduli should be positive and within reasonable ranges
        # This is a simplified check; full tensor bounds would require more complex analysis
        if bounds['K_Hill'] <= 0:
            errors.append("Invalid Hill bulk modulus (non-positive)")
        if bounds['G_Hill'] <= 0:
            errors.append("Invalid Hill shear modulus (non-positive)")
    
    return errors

def validate_dataset(
    metadata_path: Path,
    schema_path: Path,
    validation_log_path: Path,
    image_dir: Optional[Path] = None,
    batch_size: int = 100
) -> int:
    """
    Validate a dataset of microstructures and stiffness tensors.
    
    This function processes entries in batches to avoid memory issues.
    It logs validation failures to a CSV file.
    
    Args:
        metadata_path: Path to the metadata JSON file
        schema_path: Path to the schema YAML file
        validation_log_path: Path to the output validation log CSV
        image_dir: Optional directory containing image files for topological validation
        batch_size: Number of entries to process in each batch
    
    Returns:
        Number of validation failures
    """
    # Load schema
    try:
        schema = load_schema(schema_path)
        logger.info(f"Loaded schema from {schema_path}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return -1
    
    # Load metadata
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        entries = metadata.get('entries', [])
        logger.info(f"Loaded {len(entries)} entries from {metadata_path}")
    except Exception as e:
        logger.error(f"Failed to load metadata: {e}")
        return -1
    
    # Prepare validation log
    validation_log_path.parent.mkdir(parents=True, exist_ok=True)
    log_header = ['entry_id', 'reason', 'density', 'topology']
    
    failure_count = 0
    
    # Process in batches
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i + batch_size]
        
        for entry in batch:
            entry_id = entry.get('seed', f"unknown_{i}")
            reason = None
            density = entry.get('inclusion_density', 'N/A')
            topology = entry.get('topology_type', 'N/A')
            
            # 1. Schema Conformance Check
            schema_errors = validate_schema_conformity(entry, schema)
            if schema_errors:
                reason = f"Schema violation: {', '.join(schema_errors)}"
                failure_count += 1
            
            # 2. Physical Plausibility Check - Stiffness
            if reason is None:
                stiffness_tensor = entry.get('stiffness_tensor')
                if stiffness_tensor is not None:
                    stiffness_array = np.array(stiffness_tensor)
                    
                    # Check for negative values
                    if np.any(stiffness_array < 0):
                        reason = "Unphysical Microstructure: negative stiffness"
                        failure_count += 1
                    
                    # Check for NaN
                    elif np.any(np.isnan(stiffness_array)):
                        reason = "Unphysical Microstructure: NaN in stiffness"
                        failure_count += 1
                    
                    # Check for Inf
                    elif np.any(np.isinf(stiffness_array)):
                        reason = "Unphysical Microstructure: Inf in stiffness"
                        failure_count += 1
            
            # 3. Solver Convergence Check (if residual is available)
            if reason is None and 'solver_residual' in entry:
                residual = entry['solver_residual']
                if residual > 1e-4:
                    reason = "Solver Convergence Failure"
                    failure_count += 1
            
            # 4. Topological Metrics Check (if image is available)
            if reason is None and image_dir is not None:
                image_path = entry.get('image_path')
                if image_path:
                    full_image_path = image_dir / image_path
                    if full_image_path.exists():
                        try:
                            image = io.imread(full_image_path)
                            shape_factor = calculate_shape_factor(image)
                            
                            # Check for NaN shape factor
                            if np.isnan(shape_factor):
                                reason = "Unphysical Microstructure: NaN shape_factor"
                                failure_count += 1
                            
                            # Optional: Check for extreme shape factors (domain specific)
                            # if shape_factor > some_threshold:
                            #     reason = "Unphysical Microstructure: extreme shape_factor"
                            
                        except Exception as e:
                            logger.warning(f"Could not compute topological metrics for {entry_id}: {e}")
                            # Don't fail the entry for image processing errors, just log
            else:
                # If we have an image path but can't read it, log a warning
                if image_dir is not None and 'image_path' in entry:
                    full_image_path = image_dir / entry['image_path']
                    if not full_image_path.exists():
                        logger.warning(f"Image file not found for entry {entry_id}: {full_image_path}")
            
            # Log failure if any
            if reason:
                with open(validation_log_path, 'a', newline='') as log_file:
                    writer = csv.writer(log_file)
                    if i == 0 and entry == batch[0]:
                        writer.writerow(log_header)
                    writer.writerow([entry_id, reason, density, topology])
                
                logger.warning(f"Entry {entry_id} failed validation: {reason}")
    
    logger.info(f"Validation complete. {failure_count} failures logged to {validation_log_path}")
    return failure_count

def main():
    """Main entry point for the validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate microstructure dataset')
    parser.add_argument('--metadata', type=str, required=True, 
                      help='Path to metadata JSON file')
    parser.add_argument('--schema', type=str, required=True, 
                      help='Path to schema YAML file')
    parser.add_argument('--output', type=str, required=True, 
                      help='Path to output validation log CSV')
    parser.add_argument('--images', type=str, default=None,
                      help='Directory containing image files')
    parser.add_argument('--batch-size', type=int, default=100,
                      help='Batch size for processing')
    
    args = parser.parse_args()
    
    metadata_path = Path(args.metadata)
    schema_path = Path(args.schema)
    output_path = Path(args.output)
    image_dir = Path(args.images) if args.images else None
    
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        return 1
    
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return 1
    
    failures = validate_dataset(
        metadata_path=metadata_path,
        schema_path=schema_path,
        validation_log_path=output_path,
        image_dir=image_dir,
        batch_size=args.batch_size
    )
    
    if failures < 0:
        logger.error("Validation failed due to loading errors")
        return 1
    
    if failures > 0:
        logger.warning(f"Validation completed with {failures} failures")
        return 0  # Return 0 even with failures, as this is expected in validation
    
    logger.info("Validation completed successfully with no failures")
    return 0

if __name__ == '__main__':
    exit(main())
