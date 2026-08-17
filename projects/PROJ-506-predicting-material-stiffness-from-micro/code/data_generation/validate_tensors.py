import numpy as np
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Import existing utilities from the project
from code.utils.fft_homogenization import compute_effective_stiffness
from code.utils.metrics import mean_absolute_error, mean_squared_error, r2_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict:
    """Load and return the YAML schema definition."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_conformity(record: Dict, schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validate that a dataset record conforms to the schema definition.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_fields = schema.get('required_fields', [])
    
    for field in required_fields:
        field_name = field['name']
        field_type = field['type']
        
        if field_name not in record:
            errors.append(f"Missing required field: {field_name}")
            continue
        
        value = record[field_name]
        
        # Type checking
        if field_type == 'string':
            if not isinstance(value, str):
                errors.append(f"Field {field_name} should be string, got {type(value)}")
        elif field_type == 'float[]':
            if not isinstance(value, (list, np.ndarray)):
                errors.append(f"Field {field_name} should be array, got {type(value)}")
            elif len(value) == 0:
                errors.append(f"Field {field_name} is empty")
        elif field_type == 'float':
            if not isinstance(value, (int, float, np.floating)):
                errors.append(f"Field {field_name} should be float, got {type(value)}")
        elif field_type == 'integer':
            if not isinstance(value, (int, np.integer)):
                errors.append(f"Field {field_name} should be integer, got {type(value)}")
        elif field_type == 'string':
            if not isinstance(value, str):
                errors.append(f"Field {field_name} should be string, got {type(value)}")
    
    return len(errors) == 0, errors

def compute_vrh_bounds(stiffness_tensor: np.ndarray, volume_fraction: float) -> Dict[str, float]:
    """
    Compute Voigt-Reuss-Hill bounds for effective stiffness.
    
    Args:
        stiffness_tensor: 6x6 stiffness matrix (Voigt notation)
        volume_fraction: Volume fraction of inclusions (0 to 1)
        
    Returns:
        Dictionary with Voigt, Reuss, and Hill bounds for bulk and shear moduli
    """
    # Extract elastic constants from stiffness tensor (Voigt notation)
    # C11, C12, C44 for isotropic approximation
    if stiffness_tensor.shape != (6, 6):
        raise ValueError(f"Stiffness tensor must be 6x6, got {stiffness_tensor.shape}")
    
    C11 = stiffness_tensor[0, 0]
    C12 = stiffness_tensor[0, 1]
    C44 = stiffness_tensor[3, 3]
    
    # Voigt bounds (upper bound)
    K_voigt = (C11 + 2 * C12) / 3
    G_voigt = (C11 - C12 + 3 * C44) / 5
    
    # Reuss bounds (lower bound) - simplified for isotropic case
    # For full tensor, we would invert the compliance matrix
    # Here we use a simplified approximation
    S11 = 1 / C11 if C11 != 0 else 0
    S12 = -C12 / (C11 * (C11 + C12)) if C11 != 0 and C12 != 0 else 0
    S44 = 1 / C44 if C44 != 0 else 0
    
    K_reuss = 1 / (3 * (S11 + 2 * S12)) if (S11 + 2 * S12) != 0 else 0
    G_reuss = 1 / (S11 - S12 + 3 * S44) * 5 / (S11 - S12 + 3 * S44) if (S11 - S12 + 3 * S44) != 0 else 0
    
    # Hill average (arithmetic mean of Voigt and Reuss)
    K_hill = (K_voigt + K_reuss) / 2
    G_hill = (G_voigt + G_reuss) / 2
    
    return {
        'K_voigt': float(K_voigt),
        'K_reuss': float(K_reuss),
        'K_hill': float(K_hill),
        'G_voigt': float(G_voigt),
        'G_reuss': float(G_reuss),
        'G_hill': float(G_hill)
    }

def validate_vrh_bounds(stiffness_tensor: np.ndarray, volume_fraction: float) -> Tuple[bool, str]:
    """
    Validate that computed stiffness tensor falls within VRH bounds.
    
    Args:
        stiffness_tensor: 6x6 stiffness matrix
        volume_fraction: Volume fraction of inclusions
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        bounds = compute_vrh_bounds(stiffness_tensor, volume_fraction)
        
        # Extract effective bulk and shear moduli from stiffness tensor
        K_eff = (stiffness_tensor[0, 0] + 2 * stiffness_tensor[0, 1]) / 3
        G_eff = (stiffness_tensor[0, 0] - stiffness_tensor[0, 1] + 3 * stiffness_tensor[3, 3]) / 5
        
        # Check if effective moduli are within bounds
        if not (bounds['K_reuss'] <= K_eff <= bounds['K_voigt']):
            return False, f"Bulk modulus {K_eff:.2f} outside VRH bounds [{bounds['K_reuss']:.2f}, {bounds['K_voigt']:.2f}]"
        
        if not (bounds['G_reuss'] <= G_eff <= bounds['G_voigt']):
            return False, f"Shear modulus {G_eff:.2f} outside VRH bounds [{bounds['G_reuss']:.2f}, {bounds['G_voigt']:.2f}]"
        
        # Check for unphysical values (negative stiffness)
        if K_eff < 0 or G_eff < 0:
            return False, f"Unphysical stiffness values: K={K_eff:.2f}, G={G_eff:.2f}"
        
        # Check for extreme values that might indicate solver failure
        if K_eff > 1e6 or G_eff > 1e6:
            return False, f"Extremely high stiffness values: K={K_eff:.2e}, G={G_eff:.2e}"
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"VRH validation error: {str(e)}"

def validate_dataset(metadata_path: str, schema_path: str, output_log_path: str) -> Dict[str, Any]:
    """
    Validate the entire dataset against schema and physical constraints.
    
    Args:
        metadata_path: Path to the dataset metadata JSON file
        schema_path: Path to the schema YAML file
        output_log_path: Path to write the validation log CSV
        
    Returns:
        Summary statistics of the validation
    """
    # Load schema
    schema = load_schema(schema_path)
    
    # Load metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    validation_results = []
    valid_count = 0
    invalid_count = 0
    
    for record in metadata:
        seed = record.get('seed', 'unknown')
        is_valid = True
        reasons = []
        
        # 1. Schema conformity check
        schema_valid, schema_errors = validate_schema_conformity(record, schema)
        if not schema_valid:
            is_valid = False
            reasons.extend(schema_errors)
        
        # 2. Physical plausibility check (VRH bounds)
        if 'stiffness_tensor' in record and 'inclusion_density' in record:
            try:
                stiffness = np.array(record['stiffness_tensor'])
                density = float(record['inclusion_density'])
                
                vrh_valid, vrh_reason = validate_vrh_bounds(stiffness, density)
                if not vrh_valid:
                    is_valid = False
                    reasons.append(vrh_reason)
                    
            except Exception as e:
                is_valid = False
                reasons.append(f"Error during VRH check: {str(e)}")
        
        # 3. Additional checks for unphysical microstructures
        if 'topology_type' in record:
            topology = record['topology_type']
            if topology not in ['void', 'inclusion', 'mixed']:
                is_valid = False
                reasons.append(f"Invalid topology type: {topology}")
        
        # Record the result
        validation_results.append({
            'seed': seed,
            'is_valid': is_valid,
            'reasons': '; '.join(reasons) if reasons else 'Valid',
            'inclusion_density': record.get('inclusion_density', None),
            'topology_type': record.get('topology_type', None)
        })
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
    
    # Write validation log to CSV
    log_path = Path(output_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write('seed,is_valid,reasons,inclusion_density,topology_type\n')
        for result in validation_results:
            f.write(f"{result['seed']},{result['is_valid']},\"{result['reasons']}\",{result['inclusion_density']},{result['topology_type']}\n")
    
    logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid")
    logger.info(f"Validation log written to: {output_log_path}")
    
    return {
        'total_records': len(metadata),
        'valid_count': valid_count,
        'invalid_count': invalid_count,
        'validation_rate': valid_count / len(metadata) if len(metadata) > 0 else 0,
        'log_path': str(log_path)
    }

def main():
    """Main entry point for tensor validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate generated stiffness tensors')
    parser.add_argument('--metadata', type=str, required=True, help='Path to dataset metadata JSON')
    parser.add_argument('--schema', type=str, required=True, help='Path to schema YAML')
    parser.add_argument('--output', type=str, default='data/processed/validation_log.csv', 
                      help='Path to output validation log CSV')
    
    args = parser.parse_args()
    
    try:
        results = validate_dataset(args.metadata, args.schema, args.output)
        print(json.dumps(results, indent=2))
        
        # Exit with error code if validation rate is too low
        if results['validation_rate'] < 0.9:
            logger.warning(f"Validation rate {results['validation_rate']:.2%} is below 90% threshold")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    import sys
    main()
