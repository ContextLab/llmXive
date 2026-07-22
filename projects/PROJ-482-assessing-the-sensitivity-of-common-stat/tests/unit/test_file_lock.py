import pytest
import os
import tempfile
import csv
from code.utils.file_lock import file_lock, write_pvalue_batch

def test_file_lock_context_manager():
    """Test that file_lock context manager properly acquires and releases lock."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name
        f.write("test\n")
    
    try:
        with file_lock(temp_path, 'r') as f:
            content = f.read()
            assert content == "test\n"
        
        # File should be accessible after context
        with open(temp_path, 'r') as f:
            assert f.read() == "test\n"
    finally:
        os.unlink(temp_path)

def test_write_pvalue_batch():
    """Test writing p-value records to CSV."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name
    
    try:
        records = [
            {'sample_size': 10, 'distribution_type': 'normal', 'test_type': 't_test', 'p_value': 0.03, 'hypothesis_type': 'null'},
            {'sample_size': 20, 'distribution_type': 'uniform', 'test_type': 'anova', 'p_value': 0.15, 'hypothesis_type': 'alternative'}
        ]
        
        schema = {
            'sample_size': 'int',
            'distribution_type': 'string',
            'test_type': 'string',
            'p_value': 'float',
            'hypothesis_type': 'string'
        }
        
        count = write_pvalue_batch(temp_path, records, schema)
        assert count == 2
        
        # Verify file contents
        with open(temp_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['sample_size'] == '10'
            assert rows[0]['p_value'] == '0.03'
    finally:
        os.unlink(temp_path)

def test_write_pvalue_batch_header_creation():
    """Test that header is written only on first write."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name
    
    try:
        schema = {
            'sample_size': 'int',
            'distribution_type': 'string',
            'test_type': 'string',
            'p_value': 'float',
            'hypothesis_type': 'string'
        }
        
        # First write
        records1 = [{'sample_size': 10, 'distribution_type': 'normal', 'test_type': 't_test', 'p_value': 0.03, 'hypothesis_type': 'null'}]
        write_pvalue_batch(temp_path, records1, schema)
        
        # Second write
        records2 = [{'sample_size': 20, 'distribution_type': 'uniform', 'test_type': 'anova', 'p_value': 0.15, 'hypothesis_type': 'alternative'}]
        write_pvalue_batch(temp_path, records2, schema)
        
        # Verify only one header
        with open(temp_path, 'r') as f:
            lines = f.readlines()
            header_count = sum(1 for line in lines if line.strip() == 'sample_size,distribution_type,test_type,p_value,hypothesis_type')
            assert header_count == 1
            assert len(lines) == 3  # 1 header + 2 data rows
    finally:
        os.unlink(temp_path)
