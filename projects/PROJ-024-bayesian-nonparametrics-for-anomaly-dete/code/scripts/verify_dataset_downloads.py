#!/usr/bin/env python3
"""
T048: Verify all three UCI datasets are downloaded via download_datasets.py

This script ensures Electricity, Traffic, and Synthetic Control Chart datasets
are downloaded and validated per SC-001 requirement for 3 UCI datasets.

Usage: python verify_dataset_downloads.py

Exit codes:
  0 - All datasets downloaded and validated successfully
  1 - One or more datasets failed to download or validate
"""

import os
import sys
import hashlib
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from download_datasets import (
    download_electricity_dataset,
    download_traffic_dataset,
    download_synthetic_control_chart_dataset,
    compute_file_checksum,
    DownloadResult
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Download and verify all three UCI datasets."""
    data_raw_dir = project_root / 'data' / 'raw'
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    
    datasets = [
        ('electricity', download_electricity_dataset, 'electricity.csv'),
        ('traffic', download_traffic_dataset, 'traffic.csv'),
        ('synthetic_control_chart', download_synthetic_control_chart_dataset, 'synthetic_control_chart.csv')
    ]
    
    results = []
    all_success = True
    
    logger.info("=" * 60)
    logger.info("T048: Verifying UCI Dataset Downloads (SC-001 requirement)")
    logger.info("=" * 60)
    
    for name, download_func, expected_filename in datasets:
        logger.info(f"\nProcessing {name} dataset...")
        expected_path = data_raw_dir / expected_filename
        
        # Check if file already exists
        if expected_path.exists():
            file_size = os.path.getsize(expected_path)
            if file_size > 0:
                logger.info(f"  ✓ {expected_filename} already exists ({file_size} bytes)")
                checksum = compute_file_checksum(str(expected_path))
                results.append({
                    'name': name,
                    'success': True,
                    'file_path': str(expected_path),
                    'checksum': checksum,
                    'size': file_size,
                    'status': 'already_exists'
                })
                continue
            else:
                logger.warning(f"  ⚠ {expected_filename} exists but is empty, re-downloading...")
        
        # Download the dataset
        try:
            result = download_func()
            if isinstance(result, DownloadResult):
                if result.success:
                    checksum = compute_file_checksum(str(result.file_path))
                    file_size = os.path.getsize(result.file_path)
                    results.append({
                        'name': name,
                        'success': True,
                        'file_path': str(result.file_path),
                        'checksum': checksum,
                        'size': file_size,
                        'status': 'downloaded'
                    })
                    logger.info(f"  ✓ {name}: {result.file_path.name} ({file_size} bytes, checksum: {checksum[:16]}...)")
                else:
                    error_msg = str(result.error) if result.error else 'Unknown error'
                    results.append({
                        'name': name,
                        'success': False,
                        'error': error_msg,
                        'status': 'failed'
                    })
                    logger.error(f"  ✗ {name}: {error_msg}")
                    all_success = False
            else:
                # Handle case where function returns dict or None
                if result and result.get('success'):
                    file_path = Path(result.get('file_path', ''))
                    if file_path.exists():
                        checksum = compute_file_checksum(str(file_path))
                        file_size = os.path.getsize(file_path)
                        results.append({
                            'name': name,
                            'success': True,
                            'file_path': str(file_path),
                            'checksum': checksum,
                            'size': file_size,
                            'status': 'downloaded'
                        })
                        logger.info(f"  ✓ {name}: {file_path.name} ({file_size} bytes)")
                    else:
                        results.append({
                            'name': name,
                            'success': False,
                            'error': 'File not found after download',
                            'status': 'failed'
                        })
                        logger.error(f"  ✗ {name}: File not found after download")
                        all_success = False
                else:
                    error_msg = result.get('error', 'Download failed') if isinstance(result, dict) else 'Download failed'
                    results.append({
                        'name': name,
                        'success': False,
                        'error': error_msg,
                        'status': 'failed'
                    })
                    logger.error(f"  ✗ {name}: {error_msg}")
                    all_success = False
        except Exception as e:
            results.append({
                'name': name,
                'success': False,
                'error': str(e),
                'status': 'exception'
            })
            logger.error(f"  ✗ {name}: Exception - {e}")
            all_success = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 60)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(datasets)
    
    logger.info(f"Success: {success_count}/{total_count} datasets")
    for r in results:
        status = "✓" if r['success'] else "✗"
        if r['success']:
            logger.info(f"  {status} {r['name']}: {r['file_path'].split('/')[-1]} ({r['size']} bytes, checksum: {r['checksum'][:16]}...)")
        else:
            logger.info(f"  {status} {r['name']}: {r.get('error', 'Unknown error')}")
    
    # Write summary report
    summary_path = project_root / 'data' / 'processed' / 'results' / 'dataset_download_summary.txt'
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, 'w') as f:
        f.write("Dataset Download Summary - T048 Verification\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Date: {__import__('datetime').datetime.now().isoformat()}\n")
        f.write(f"Total datasets: {total_count}\n")
        f.write(f"Successful downloads: {success_count}\n\n")
        f.write("Per-dataset status:\n")
        for r in results:
            f.write(f"  - {r['name']}: {'SUCCESS' if r['success'] else 'FAILED'}\n")
            if r['success']:
                f.write(f"    File: {r['file_path']}\n")
                f.write(f"    Size: {r['size']} bytes\n")
                f.write(f"    Checksum: {r['checksum']}\n")
            else:
                f.write(f"    Error: {r.get('error', 'Unknown')}\n")
        f.write("\n")
        f.write(f"Overall status: {'PASS' if all_success else 'FAIL'}\n")
    
    logger.info(f"\nSummary written to: {summary_path}")
    
    return 0 if all_success else 1

if __name__ == '__main__':
    sys.exit(main())
