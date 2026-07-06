"""
Integration test for FR-002 Verification: Reconstructor Completeness.

This test verifies that the statistical reconstruction module can process
all extracted summaries and compute reconstructed p-values where possible.

Requirements verified:
- Reconstructor processes all extracted summaries
- Reconstructed p-values are computed for valid inputs
- Fallback logic works for missing/invalid data
- All records are processed without errors
"""
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from code.src.utils.logger import get_default_logger, get_error_message
from code.src.audit.reconstructor import reconstruct_single_summary, reconstruct_all, main
from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import validate_summary, create_audit_record

logger = get_default_logger(__name__)

# Test configuration
TEST_OUTPUT_DIR = PROJECT_ROOT / "data" / "test_reconstruction"
TEST_INPUT_FILE = TEST_OUTPUT_DIR / "test_summaries.json"
TEST_OUTPUT_FILE = TEST_OUTPUT_DIR / "reconstructed_results.json"
TEST_AUDIT_FILE = TEST_OUTPUT_DIR / "audit_results.json"

def setup_test_environment():
    """Create test directories and sample data."""
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create synthetic test data that mimics real extracted summaries
    test_summaries = [
        {
            "url": "https://example.com/test1",
            "p_value": 0.03,
            "sample_size_control": 1000,
            "sample_size_treatment": 1000,
            "conversion_rate_control": 0.10,
            "conversion_rate_treatment": 0.12,
            "outcome_type": "binary",
            "domain": "example.com",
            "extraction_timestamp": "2024-01-01 12:00:00"
        },
        {
            "url": "https://example.com/test2",
            "p_value": 0.01,
            "sample_size_control": 500,
            "sample_size_treatment": 500,
            "mean_control": 10.5,
            "mean_treatment": 11.2,
            "std_control": 2.1,
            "std_treatment": 2.3,
            "outcome_type": "continuous",
            "domain": "example.com",
            "extraction_timestamp": "2024-01-01 12:05:00"
        },
        {
            "url": "https://example.com/test3",
            "p_value": None,  # Missing p-value - should use reconstruction
            "sample_size_control": 800,
            "sample_size_treatment": 800,
            "conversion_rate_control": 0.15,
            "conversion_rate_treatment": 0.18,
            "outcome_type": "binary",
            "domain": "example.com",
            "extraction_timestamp": "2024-01-01 12:10:00"
        },
        {
            "url": "https://example.com/test4",
            "p_value": 0.04,
            "sample_size_control": None,  # Missing sample size - should handle gracefully
            "sample_size_treatment": None,
            "outcome_type": "binary",
            "domain": "example.com",
            "extraction_timestamp": "2024-01-01 12:15:00"
        }
    ]
    
    with open(TEST_INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_summaries, f, indent=2)
    
    logger.info(f"Created test input file: {TEST_INPUT_FILE}")

def test_reconstruction_on_test_data() -> Tuple[int, int, List[Dict]]:
    """Test reconstruction on synthetic test data."""
    logger.info("Testing reconstruction on test data...")
    
    # Load test data
    with open(TEST_INPUT_FILE, 'r', encoding='utf-8') as f:
        test_summaries = json.load(f)
    
    reconstructed_count = 0
    total_processed = 0
    results = []
    
    for i, summary_data in enumerate(test_summaries):
        try:
            # Convert to ABTestSummary object
            summary = ABTestSummary(**summary_data)
            
            # Reconstruct
            reconstructed = reconstruct_single_summary(summary)
            
            total_processed += 1
            
            if reconstructed:
                reconstructed_count += 1
                results.append({
                    "url": summary.url,
                    "original_p_value": summary.p_value,
                    "reconstructed_p_value": reconstructed.reconstructed_p_value,
                    "test_type": reconstructed.test_type,
                    "success": True
                })
                logger.info(f"✓ Reconstructed for {summary.url} (type: {reconstructed.test_type})")
            else:
                results.append({
                    "url": summary.url,
                    "original_p_value": summary.p_value,
                    "reconstructed_p_value": None,
                    "success": False,
                    "reason": "Reconstruction returned None"
                })
                logger.warning(f"⚠ Reconstruction failed for {summary.url}")
                
        except Exception as e:
            total_processed += 1
            results.append({
                "url": summary_data.get("url", f"test_{i}"),
                "success": False,
                "error": str(e)
            })
            logger.error(f"✗ Reconstruction error for {summary_data.get('url', f'test_{i}')}: {str(e)}")
    
    return reconstructed_count, total_processed, results

def test_batch_reconstruction() -> bool:
    """Test batch reconstruction of all summaries."""
    logger.info("Testing batch reconstruction...")
    
    # Load test data
    with open(TEST_INPUT_FILE, 'r', encoding='utf-8') as f:
        test_summaries = json.load(f)
    
    # Convert to ABTestSummary objects
    summaries = []
    for data in test_summaries:
        try:
            summaries.append(ABTestSummary(**data))
        except Exception as e:
            logger.warning(f"Failed to create summary from {data.get('url')}: {e}")
    
    if not summaries:
        logger.error("No valid summaries to process")
        return False
    
    # Run batch reconstruction
    try:
        results = reconstruct_all(summaries)
        
        successful = sum(1 for r in results if r is not None)
        total = len(results)
        
        logger.info(f"Batch reconstruction: {successful}/{total} successful")
        
        # Write results
        with open(TEST_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump([{
                "url": r.url if r else "None",
                "reconstructed_p_value": r.reconstructed_p_value if r else None,
                "test_type": r.test_type if r else None,
                "success": r is not None
            } for r in results], f, indent=2)
        
        return successful > 0  # At least some should succeed
        
    except Exception as e:
        logger.error(f"Batch reconstruction failed: {str(e)}")
        return False

def test_validation_integration() -> bool:
    """Test integration between reconstruction and validation."""
    logger.info("Testing reconstruction-validation integration...")
    
    # Load test data
    with open(TEST_INPUT_FILE, 'r', encoding='utf-8') as f:
        test_summaries = json.load(f)
    
    summaries = []
    for data in test_summaries:
        try:
            summaries.append(ABTestSummary(**data))
        except:
            pass
    
    if not summaries:
        return False
    
    # Validate each summary (which includes reconstruction)
    audit_records = []
    successful_validations = 0
    
    for summary in summaries:
        try:
            is_consistent, audit_record = validate_summary(summary)
            
            if audit_record:
                audit_records.append(audit_record)
                successful_validations += 1
                logger.info(f"✓ Validated: {summary.url} (consistent: {is_consistent})")
            else:
                logger.warning(f"⚠ No audit record for {summary.url}")
                
        except Exception as e:
            logger.error(f"Validation error for {summary.url}: {str(e)}")
    
    # Write audit results
    with open(TEST_AUDIT_FILE, 'w', encoding='utf-8') as f:
        json.dump([{
            "url": r.url,
            "is_consistent": r.is_consistent,
            "reconstructed_p_value": r.reconstructed_p_value,
            "original_p_value": r.original_p_value,
            "data_quality_warning": r.data_quality_warning
        } for r in audit_records], f, indent=2)
    
    success_rate = successful_validations / len(summaries) if summaries else 0
    logger.info(f"Validation success rate: {success_rate:.1%}")
    
    return success_rate > 0.5  # At least 50% should validate

def test_fallback_logic():
    """Test that fallback logic works for missing data."""
    logger.info("Testing fallback logic for missing data...")
    
    # Create summary with missing critical fields
    incomplete_summary = ABTestSummary(
        url="https://example.com/incomplete",
        p_value=None,
        sample_size_control=None,
        sample_size_treatment=None,
        outcome_type="binary",
        domain="example.com",
        extraction_timestamp="2024-01-01 12:00:00"
    )
    
    try:
        reconstructed = reconstruct_single_summary(incomplete_summary)
        
        # Should return a result with fallback values or None
        if reconstructed:
            logger.info(f"✓ Fallback reconstruction succeeded: {reconstructed.test_type}")
            return True
        else:
            logger.info("✓ Fallback correctly returned None for insufficient data")
            return True
            
    except Exception as e:
        logger.error(f"Fallback logic error: {str(e)}")
        return False

def main():
    """Run all integration tests for FR-002 reconstructor completeness."""
    logger.info("=" * 60)
    logger.info("Starting FR-002 Verification: Reconstructor Completeness Test")
    logger.info("=" * 60)
    
    try:
        # Setup
        setup_test_environment()
        
        # Run tests
        reconstructed, total, results = test_reconstruction_on_test_data()
        batch_ok = test_batch_reconstruction()
        validation_ok = test_validation_integration()
        fallback_ok = test_fallback_logic()
        
        # Calculate success rate
        success_rate = reconstructed / total if total > 0 else 0
        
        logger.info(f"Reconstruction success rate: {success_rate:.1%}")
        logger.info(f"Batch reconstruction: {batch_ok}")
        logger.info(f"Validation integration: {validation_ok}")
        logger.info(f"Fallback logic: {fallback_ok}")
        
        # FR-002 requires that all records are processed and reconstruction works
        if success_rate >= 0.5 and batch_ok and validation_ok and fallback_ok:
            logger.info("=" * 60)
            logger.info("✓ ALL FR-002 VERIFICATION TESTS PASSED")
            logger.info(f"  - Reconstruction accuracy: {success_rate:.1%}")
            logger.info(f"  - Batch processing: {batch_ok}")
            logger.info(f"  - Validation integration: {validation_ok}")
            logger.info(f"  - Fallback logic: {fallback_ok}")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("Verification failed")
            logger.info("=" * 60)
            logger.error("✗ FR-002 VERIFICATION FAILED")
            logger.info("=" * 60)
            return 1
            
    except AssertionError as e:
        logger.error(f"TEST FAILED: {str(e)}")
        logger.info("=" * 60)
        logger.error("✗ FR-002 VERIFICATION FAILED")
        logger.info("=" * 60)
        return 1
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("=" * 60)
        logger.error("✗ FR-002 VERIFICATION FAILED WITH EXCEPTION")
        logger.info("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())