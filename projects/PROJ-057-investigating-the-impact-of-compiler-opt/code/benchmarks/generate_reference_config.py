import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

def generate_reference_configs(input_dir: str, output_config_path: str) -> List[Dict[str, Any]]:
    """
    Generate a configuration list for reference benchmarks based on input files.
    
    Args:
        input_dir: Directory containing input binary tensors
        output_config_path: Path to save the JSON configuration file
        
    Returns:
        List of configuration dictionaries
    """
    input_path = Path(input_dir)
    configs = []
    
    # Scan for input files and infer kernel type from naming convention
    # Assuming files are named: {config_id}_{kernel_type}.bin
    for file_path in input_path.glob('*.bin'):
        filename = file_path.name
        # Parse filename: assume format "config_id_kerneltype.bin"
        parts = filename.replace('.bin', '').split('_')
        if len(parts) >= 2:
            config_id = '_'.join(parts[:-1])  # In case of underscores in ID
            kernel_type = parts[-1]
            
            if kernel_type in ['matmul', 'softmax', 'layernorm']:
                configs.append({
                    'config_id': config_id,
                    'kernel_type': kernel_type,
                    'tensor_file': filename
                })
    
    # Save to JSON
    with open(output_config_path, 'w') as f:
        json.dump(configs, f, indent=2)
    
    return configs

def main():
    parser = argparse.ArgumentParser(description='Generate reference benchmark configurations')
    parser.add_argument('--input-dir', type=str, default='data/raw',
                      help='Directory containing input binary tensors')
    parser.add_argument('--output-config', type=str, default='data/raw/reference_configs.json',
                      help='Path to save the JSON configuration file')
    
    args = parser.parse_args()
    
    configs = generate_reference_configs(args.input_dir, args.output_config)
    print(f"Generated {len(configs)} reference configurations")
    print(f"Saved to {args.output_config}")

if __name__ == '__main__':
    main()
