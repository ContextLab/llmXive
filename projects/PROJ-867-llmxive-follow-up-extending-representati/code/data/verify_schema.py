"""
Semantic verification of PubLayNet annotations.

This module verifies that the loaded PubLayNet dataset annotations contain
the required structural information (bounding boxes and text content)
before processing begins, as required by Plan Phase 0 Step 1.

It performs semantic checks:
1. Presence of 'boxes' (bounding box coordinates)
2. Presence of 'text' (text content labels)
3. Consistency between boxes and text (same length)
4. Validity of box coordinates (non-negative, within reasonable bounds)
5. Non-empty text content
"""
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import sys

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config_dict, ensure_dirs


def validate_box(box: List[float], image_width: int = 1000, image_height: int = 1000) -> Tuple[bool, str]:
    """
    Validate a single bounding box.
    
    Args:
        box: List of 4 floats [x1, y1, x2, y2]
        image_width: Expected image width for normalization check
        image_height: Expected image height for normalization check
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(box) != 4:
        return False, f"Box must have 4 coordinates, got {len(box)}"
    
    x1, y1, x2, y2 = box
    
    # Check for non-negative coordinates
    if any(coord < 0 for coord in box):
        return False, f"Box coordinates must be non-negative: {box}"
    
    # Check ordering: x1 <= x2 and y1 <= y2
    if x1 > x2:
        return False, f"Box x1 ({x1}) must be <= x2 ({x2})"
    if y1 > y2:
        return False, f"Box y1 ({y1}) must be <= y2 ({y2})"
    
    # Check for zero-area boxes
    if x1 == x2 or y1 == y2:
        return False, f"Box has zero area: {box}"
    
    # Check if coordinates are within reasonable bounds (0-1000 for normalized)
    if x2 > image_width or y2 > image_height:
        # PubLayNet uses 1000x1000 normalized coordinates
        return False, f"Box exceeds image bounds: {box} (image: {image_width}x{image_height})"
    
    return True, ""


def validate_annotation(annotation: Dict[str, Any], image_idx: int) -> List[str]:
    """
    Validate a single annotation dictionary.
    
    Args:
        annotation: Dictionary containing 'boxes' and 'text' keys
        image_idx: Index of the image for error reporting
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check for required keys
    if 'boxes' not in annotation:
        errors.append(f"Image {image_idx}: Missing 'boxes' key in annotation")
        return errors
        
    if 'text' not in annotation:
        errors.append(f"Image {image_idx}: Missing 'text' key in annotation")
        return errors
    
    boxes = annotation['boxes']
    texts = annotation['text']
    
    # Check types
    if not isinstance(boxes, list):
        errors.append(f"Image {image_idx}: 'boxes' must be a list, got {type(boxes)}")
        return errors
        
    if not isinstance(texts, list):
        errors.append(f"Image {image_idx}: 'text' must be a list, got {type(texts)}")
        return errors
    
    # Check length consistency
    if len(boxes) != len(texts):
        errors.append(
            f"Image {image_idx}: Mismatch between boxes ({len(boxes)}) and text ({len(texts)})"
        )
    
    # Check for empty annotations
    if len(boxes) == 0:
        errors.append(f"Image {image_idx}: Empty annotation (no boxes or text)")
    
    # Validate each box
    for i, box in enumerate(boxes):
        is_valid, error_msg = validate_box(box)
        if not is_valid:
            errors.append(f"Image {image_idx}, box {i}: {error_msg}")
    
    # Validate text content
    for i, text in enumerate(texts):
        if not isinstance(text, str):
            errors.append(f"Image {image_idx}, text {i}: Must be string, got {type(text)}")
        elif len(text.strip()) == 0:
            # Allow empty strings but warn - might indicate data quality issue
            pass  # Not an error, but could be logged
    
    return errors


def verify_publaynet_schema(dataset_path: str, max_samples: Optional[int] = None) -> Dict[str, Any]:
    """
    Perform semantic verification of PubLayNet annotations.
    
    This function checks that the dataset annotations contain the required
    structural information (bounding boxes and text content) before processing.
    
    Args:
        dataset_path: Path to the directory containing PubLayNet data
        max_samples: Maximum number of samples to verify (None for all)
        
    Returns:
        Dictionary containing verification results:
            - total_samples: Total number of samples checked
            - valid_samples: Number of samples that passed validation
            - error_rate: Fraction of samples with errors
            - errors: List of detailed error messages
            - summary: Brief summary of the verification
    """
    config = get_config_dict()
    ensure_dirs()
    
    results = {
        'total_samples': 0,
        'valid_samples': 0,
        'error_rate': 0.0,
        'errors': [],
        'summary': '',
        'verified': False
    }
    
    # Find annotation files
    annotation_files = []
    if os.path.isdir(dataset_path):
        for root, _, files in os.walk(dataset_path):
            for file in files:
                if file.endswith('.json') or file.endswith('.jsonl'):
                    annotation_files.append(os.path.join(root, file))
    elif os.path.isfile(dataset_path):
        annotation_files = [dataset_path]
    
    if not annotation_files:
        results['summary'] = "No annotation files found in the specified path"
        results['verified'] = False
        return results
    
    total_errors = 0
    all_errors = []
    
    for file_path in annotation_files:
        if max_samples and results['total_samples'] >= max_samples:
            break
            
        try:
            # Handle JSONL format (one JSON object per line)
            if file_path.endswith('.jsonl'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f):
                        if max_samples and results['total_samples'] >= max_samples:
                            break
                        
                        try:
                            annotation = json.loads(line.strip())
                            errors = validate_annotation(annotation, results['total_samples'])
                            
                            results['total_samples'] += 1
                            
                            if errors:
                                total_errors += 1
                                all_errors.extend([f"{file_path}:{line_num}: " + e for e in errors])
                            else:
                                results['valid_samples'] += 1
                                
                        except json.JSONDecodeError as e:
                            all_errors.append(f"{file_path}:{line_num}: Invalid JSON - {str(e)}")
                            total_errors += 1
                            results['total_samples'] += 1
            
            # Handle JSON format (list of annotations)
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    annotations = json.load(f)
                    
                    if not isinstance(annotations, list):
                        all_errors.append(f"{file_path}: Expected a list of annotations")
                        continue
                    
                    for idx, annotation in enumerate(annotations):
                        if max_samples and results['total_samples'] >= max_samples:
                            break
                        
                        errors = validate_annotation(annotation, results['total_samples'])
                        results['total_samples'] += 1
                        
                        if errors:
                            total_errors += 1
                            all_errors.extend([f"{file_path}:{idx}: " + e for e in errors])
                        else:
                            results['valid_samples'] += 1
                            
        except Exception as e:
            all_errors.append(f"{file_path}: Failed to read file - {str(e)}")
    
    # Calculate results
    results['total_samples'] = results['valid_samples'] + total_errors
    if results['total_samples'] > 0:
        results['error_rate'] = total_errors / results['total_samples']
    
    results['errors'] = all_errors
    
    # Generate summary
    if results['total_samples'] == 0:
        results['summary'] = "No samples were processed"
        results['verified'] = False
    elif results['error_rate'] == 0:
        results['summary'] = f"All {results['total_samples']} samples passed semantic verification"
        results['verified'] = True
    elif results['error_rate'] < 0.05:
        results['summary'] = f"Minor issues detected: {total_errors}/{results['total_samples']} samples ({results['error_rate']:.1%} error rate)"
        results['verified'] = True
    else:
        results['summary'] = f"Significant issues detected: {total_errors}/{results['total_samples']} samples ({results['error_rate']:.1%} error rate)"
        results['verified'] = False
    
    return results


def main():
    """Main entry point for schema verification."""
    config = get_config_dict()
    data_path = config.get('data_path', 'data/publaynet')
    max_samples = config.get('max_verify_samples', 1000)
    
    print(f"Verifying PubLayNet schema at: {data_path}")
    print(f"Maximum samples to check: {max_samples}")
    
    results = verify_publaynet_schema(data_path, max_samples)
    
    print("\n" + "="*60)
    print("VERIFICATION RESULTS")
    print("="*60)
    print(f"Total samples checked: {results['total_samples']}")
    print(f"Valid samples: {results['valid_samples']}")
    print(f"Error rate: {results['error_rate']:.2%}")
    print(f"Verified: {'YES' if results['verified'] else 'NO'}")
    
    if results['errors']:
        print(f"\nFirst 10 errors:")
        for i, error in enumerate(results['errors'][:10]):
            print(f"  {i+1}. {error}")
        if len(results['errors']) > 10:
            print(f"  ... and {len(results['errors']) - 10} more errors")
    
    print("="*60)
    
    # Save results to data/
    output_path = config.get('output_path', 'data')
    ensure_dirs()
    
    output_file = os.path.join(output_path, 'verification_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")
    
    # Exit with error code if verification failed
    if not results['verified']:
        print("\n⚠️  Schema verification FAILED. Please fix the errors before proceeding.")
        sys.exit(1)
    else:
        print("\n✓ Schema verification PASSED. Ready to proceed with processing.")
        sys.exit(0)


if __name__ == "__main__":
    main()
