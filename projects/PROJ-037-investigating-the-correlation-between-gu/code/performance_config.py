"""
Performance configuration for the gut microbiome and circadian rhythm study.

This module defines configuration settings for optimizing pipeline performance
to meet the < 6h runtime target on N=200 samples.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class PerformanceConfig:
    """Configuration for performance optimization."""
    
    # Parallelism settings
    n_jobs: int = 4  # Conservative default
    max_workers: int = 4
    
    # Memory management
    chunk_size: int = 1000  # Rows per chunk for large file processing
    memory_limit_mb: int = 4000  # Maximum memory usage in MB
    
    # Caching
    enable_cache: bool = True
    cache_dir: str = "data/cache"
    
    # Time limits
    max_runtime_seconds: int = 6 * 3600  # 6 hours
    timeout_per_step_seconds: int = 30 * 60  # 30 minutes per step
    
    # Optimization flags
    optimize_memory: bool = True
    parallelize_diversity: bool = True
    parallelize_correlations: bool = True
    
    # Logging
    log_performance: bool = True
    performance_log_path: str = "data/outputs/performance.log"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'n_jobs': self.n_jobs,
            'max_workers': self.max_workers,
            'chunk_size': self.chunk_size,
            'memory_limit_mb': self.memory_limit_mb,
            'enable_cache': self.enable_cache,
            'cache_dir': self.cache_dir,
            'max_runtime_seconds': self.max_runtime_seconds,
            'timeout_per_step_seconds': self.timeout_per_step_seconds,
            'optimize_memory': self.optimize_memory,
            'parallelize_diversity': self.parallelize_diversity,
            'parallelize_correlations': self.parallelize_correlations,
            'log_performance': self.log_performance,
            'performance_log_path': self.performance_log_path
        }
    
    @classmethod
    def from_env(cls) -> 'PerformanceConfig':
        """Create config from environment variables."""
        return cls(
            n_jobs=int(os.getenv('N_JOBS', '4')),
            max_workers=int(os.getenv('MAX_WORKERS', '4')),
            chunk_size=int(os.getenv('CHUNK_SIZE', '1000')),
            memory_limit_mb=int(os.getenv('MEMORY_LIMIT_MB', '4000')),
            enable_cache=os.getenv('ENABLE_CACHE', 'true').lower() == 'true',
            cache_dir=os.getenv('CACHE_DIR', 'data/cache'),
            max_runtime_seconds=int(os.getenv('MAX_RUNTIME_SECONDS', str(6 * 3600))),
            timeout_per_step_seconds=int(os.getenv('TIMEOUT_PER_STEP_SECONDS', str(30 * 60))),
            optimize_memory=os.getenv('OPTIMIZE_MEMORY', 'true').lower() == 'true',
            parallelize_diversity=os.getenv('PARALLELIZE_DIVERSITY', 'true').lower() == 'true',
            parallelize_correlations=os.getenv('PARALLELIZE_CORRELATIONS', 'true').lower() == 'true',
            log_performance=os.getenv('LOG_PERFORMANCE', 'true').lower() == 'true',
            performance_log_path=os.getenv('PERFORMANCE_LOG_PATH', 'data/outputs/performance.log')
        )

# Global configuration instance
_config: Optional[PerformanceConfig] = None

def get_performance_config() -> PerformanceConfig:
    """Get the global performance configuration."""
    global _config
    if _config is None:
        _config = PerformanceConfig.from_env()
    return _config

def set_performance_config(config: PerformanceConfig):
    """Set the global performance configuration."""
    global _config
    _config = config

def reset_performance_config():
    """Reset the global performance configuration to defaults."""
    global _config
    _config = None
