"""
Tests for performance optimization components.
Verifies that optimized components work correctly and meet performance targets.
"""
import os
import sys
import json
import tempfile
import csv
import time
import unittest
import numpy as np
from scipy.spatial import ConvexHull

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from utils.performance_optimizer import (
    OptimizedDataLoader,
    OptimizedDescriptorGenerator,
    OptimizedConvexHullChecker,
    OptimizedResourceMonitor,
    run_performance_benchmark
)
from utils.error_codes import ErrorCode
from utils.logging import get_logger

logger = get_logger(__name__)

class TestOptimizedDataLoader(unittest.TestCase):
    """Tests for OptimizedDataLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = [
            {'element_a': 'Cu', 'element_b': 'Zn', 'composition_a': '0.3', 'temperature': '1000'},
            {'element_a': 'Cu', 'element_b': 'Zn', 'composition_a': '0.5', 'temperature': '1100'},
            {'element_a': 'Al', 'element_b': 'Cu', 'composition_a': '0.4', 'temperature': '900'},
            {'element_a': 'Fe', 'element_b': 'C', 'composition_a': '0.01', 'temperature': '1500'},
        ]
        
        # Create temporary CSV file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        writer = csv.DictWriter(self.temp_file, fieldnames=self.test_data[0].keys())
        writer.writeheader()
        writer.writerows(self.test_data)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_stream_csv_basic(self):
        """Test basic CSV streaming functionality."""
        loader = OptimizedDataLoader(chunk_size=2)
        stats = loader.stream_csv(self.temp_file.name)
        
        self.assertEqual(stats['count'], 4)
        self.assertIn('mean', stats)
        self.assertIn('variance', stats)
        self.assertIn('min', stats)
        self.assertIn('max', stats)
    
    def test_stream_csv_memory_check(self):
        """Test memory limit checking during streaming."""
        loader = OptimizedDataLoader(chunk_size=2, max_memory_gb=0.001)  # Very low limit
        
        # This should raise MemoryError due to artificial limit
        with self.assertRaises(MemoryError):
            loader.stream_csv(self.temp_file.name)
    
    def test_stream_csv_empty_file(self):
        """Test streaming an empty CSV file."""
        # Create empty CSV
        empty_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        empty_file.write('col1,col2\n')
        empty_file.close()
        
        try:
            loader = OptimizedDataLoader()
            stats = loader.stream_csv(empty_file.name)
            self.assertEqual(stats['count'], 0)
        finally:
            os.remove(empty_file.name)

class TestOptimizedDescriptorGenerator(unittest.TestCase):
    """Tests for OptimizedDescriptorGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.elemental_properties = {
            'Cu': {
                'atomic_radius_angstrom': 1.28,
                'electronegativity_pauling': 1.90,
                'valence_electrons': 1
            },
            'Zn': {
                'atomic_radius_angstrom': 1.34,
                'electronegativity_pauling': 1.65,
                'valence_electrons': 2
            },
            'Al': {
                'atomic_radius_angstrom': 1.43,
                'electronegativity_pauling': 1.61,
                'valence_electrons': 3
            },
            'Fe': {
                'atomic_radius_angstrom': 1.24,
                'electronegativity_pauling': 1.83,
                'valence_electrons': 2
            },
            'C': {
                'atomic_radius_angstrom': 0.77,
                'electronegativity_pauling': 2.55,
                'valence_electrons': 4
            }
        }
        
        self.generator = OptimizedDescriptorGenerator(self.elemental_properties)
    
    def test_generate_batch_basic(self):
        """Test basic batch descriptor generation."""
        alloys = [
            ('Cu', 'Zn', 0.5),
            ('Al', 'Cu', 0.3)
        ]
        
        results = self.generator.generate_batch(alloys)
        
        self.assertEqual(len(results), 2)
        self.assertIn('mean_atomic_radius', results[0])
        self.assertIn('electronegativity_variance', results[0])
        self.assertIn('valence_electron_count', results[0])
        self.assertIn('hume_rothery_concentration', results[0])
    
    def test_generate_batch_missing_element(self):
        """Test error handling for missing element."""
        alloys = [('Cu', 'Unknown', 0.5)]
        
        with self.assertRaises(ValueError):
            self.generator.generate_batch(alloys)
    
    def test_generate_batch_vectorized(self):
        """Test that vectorized operations produce correct results."""
        # Cu-Zn 50-50
        # Mean radius = (1.28 + 1.34) / 2 = 1.31
        # EN variance = 0.5 * 0.5 * (1.90 - 1.65)^2 = 0.25 * 0.0625 = 0.015625
        alloys = [('Cu', 'Zn', 0.5)]
        results = self.generator.generate_batch(alloys)
        
        self.assertAlmostEqual(results[0]['mean_atomic_radius'], 1.31, places=2)
        self.assertAlmostEqual(results[0]['electronegativity_variance'], 0.015625, places=4)

class TestOptimizedConvexHullChecker(unittest.TestCase):
    """Tests for OptimizedConvexHullChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.properties = {
            'Cu': {
                'atomic_radius_angstrom': 1.28,
                'electronegativity_pauling': 1.90
            },
            'Zn': {
                'atomic_radius_angstrom': 1.34,
                'electronegativity_pauling': 1.65
            },
            'Al': {
                'atomic_radius_angstrom': 1.43,
                'electronegativity_pauling': 1.61
            },
            'Fe': {
                'atomic_radius_angstrom': 1.24,
                'electronegativity_pauling': 1.83
            }
        }
        
        self.checker = OptimizedConvexHullChecker()
    
    def test_build_hull_basic(self):
        """Test basic convex hull building."""
        elements = ['Cu', 'Zn', 'Al']
        hull = self.checker.build_hull(elements, self.properties)
        
        self.assertIsNotNone(hull)
        self.assertIsInstance(hull, ConvexHull)
    
    def test_build_hull_insufficient_points(self):
        """Test hull building with insufficient points."""
        elements = ['Cu', 'Zn']  # Only 2 points
        hull = self.checker.build_hull(elements, self.properties)
        
        self.assertIsNone(hull)
    
    def test_point_in_hull(self):
        """Test point-in-hull checking."""
        elements = ['Cu', 'Zn', 'Al']
        hull = self.checker.build_hull(elements, self.properties)
        
        # Point inside (centroid)
        center = [
            (self.properties['Cu']['atomic_radius_angstrom'] + 
             self.properties['Zn']['atomic_radius_angstrom'] + 
             self.properties['Al']['atomic_radius_angstrom']) / 3,
            (self.properties['Cu']['electronegativity_pauling'] + 
             self.properties['Zn']['electronegativity_pauling'] + 
             self.properties['Al']['electronegativity_pauling']) / 3
        ]
        
        self.assertTrue(self.checker.point_in_hull(hull, center))
        
        # Point outside (far away)
        outside_point = [10.0, 10.0]
        self.assertFalse(self.checker.point_in_hull(hull, outside_point))

class TestOptimizedResourceMonitor(unittest.TestCase):
    """Tests for OptimizedResourceMonitor class."""
    
    def test_start_monitoring(self):
        """Test starting resource monitoring."""
        monitor = OptimizedResourceMonitor()
        monitor.start_monitoring()
        
        self.assertIsNotNone(monitor._start_time)
        self.assertIsNotNone(monitor._start_memory)
    
    def test_check_limits_time(self):
        """Test time limit checking."""
        monitor = OptimizedResourceMonitor(max_time_seconds=1)
        monitor.start_monitoring()
        
        # Should pass initially
        self.assertFalse(monitor.check_limits())
        
        # Wait and check again (simulated)
        monitor._start_time = time.time() - 10  # Pretend 10 seconds passed
        self.assertTrue(monitor.check_limits())
    
    def test_check_limits_memory(self):
        """Test memory limit checking."""
        monitor = OptimizedResourceMonitor(max_memory_gb=0.001)  # Very low limit
        monitor.start_monitoring()
        
        # Should fail due to low limit
        self.assertTrue(monitor.check_limits())
    
    def test_log_resource_usage(self):
        """Test logging resource usage."""
        monitor = OptimizedResourceMonitor()
        monitor.start_monitoring()
        
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_output.close()
        
        try:
            monitor.log_resource_usage(temp_output.name)
            
            with open(temp_output.name, 'r') as f:
                data = json.load(f)
            
            self.assertIn('execution_time_seconds', data)
            self.assertIn('peak_memory_gb', data)
        finally:
            os.remove(temp_output.name)

class TestRunPerformanceBenchmark(unittest.TestCase):
    """Tests for run_performance_benchmark function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create test data file
        self.temp_data = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        writer = csv.DictWriter(
            self.temp_data, 
            fieldnames=['element_a', 'element_b', 'composition_a', 'temperature']
        )
        writer.writeheader()
        for i in range(100):
            writer.writerow({
                'element_a': 'Cu',
                'element_b': 'Zn',
                'composition_a': str(0.1 * (i % 10)),
                'temperature': str(1000 + i * 10)
            })
        self.temp_data.close()
        
        # Create test properties file
        self.temp_props = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
        writer = csv.DictWriter(
            self.temp_props,
            fieldnames=['element', 'atomic_radius_angstrom', 'electronegativity_pauling', 'valence_electrons']
        )
        writer.writeheader()
        writer.writerow({'element': 'Cu', 'atomic_radius_angstrom': '1.28', 'electronegativity_pauling': '1.90', 'valence_electrons': '1'})
        writer.writerow({'element': 'Zn', 'atomic_radius_angstrom': '1.34', 'electronegativity_pauling': '1.65', 'valence_electrons': '2'})
        writer.writerow({'element': 'Al', 'atomic_radius_angstrom': '1.43', 'electronegativity_pauling': '1.61', 'valence_electrons': '3'})
        self.temp_props.close()
        
        self.temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_output.close()
    
    def tearDown(self):
        """Clean up temporary files."""
        for f in [self.temp_data, self.temp_props, self.temp_output]:
            if os.path.exists(f.name):
                os.remove(f.name)
    
    def test_run_benchmark_basic(self):
        """Test basic benchmark execution."""
        results = run_performance_benchmark(
            self.temp_data.name,
            self.temp_props.name,
            self.temp_output.name
        )
        
        self.assertIn('components', results)
        self.assertTrue(os.path.exists(self.temp_output.name))
        
        # Check output file content
        with open(self.temp_output.name, 'r') as f:
            output_data = json.load(f)
        
        self.assertIn('timestamp', output_data)
        self.assertIn('components', output_data)

if __name__ == '__main__':
    unittest.main()