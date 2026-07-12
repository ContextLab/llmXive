"""
Provenance tracking module for the llmXive science pipeline.

This module generates machine-readable YAML sidecars for data artifacts,
recording the pipeline version, parameters, software versions, and execution
context to ensure reproducibility and traceability (Constitution Principle VI).
"""
import os
import time
import uuid
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Pipeline version identifier - should be updated with each major release
PIPELINE_VERSION = "1.0.0"
PIPELINE_NAME = "llmXive-social-exclusion-reward-pipeline"


def get_software_versions() -> Dict[str, str]:
    """
    Collect versions of key software dependencies.
    
    Returns:
        Dictionary mapping package names to their versions.
        Returns 'unknown' if version cannot be determined.
    """
    versions = {}
    
    # Core scientific packages
    packages_to_check = [
        'numpy', 'pandas', 'scipy', 'nibabel', 
        'nilearn', 'statsmodels', 'scikit-learn'
    ]
    
    for pkg_name in packages_to_check:
        try:
            module = __import__(pkg_name)
            version = getattr(module, '__version__', 'unknown')
            versions[pkg_name] = str(version)
        except ImportError:
            versions[pkg_name] = 'not_installed'
        except AttributeError:
            versions[pkg_name] = 'unknown'
    
    return versions


def generate_provenance_sidecar(
    input_file: str,
    output_file: str,
    processing_stage: str,
    parameters: Optional[Dict[str, Any]] = None,
    parent_provenance_ids: Optional[List[str]] = None,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate a YAML sidecar file for a processed data artifact.
    
    This function creates a machine-readable record of how a data file
    was produced, including:
    - Unique provenance ID
    - Timestamp of generation
    - Pipeline version and name
    - Software versions at time of execution
    - Input file path
    - Output file path
    - Processing stage name
    - Parameters used
    - Parent provenance IDs (for lineage tracking)
    - Additional custom metadata
    
    Args:
        input_file: Path to the input data file that was processed.
        output_file: Path to the output data file being documented.
        processing_stage: Name of the pipeline stage (e.g., 'preprocessing', 'glm').
        parameters: Dictionary of parameters used during processing.
        parent_provenance_ids: List of provenance IDs from parent files.
        additional_metadata: Any additional key-value pairs to record.
        
    Returns:
        Path to the generated sidecar file (output_file + '.provenance.yml').
        
    Raises:
        FileNotFoundError: If input_file does not exist.
        ValueError: If required parameters are missing or invalid.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    if not processing_stage:
        raise ValueError("processing_stage cannot be empty")
    
    # Generate unique ID for this provenance record
    provenance_id = str(uuid.uuid4())
    
    # Collect software versions
    software_versions = get_software_versions()
    
    # Build the provenance record
    provenance_record = {
        'provenance_id': provenance_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'pipeline': {
            'name': PIPELINE_NAME,
            'version': PIPELINE_VERSION
        },
        'software_versions': software_versions,
        'input': {
            'file_path': str(input_file),
            'file_exists': True
        },
        'output': {
            'file_path': str(output_file)
        },
        'processing': {
            'stage': processing_stage,
            'parameters': parameters or {}
        },
        'lineage': {
            'parent_provenance_ids': parent_provenance_ids or []
        }
    }
    
    # Add additional metadata if provided
    if additional_metadata:
        provenance_record['metadata'] = additional_metadata
    
    # Determine sidecar file path
    sidecar_path = Path(output_file).with_suffix(output_file.split('.')[-1] + '.provenance.yml')
    if not sidecar_path.suffix.endswith('.provenance.yml'):
        # Handle files without extension or with complex extensions
        sidecar_path = Path(str(output_file) + '.provenance.yml')
    
    # Ensure the directory exists
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the YAML sidecar file
    with open(sidecar_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            provenance_record,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=1000
        )
    
    return str(sidecar_path)


def generate_provenance_manifest(
    output_dir: str,
    stage_name: str,
    file_entries: List[Dict[str, Any]]
) -> str:
    """
    Generate a manifest file that aggregates provenance records for a batch.
    
    This creates a summary YAML file containing provenance information for
    multiple processed files, useful for batch tracking and auditing.
    
    Args:
        output_dir: Directory where the manifest will be saved.
        stage_name: Name of the processing stage.
        file_entries: List of dictionaries containing file-specific provenance data.
            Each entry should have:
            - 'input_file': Path to input
            - 'output_file': Path to output
            - 'provenance_id': ID from the sidecar
            - 'parameters': Processing parameters
            
    Returns:
        Path to the generated manifest file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        'manifest_id': str(uuid.uuid4()),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'pipeline': {
            'name': PIPELINE_NAME,
            'version': PIPELINE_VERSION
        },
        'stage': stage_name,
        'software_versions': get_software_versions(),
        'file_provenance': file_entries,
        'summary': {
            'total_files': len(file_entries),
            'generated_at': datetime.now(timezone.utc).isoformat()
        }
    }
    
    manifest_path = output_path / f"{stage_name}_provenance_manifest.yml"
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        yaml.dump(
            manifest,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=1000
        )
    
    return str(manifest_path)


def main():
    """
    Command-line interface for testing provenance generation.
    
    Usage:
        python -m utils.provenance --input /path/to/input.nii.gz \
                                   --output /path/to/output.nii.gz \
                                   --stage preprocessing \
                                   --param smoothing=6 \
                                   --param normalization=MNI
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate provenance sidecar for data artifacts'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to the input data file'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Path to the output data file'
    )
    parser.add_argument(
        '--stage', '-s',
        required=True,
        help='Processing stage name'
    )
    parser.add_argument(
        '--param', '-p',
        action='append',
        default=[],
        help='Processing parameters in key=value format (can be repeated)'
    )
    parser.add_argument(
        '--parent-id',
        action='append',
        default=[],
        help='Parent provenance IDs (can be repeated)'
    )
    
    args = parser.parse_args()
    
    # Parse parameters
    parameters = {}
    for param in args.param:
        if '=' in param:
            key, value = param.split('=', 1)
            parameters[key] = value
        else:
            parameters[param] = True
    
    # Generate sidecar
    try:
        sidecar_path = generate_provenance_sidecar(
            input_file=args.input,
            output_file=args.output,
            processing_stage=args.stage,
            parameters=parameters,
            parent_provenance_ids=args.parent_id
        )
        print(f"Provenance sidecar generated: {sidecar_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())