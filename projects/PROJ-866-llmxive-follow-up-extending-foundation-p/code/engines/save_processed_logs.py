import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to allow relative imports if running as script
# Note: In the actual project structure, this file is at code/engines/
# and imports from code/engines/ are relative to the code/ directory root
# However, since this is a standalone script, we handle imports carefully.

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        raise

def save_json_file(file_path: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def process_execution_log(
    raw_log: Dict[str, Any],
    compression_level: int,
    token_count: int
) -> Dict[str, Any]:
    """
    Process a raw execution log into a processed format.
    
    Args:
        raw_log: The raw execution log from full_context or compressed_context
        compression_level: The depth/truncation level used (0 for full context)
        token_count: The actual token count for the context passed
        
    Returns:
        A processed log entry with compression metadata
    """
    processed_entry = raw_log.copy()
    
    # Add compression-specific metadata
    processed_entry['compression_level'] = compression_level
    processed_entry['token_count'] = token_count
    
    # Ensure violation flags are present (set to 0 if not in raw log)
    if 'policy_violations' not in processed_entry:
        processed_entry['policy_violations'] = []
    if 'violation_count' not in processed_entry:
        processed_entry['violation_count'] = len(processed_entry.get('policy_violations', []))
    
    # Ensure status is present
    if 'status' not in processed_entry:
        processed_entry['status'] = 'completed' if processed_entry.get('success', False) else 'failed'
    
    return processed_entry

def save_processed_logs(
    input_dir: str,
    output_dir: str,
    compression_level: int,
    token_counts: Optional[Dict[str, int]] = None
) -> List[str]:
    """
    Process and save execution logs from input directory to output directory.
    
    Args:
        input_dir: Directory containing raw execution log JSON files
        output_dir: Directory to save processed execution logs
        compression_level: The compression depth used for these logs
        token_counts: Optional dict mapping workflow_id to token count.
                     If None, will try to infer from filename or use 0.
                     
    Returns:
        List of output file paths created
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    processed_files = []
    
    # Find all JSON files in input directory
    json_files = list(input_path.glob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in {input_dir}")
        return []
    
    print(f"Processing {len(json_files)} execution log files...")
    
    for json_file in json_files:
        try:
            # Load raw log
            raw_log = load_json_file(str(json_file))
            
            # Extract workflow ID for token count lookup
            workflow_id = raw_log.get('workflow_id', json_file.stem)
            
            # Get token count
            if token_counts and workflow_id in token_counts:
                token_count = token_counts[workflow_id]
            else:
                # Fallback: try to extract from filename or use 0
                # If the filename pattern is <workflow_id>_compressed_<level>.json
                # We could parse it, but for now we'll use 0 if not provided
                token_count = 0
                # Try to find token count in the log itself if available
                if 'token_count' in raw_log:
                    token_count = raw_log['token_count']
            
            # Process the log
            processed_entry = process_execution_log(
                raw_log,
                compression_level=compression_level,
                token_count=token_count
            )
            
            # Determine output filename
            # Keep original name but add _processed suffix if needed
            output_filename = f"{json_file.stem}_processed_{compression_level}.json"
            output_file_path = output_path / output_filename
            
            # Save processed log
            save_json_file(str(output_file_path), processed_entry)
            processed_files.append(str(output_file_path))
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            # Continue with next file rather than failing completely
            continue
    
    print(f"Saved {len(processed_files)} processed execution logs to {output_dir}")
    return processed_files

def main():
    """
    Main entry point for saving processed execution logs.
    
    Usage:
        python code/engines/save_processed_logs.py --input data/raw/execution_logs_full --output data/processed/ --level 0
        python code/engines/save_processed_logs.py --input data/raw/execution_logs_compressed --output data/processed/ --level 2
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Save processed execution logs with compression metadata')
    parser.add_argument('--input', '-i', required=True, help='Input directory containing raw execution logs')
    parser.add_argument('--output', '-o', required=True, help='Output directory for processed logs')
    parser.add_argument('--level', '-l', type=int, required=True, help='Compression level (depth) used')
    parser.add_argument('--token-file', '-t', help='Optional JSON file containing workflow_id -> token_count mapping')
    
    args = parser.parse_args()
    
    token_counts = None
    if args.token_file:
        if not os.path.exists(args.token_file):
            print(f"Error: Token count file not found: {args.token_file}")
            sys.exit(1)
        token_counts = load_json_file(args.token_file)
    
    processed_files = save_processed_logs(
        input_dir=args.input,
        output_dir=args.output,
        compression_level=args.level,
        token_counts=token_counts
    )
    
    if not processed_files:
        print("Warning: No files were processed. Check input directory and logs.")
        sys.exit(0)
    
    # Print summary
    print("\nSummary:")
    print(f"  Input directory: {args.input}")
    print(f"  Output directory: {args.output}")
    print(f"  Compression level: {args.level}")
    print(f"  Files processed: {len(processed_files)}")
    
    # Save a manifest of processed files
    manifest = {
        'compression_level': args.level,
        'input_dir': args.input,
        'output_dir': args.output,
        'processed_files': processed_files,
        'count': len(processed_files)
    }
    
    manifest_path = Path(args.output) / f"manifest_level_{args.level}.json"
    save_json_file(str(manifest_path), manifest)
    print(f"  Manifest saved to: {manifest_path}")

if __name__ == "__main__":
    main()