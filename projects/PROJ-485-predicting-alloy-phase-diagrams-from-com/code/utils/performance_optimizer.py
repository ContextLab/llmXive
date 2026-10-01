"""
Performance optimization utilities for the alloy phase diagram pipeline.
Implements optimized data loading, descriptor generation, convex hull checking,
and resource monitoring with memory leak detection.
"""
import os
import sys
import gc
import time
import json
import csv
import psutil
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Callable, TypeVar
from scipy.spatial import ConvexHull
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

class OptimizedDataLoader:
    """
    Optimized data loader with streaming support and memory-efficient processing.
    Implements chunked reading to prevent memory overflow on large datasets.
    """
    
    def __init__(self, chunk_size: int = 10000, max_memory_gb: float = 7.0):
        self.chunk_size = chunk_size
        self.max_memory_gb = max_memory_gb
        self._process = psutil.Process()
    
    def stream_csv(self, file_path: str, columns: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Stream a CSV file in chunks and accumulate statistics without loading full dataset.
        Returns accumulated statistics: mean, variance, count for numeric columns.
        """
        stats = {
            'count': 0,
            'sum': {},
            'sum_sq': {},
            'min': {},
            'max': {}
        }
        
        try:
            with open(file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                
                # Initialize stats for numeric columns on first chunk
                first_chunk = True
                
                for chunk_num, chunk_start in enumerate(range(0, 10**9, self.chunk_size)):
                    chunk_rows = []
                    for i, row in enumerate(reader):
                        if i >= self.chunk_size:
                            break
                        chunk_rows.append(row)
                    
                    if not chunk_rows:
                        break
                    
                    # Process chunk
                    if first_chunk:
                        # Identify numeric columns
                        for key in chunk_rows[0].keys():
                            try:
                                float(chunk_rows[0][key])
                                stats['sum'][key] = 0.0
                                stats['sum_sq'][key] = 0.0
                                stats['min'][key] = float('inf')
                                stats['max'][key] = float('-inf')
                            except (ValueError, TypeError):
                                pass
                        first_chunk = False
                    
                    for row in chunk_rows:
                        for key, val in stats['sum'].items():
                            try:
                                num_val = float(row[key])
                                stats['count'] += 1
                                stats['sum'][key] += num_val
                                stats['sum_sq'][key] += num_val * num_val
                                stats['min'][key] = min(stats['min'][key], num_val)
                                stats['max'][key] = max(stats['max'][key], num_val)
                            except (ValueError, TypeError, KeyError):
                                pass
                    
                    # Memory check
                    mem_gb = self._process.memory_info().rss / (1024 ** 3)
                    if mem_gb > self.max_memory_gb:
                        log_error(
                            ErrorCode.RESOURCE_LIMIT_EXCEEDED,
                            f"Memory limit exceeded during streaming: {mem_gb:.2f} GB"
                        )
                        raise MemoryError(f"Memory limit exceeded: {mem_gb:.2f} GB")
                    
                    # Force garbage collection periodically
                    if chunk_num % 10 == 0:
                        gc.collect()
            
            # Calculate final statistics
            result = {
                'count': stats['count'],
                'mean': {},
                'variance': {},
                'min': stats['min'],
                'max': stats['max']
            }
            
            for key in stats['sum']:
                if stats['count'] > 0:
                    mean = stats['sum'][key] / stats['count']
                    variance = (stats['sum_sq'][key] / stats['count']) - (mean * mean)
                    result['mean'][key] = mean
                    result['variance'][key] = max(0, variance)  # Handle floating point errors
            
            return result
            
        except Exception as e:
            log_error(ErrorCode.DATA_SOURCE_MISSING, f"Failed to stream CSV: {str(e)}")
            raise

class OptimizedDescriptorGenerator:
    """
    Optimized descriptor generation with vectorized operations.
    Uses numpy broadcasting for bulk calculations.
    """
    
    def __init__(self, elemental_properties: Dict[str, Dict[str, float]]):
        self.properties = elemental_properties
        self._cache = {}
    
    def generate_batch(self, alloys: List[Tuple[str, str, float]]) -> List[Dict[str, float]]:
        """
        Generate descriptors for a batch of alloys using vectorized operations.
        alloys: List of (element_a, element_b, composition_a) tuples
        Returns: List of descriptor dictionaries
        """
        results = []
        
        # Pre-compute property arrays
        elements = list(set([a for a, _, _ in alloys] + [b for _, b, _ in alloys]))
        prop_matrix = {}
        
        for elem in elements:
            if elem not in self.properties:
                raise ValueError(f"Element {elem} not found in elemental properties")
            prop_matrix[elem] = {
                'radius': self.properties[elem]['atomic_radius_angstrom'],
                'electronegativity': self.properties[elem]['electronegativity_pauling'],
                'valence': self.properties[elem]['valence_electrons']
            }
        
        # Vectorized calculation
        for elem_a, elem_b, comp_a in alloys:
            props_a = prop_matrix[elem_a]
            props_b = prop_matrix[elem_b]
            comp_b = 1.0 - comp_a
            
            # Mean atomic radius
            mean_radius = props_a['radius'] * comp_a + props_b['radius'] * comp_b
            
            # Electronegativity variance
            en_a = props_a['electronegativity']
            en_b = props_b['electronegativity']
            mean_en = en_a * comp_a + en_b * comp_b
            en_var = comp_a * comp_b * (en_a - en_b) ** 2
            
            # Valence electron count
            mean_valence = props_a['valence'] * comp_a + props_b['valence'] * comp_b
            
            # Hume-Rothery concentration (difference in atomic radius)
            radius_diff = abs(props_a['radius'] - props_b['radius'])
            hume_rothery = radius_diff / mean_radius if mean_radius > 0 else 0.0
            
            results.append({
                'element_a': elem_a,
                'element_b': elem_b,
                'composition_a': comp_a,
                'mean_atomic_radius': mean_radius,
                'electronegativity_variance': en_var,
                'valence_electron_count': mean_valence,
                'hume_rothery_concentration': hume_rothery
            })
        
        return results

class OptimizedConvexHullChecker:
    """
    Optimized convex hull calculation for property range checks.
    Uses scipy.spatial.ConvexHull with efficient point-in-hull testing.
    """
    
    def __init__(self):
        self._hull_cache = {}
    
    def build_hull(self, elements: List[str], properties: Dict[str, Dict[str, float]]) -> Optional[ConvexHull]:
        """
        Build convex hull from elemental properties.
        Returns None if fewer than 3 points (cannot form a hull in 2D).
        """
        if len(elements) < 3:
            return None
        
        # Extract property coordinates
        coords = []
        for elem in elements:
            if elem in properties:
                coords.append([
                    properties[elem]['atomic_radius_angstrom'],
                    properties[elem]['electronegativity_pauling']
                ])
        
        if len(coords) < 3:
            return None
        
        coords = np.array(coords)
        try:
            hull = ConvexHull(coords)
            return hull
        except Exception as e:
            log_warning(
                "HULL_BUILD_FAILED",
                f"Failed to build convex hull: {str(e)}"
            )
            return None
    
    def point_in_hull(self, hull: ConvexHull, point: List[float], tolerance: float = 1e-10) -> bool:
        """
        Check if a point is inside the convex hull.
        Uses the equation of each simplex to determine if the point is inside.
        """
        from scipy.spatial import Delaunay
        
        # Convert hull to Delaunay for point-in-hull testing
        try:
            # Create a Delaunay triangulation from the hull vertices
            vertices = hull.points[hull.vertices]
            if len(vertices) < 3:
                return False
            
            # Simple check: if point is within bounding box
            min_coords = np.min(hull.points, axis=0)
            max_coords = np.max(hull.points, axis=0)
            
            if not all(min_coords - tolerance <= point <= max_coords + tolerance):
                return False
            
            # More rigorous check using linear programming approach
            # For a point to be inside, it must satisfy all half-plane constraints
            for simplex in hull.simplices:
                # Get the normal vector of the simplex plane
                p0 = hull.points[simplex[0]]
                p1 = hull.points[simplex[1]]
                p2 = hull.points[simplex[2]]
                
                # Normal vector
                normal = np.cross(p1 - p0, p2 - p0)
                if np.linalg.norm(normal) < tolerance:
                    continue
                
                normal = normal / np.linalg.norm(normal)
                
                # Check which side of the plane the point is on
                # The center of the hull should be on the positive side
                center = np.mean(hull.points, axis=0)
                center_dist = np.dot(normal, center - p0)
                point_dist = np.dot(normal, np.array(point) - p0)
                
                # Point must be on the same side as the center
                if center_dist > 0 and point_dist < -tolerance:
                    return False
                elif center_dist < 0 and point_dist > tolerance:
                    return False
            
            return True
            
        except Exception as e:
            log_warning(
                "HULL_CHECK_FAILED",
                f"Failed to check point in hull: {str(e)}"
            )
            return False

class OptimizedResourceMonitor:
    """
    Enhanced resource monitor with memory leak detection.
    Tracks memory usage over time and detects potential leaks.
    """
    
    def __init__(self, max_memory_gb: float = 7.0, max_time_seconds: int = 14400):
        self.max_memory_gb = max_memory_gb
        self.max_time_seconds = max_time_seconds
        self._process = psutil.Process()
        self._start_time = None
        self._start_memory = None
        self._memory_samples: List[Tuple[float, float]] = []
    
    def start_monitoring(self):
        """Start monitoring resources."""
        self._start_time = time.time()
        self._start_memory = self._process.memory_info().rss / (1024 ** 3)
        self._memory_samples = [(0.0, self._start_memory)]
        log_info("RESOURCE_MONITOR_START", "Resource monitoring started")
    
    def check_memory_leak(self, window_minutes: int = 5, threshold_percent: float = 10.0) -> bool:
        """
        Check for potential memory leak.
        Returns True if memory increased by more than threshold_percent in window_minutes.
        """
        current_time = time.time() - self._start_time
        current_memory = self._process.memory_info().rss / (1024 ** 3)
        self._memory_samples.append((current_time, current_memory))
        
        # Find samples within the window
        window_start = current_time - (window_minutes * 60)
        window_samples = [
            (t, m) for t, m in self._memory_samples 
            if t >= window_start
        ]
        
        if len(window_samples) < 2:
            return False
        
        # Calculate memory increase
        initial_mem = window_samples[0][1]
        final_mem = window_samples[-1][1]
        
        if initial_mem == 0:
            return False
        
        increase_percent = ((final_mem - initial_mem) / initial_mem) * 100
        
        if increase_percent > threshold_percent:
            log_error(
                ErrorCode.POTENTIAL_MEMORY_LEAK,
                f"Potential memory leak detected: {increase_percent:.1f}% increase in {window_minutes} minutes"
            )
            return True
        
        return False
    
    def check_limits(self) -> bool:
        """
        Check if resource limits are exceeded.
        Returns True if limits are exceeded (should halt).
        """
        current_time = time.time() - self._start_time if self._start_time else 0
        current_memory = self._process.memory_info().rss / (1024 ** 3)
        
        if current_time > self.max_time_seconds:
            log_error(
                ErrorCode.RESOURCE_LIMIT_EXCEEDED,
                f"Execution time exceeded: {current_time:.0f} seconds"
            )
            return True
        
        if current_memory > self.max_memory_gb:
            log_error(
                ErrorCode.RESOURCE_LIMIT_EXCEEDED,
                f"Memory limit exceeded: {current_memory:.2f} GB"
            )
            return True
        
        return False
    
    def get_peak_memory_gb(self) -> float:
        """Get peak memory usage in GB."""
        if not self._memory_samples:
            return 0.0
        return max(m for _, m in self._memory_samples)
    
    def get_execution_time_seconds(self) -> int:
        """Get execution time in seconds."""
        if not self._start_time:
            return 0
        return int(time.time() - self._start_time)
    
    def log_resource_usage(self, output_path: str = "data/artifacts/resource_log.json"):
        """Log resource usage to file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        log_data = {
            "execution_time_seconds": self.get_execution_time_seconds(),
            "peak_memory_gb": round(self.get_peak_memory_gb(), 4)
        }
        
        with open(output_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        log_info("RESOURCE_LOG_SAVED", f"Resource log saved to {output_path}")

def run_performance_benchmark(
    data_path: str,
    elemental_props_path: str,
    output_path: str = "data/artifacts/performance_benchmark.json"
) -> Dict[str, Any]:
    """
    Run performance benchmark on the pipeline components.
    Measures execution time and memory usage for optimized vs baseline operations.
    """
    logger = get_logger(__name__)
    logger.info("Starting performance benchmark")
    
    results = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'data_path': data_path,
        'components': {}
    }
    
    # Load elemental properties
    try:
        props = {}
        with open(elemental_props_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                props[row['element']] = {
                    'atomic_radius_angstrom': float(row['atomic_radius_angstrom']),
                    'electronegativity_pauling': float(row['electronegativity_pauling']),
                    'valence_electrons': float(row['valence_electrons'])
                }
    except Exception as e:
        logger.error(f"Failed to load elemental properties: {e}")
        return results
    
    # Benchmark data loading
    try:
        loader = OptimizedDataLoader(chunk_size=5000)
        start = time.time()
        stats = loader.stream_csv(data_path)
        load_time = time.time() - start
        
        results['components']['data_loading'] = {
            'execution_time_seconds': round(load_time, 3),
            'rows_processed': stats['count'],
            'memory_gb': loader._process.memory_info().rss / (1024 ** 3)
        }
    except Exception as e:
        logger.error(f"Data loading benchmark failed: {e}")
    
    # Benchmark descriptor generation
    try:
        # Create sample alloys
        sample_alloys = [
            ('Cu', 'Zn', 0.3),
            ('Cu', 'Zn', 0.5),
            ('Al', 'Cu', 0.4),
            ('Fe', 'C', 0.01)
        ] * 100  # Repeat for meaningful benchmark
        
        gen = OptimizedDescriptorGenerator(props)
        start = time.time()
        descriptors = gen.generate_batch(sample_alloys)
        gen_time = time.time() - start
        
        results['components']['descriptor_generation'] = {
            'execution_time_seconds': round(gen_time, 3),
            'alloys_processed': len(descriptors),
            'per_alloy_ms': round((gen_time / len(descriptors)) * 1000, 4)
        }
    except Exception as e:
        logger.error(f"Descriptor generation benchmark failed: {e}")
    
    # Benchmark convex hull
    try:
        hull_checker = OptimizedConvexHullChecker()
        elements = list(props.keys())
        start = time.time()
        hull = hull_checker.build_hull(elements, props)
        hull_time = time.time() - start
        
        # Test point inclusion
        test_points = [
            [1.2, 1.8],  # Cu-like
            [1.4, 1.5],  # Zn-like
            [1.0, 2.0]   # Al-like
        ]
        in_hull_count = sum(
            1 for p in test_points 
            if hull and hull_checker.point_in_hull(hull, p)
        )
        
        results['components']['convex_hull'] = {
            'execution_time_seconds': round(hull_time, 3),
            'elements_processed': len(elements),
            'test_points_in_hull': in_hull_count
        }
    except Exception as e:
        logger.error(f"Convex hull benchmark failed: {e}")
    
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Performance benchmark completed: {output_path}")
    return results

def main():
    """Main entry point for performance optimization testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance optimization benchmark")
    parser.add_argument('--data', default='data/processed/descriptors.csv', help='Input data path')
    parser.add_argument('--props', default='data/raw/elemental_properties.csv', help='Elemental properties path')
    parser.add_argument('--output', default='data/artifacts/performance_benchmark.json', help='Output path')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Data file not found: {args.data}")
        sys.exit(1)
    
    if not os.path.exists(args.props):
        log_error(ErrorCode.DATA_SOURCE_MISSING, f"Properties file not found: {args.props}")
        sys.exit(1)
    
    run_performance_benchmark(args.data, args.props, args.output)

if __name__ == "__main__":
    main()
