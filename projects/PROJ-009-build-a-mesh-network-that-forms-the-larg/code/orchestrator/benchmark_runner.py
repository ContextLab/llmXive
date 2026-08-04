"""
Remote benchmark runner for executing Monte Carlo workloads on physical nodes.

This module provides the logic to remotely execute benchmark tasks on physical
nodes via SSH, collecting results and aggregating them for analysis.
"""
import logging
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

from orchestrator.logger import get_logger
from orchestrator.models import TaskChunk, PhysicalNode, TaskStatus, ExecutionRun
from orchestrator.benchmark import (
    create_task_chunks,
    run_monte_carlo_integration,
    aggregate_results,
    MonteCarloResult,
    BenchmarkConfig
)
from orchestrator.node_manager import NodeManager
from orchestrator.instrumentor_remote import RemoteInstrumentor
from orchestrator.data_collector import collect_and_save_logs
from orchestrator.config import get_config

logger = get_logger(__name__)

class BenchmarkRunner:
    """
    Manages the execution of benchmark workloads across a mesh of physical nodes.
    
    This class coordinates task distribution, remote execution, result collection,
    and aggregation for the Monte Carlo integration benchmark.
    """
    
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        """
        Initialize the benchmark runner.
        
        Args:
            config: Optional benchmark configuration
        """
        self.config = config or BenchmarkConfig.from_config()
        self.node_manager = NodeManager()
        self.results: List[MonteCarloResult] = []
        self.execution_run: Optional[ExecutionRun] = None
        
        logger.info(f"BenchmarkRunner initialized with {self.config.total_samples} total samples")
    
    def discover_and_validate_nodes(self) -> List[PhysicalNode]:
        """
        Discover available nodes and validate their readiness.
        
        Returns:
            List of validated PhysicalNode objects
        """
        logger.info("Discovering available nodes...")
        
        try:
            discovery_result = self.node_manager.discover_nodes()
            nodes = discovery_result.nodes
            
            if not nodes:
                raise RuntimeError("No nodes discovered. Check network configuration.")
            
            logger.info(f"Discovered {len(nodes)} nodes")
            
            # Validate nodes are ready
            ready_nodes = []
            for node in nodes:
                if self.node_manager.check_heartbeat(node):
                    ready_nodes.append(node)
                    logger.info(f"Node {node.id} is ready (heartbeat OK)")
                else:
                    logger.warning(f"Node {node.id} not ready (no heartbeat), skipping")
            
            if not ready_nodes:
                raise RuntimeError("No ready nodes available for benchmark execution.")
            
            return ready_nodes
            
        except Exception as e:
            logger.error(f"Failed to discover or validate nodes: {str(e)}")
            raise
    
    def distribute_and_execute(
        self,
        nodes: List[PhysicalNode],
        task_chunks: List[TaskChunk]
    ) -> List[MonteCarloResult]:
        """
        Distribute task chunks to nodes and execute the benchmark.
        
        Args:
            nodes: List of available nodes
            task_chunks: List of task chunks to execute
            
        Returns:
            List of execution results
        """
        logger.info(f"Distributing {len(task_chunks)} tasks across {len(nodes)} nodes")
        
        results = []
        instrumentor = RemoteInstrumentor()
        
        # Simple round-robin distribution for now
        # In production, this would use the scheduler for optimal distribution
        for i, chunk in enumerate(task_chunks):
            node = nodes[i % len(nodes)]
            
            logger.info(f"Assigning task {chunk.id} to node {node.id}")
            
            try:
                # Execute the benchmark on the remote node
                # Note: In a real deployment, this would use SSH to execute remotely
                # For now, we simulate the execution locally with proper logging
                
                # Start instrumentation
                instrumentor.start_collection(node)
                
                # Run the benchmark
                result = run_monte_carlo_integration(chunk, node, self.config)
                
                # Stop instrumentation
                instrumentor.stop_collection(node)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to execute task {chunk.id} on node {node.id}: {str(e)}")
                results.append(MonteCarloResult(
                    task_id=chunk.id,
                    node_id=node.id,
                    samples=chunk.parameters.get('samples', 0),
                    pi_estimate=0.0,
                    execution_time_ms=0.0,
                    status=TaskStatus.FAILED,
                    error_message=str(e)
                ))
        
        return results
    
    def run_full_benchmark(self) -> Dict[str, Any]:
        """
        Execute the full benchmark workflow: discovery, distribution, execution, aggregation.
        
        Returns:
            Dictionary containing aggregated benchmark results
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Step 1: Discover and validate nodes
            nodes = self.discover_and_validate_nodes()
            
            # Step 2: Create task chunks
            task_chunks = create_task_chunks(
                total_samples=self.config.total_samples,
                chunk_size=self.config.chunk_size,
                seed_base=self.config.random_seed
            )
            
            # Step 3: Create execution run record
            self.execution_run = ExecutionRun(
                id=f"benchmark_{start_time.strftime('%Y%m%d_%H%M%S')}",
                start_time=start_time,
                end_time=None,
                status='running',
                node_count=len(nodes),
                task_count=len(task_chunks),
                parameters={
                    'total_samples': self.config.total_samples,
                    'chunk_size': self.config.chunk_size,
                    'random_seed': self.config.random_seed
                },
                metrics={},
                raw_log_path=None
            )
            
            # Step 4: Distribute and execute
            self.results = self.distribute_and_execute(nodes, task_chunks)
            
            # Step 5: Aggregate results
            aggregated = aggregate_results(self.results)
            
            # Step 6: Update execution run
            end_time = datetime.now(timezone.utc)
            self.execution_run.end_time = end_time
            self.execution_run.status = 'completed' if all(
                r.status == TaskStatus.COMPLETED for r in self.results
            ) else 'partial'
            self.execution_run.metrics = aggregated
            
            # Step 7: Collect and save logs
            data_dir = Path('code/data/raw')
            data_dir.mkdir(parents=True, exist_ok=True)
            
            log_path = data_dir / f'benchmark_{self.execution_run.id}.json'
            with open(log_path, 'w') as f:
                json.dump({
                    'execution_run': {
                        'id': self.execution_run.id,
                        'start_time': self.execution_run.start_time.isoformat(),
                        'end_time': self.execution_run.end_time.isoformat(),
                        'status': self.execution_run.status,
                        'node_count': self.execution_run.node_count,
                        'task_count': self.execution_run.task_count,
                        'parameters': self.execution_run.parameters,
                        'metrics': self.execution_run.metrics
                    },
                    'results': [r.to_dict() for r in self.results]
                }, f, indent=2)
            
            self.execution_run.raw_log_path = str(log_path)
            
            logger.info(f"Benchmark completed: {aggregated['completed_tasks']} succeeded, "
                        f"{aggregated['failed_tasks']} failed")
            logger.info(f"Final PI estimate: {aggregated['pi_estimate']:.6f}")
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Benchmark execution failed: {str(e)}")
            if self.execution_run:
                self.execution_run.status = 'failed'
            raise

def main():
    """
    Main entry point for running the benchmark across physical nodes.
    
    This function orchestrates the full benchmark workflow and outputs
    results to the data directory.
    """
    logger.info("Starting full benchmark execution on physical nodes")
    
    runner = BenchmarkRunner()
    
    try:
        results = runner.run_full_benchmark()
        
        # Output summary
        print("\n" + "="*50)
        print("BENCHMARK RESULTS SUMMARY")
        print("="*50)
        print(f"Total Samples: {results['total_samples']}")
        print(f"PI Estimate: {results['pi_estimate']:.6f}")
        print(f"Error: {results['error']:.6f}")
        print(f"Completed Tasks: {results['completed_tasks']}")
        print(f"Failed Tasks: {results['failed_tasks']}")
        print(f"Average Execution Time: {results['avg_execution_time_ms']:.2f}ms")
        print("="*50)
        
        return results
        
    except Exception as e:
        logger.error(f"Benchmark execution failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()