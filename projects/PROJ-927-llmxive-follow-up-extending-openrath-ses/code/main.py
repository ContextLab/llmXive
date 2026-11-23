import argparse
import os
import sys
import time
import signal
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import itertools

# Local imports based on provided API surface
from config import (
    ensure_directories, 
    load_state, 
    save_state, 
    SEED, 
    CORRUPTION_RATE, 
    WORKFLOW_COUNT, 
    SWEEP_RATES,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    STATE_DIR
)
from generators.workflow_generator import (
    generate_workflow, 
    generate_ground_truth_batch, 
    verify_ground_truth_hashes
)
from simulators.corruption_injector import CorruptionInjector
from simulators.corruption_log_manager import (
    load_corruption_map, 
    save_corruption_map,
    get_corruption_map_path
)
from executors.event_log_executor import EventLogExecutor
from executors.session_first_executor import SessionFirstExecutor
from reconstructors.reconstruction_engine import ReconstructionEngine
from analyzers.metrics_calculator import MetricsCalculator
from analyzers.statistical_test import run_statistical_tests
from utils.checksum_manager import update_artifact_hashes, scan_directory_for_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(STATE_DIR, 'pipeline.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def parse_args():
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline")
    parser.add_argument('--seed', type=int, default=SEED, help='Random seed')
    parser.add_argument('--count', type=int, default=WORKFLOW_COUNT, help='Number of workflows to generate')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    parser.add_argument('--corruption-rate', type=float, default=CORRUPTION_RATE, help='Corruption rate for injection')
    parser.add_argument('--sweep', action='store_true', help='Run sensitivity sweep over SWEEP_RATES')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')
    parser.add_argument('--streaming', action='store_true', help='Enable streaming mode for memory efficiency')
    
    # Explicitly add phase and architecture arguments to fix CLI mismatch
    parser.add_argument('--phase', type=str, choices=['generate', 'simulate', 'reconstruct', 'analyze'], 
                      help='Specific phase to run (overrides full pipeline)')
    parser.add_argument('--corruption-rates', type=str, 
                      help='Comma-separated list of corruption rates (overrides config)')
    parser.add_argument('--architectures', type=str, 
                      help='Comma-separated list of architectures: event_log, session_first')
    parser.add_argument('--test', type=str, 
                      help='Specific statistical test to run (e.g., cochrans_q)')

    return parser.parse_args()

def load_checkpoint():
    checkpoint_path = os.path.join(STATE_DIR, 'projects', 'PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml')
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r') as f:
            import yaml
            return yaml.safe_load(f)
    return {}

def save_checkpoint(data):
    checkpoint_path = os.path.join(STATE_DIR, 'projects', 'PROJ-927-llmxive-follow-up-extending-openrath-ses.yaml')
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
    with open(checkpoint_path, 'w') as f:
        import yaml
        yaml.dump(data, f)

def get_workflows_to_process(total_count: int, resume: bool) -> List[int]:
    if not resume:
        return list(range(total_count))
    
    checkpoint = load_checkpoint()
    last_id = checkpoint.get('checkpoint', {}).get('last_workflow_id', -1)
    status = checkpoint.get('checkpoint', {}).get('status', 'idle')
    
    logger.info(f"Resuming from workflow ID {last_id}, status: {status}")
    return list(range(last_id + 1, total_count))

def process_single_workflow(workflow_id: int, seed: int, corruption_rate: float, streaming: bool = False):
    """
    Process a single workflow: Generate -> Execute -> Corrupt -> Reconstruct -> Analyze.
    Implements streaming/batching logic to stay under memory constraints.
    """
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(300) # 5 min timeout per workflow to prevent hang

    try:
        # 1. Generate Workflow (if not already done in batch)
        # Assuming generation is handled in batch for efficiency, 
        # but we validate existence here.
        gt_path = os.path.join(RAW_DATA_DIR, 'workflows', f'{workflow_id}_ground_truth.json')
        if not os.path.exists(gt_path):
            logger.warning(f"Ground truth missing for {workflow_id}, generating on fly.")
            # In a real streaming scenario, we might generate here, 
            # but T012/T013 implies batch generation. 
            # For T043 optimization, we assume batch generation happened.
            # If we must generate here for streaming:
            # wf_data = generate_workflow(workflow_id, seed)
            # ... save ...
            raise FileNotFoundError(f"Ground truth {gt_path} not found. Run generation phase first.")

        # 2. Execute (Simulate)
        # We stream execution results to avoid holding all in memory
        exec_results = []
        
        # Determine architectures
        archs = ['event_log', 'session_first'] # Default from T025 logic
        
        for arch in archs:
            start_time = time.time()
            if arch == 'event_log':
                executor = EventLogExecutor(seed=seed + workflow_id)
            else:
                executor = SessionFirstExecutor(seed=seed + workflow_id)
            
            # Execute workflow
            result = executor.execute_workflow(workflow_id)
            exec_results.append({
                'architecture': arch,
                'result': result,
                'latency': time.time() - start_time
            })
            
            # Streaming: Write intermediate results to disk immediately to free RAM
            result_path = os.path.join(
                PROCESSED_DATA_DIR, 'results', f'{workflow_id}_{arch}_result.json'
            )
            os.makedirs(os.path.dirname(result_path), exist_ok=True)
            with open(result_path, 'w') as f:
                json.dump(result, f)
            
            del result # Explicit delete for memory management

        # 3. Inject Corruption
        # Load workflow data, corrupt, save
        injector = CorruptionInjector(corruption_rate=corruption_rate)
        corrupted_logs = injector.inject_corruption(workflow_id, exec_results)
        
        # Save corruption map update
        corruption_map = load_corruption_map()
        corruption_map[workflow_id] = corrupted_logs
        save_corruption_map(corruption_map)

        # 4. Reconstruct
        engine = ReconstructionEngine()
        recon_results = {}
        
        for arch in archs:
            try:
                # Stream reconstruction logic
                recon_state = engine.reconstruct(workflow_id, arch, corrupted_logs)
                recon_results[arch] = {
                    'success': recon_state.get('success', False),
                    'state': recon_state.get('state', {}),
                    'latency': recon_state.get('latency', 0)
                }
            except Exception as e:
                logger.error(f"Reconstruction failed for {workflow_id}/{arch}: {e}")
                recon_results[arch] = {'success': False, 'error': str(e)}

        # 5. Analyze (Local metrics)
        # Calculate metrics for this workflow immediately
        metrics = MetricsCalculator.calculate_workflow_metrics(
            workflow_id, 
            recon_results, 
            gt_path
        )
        
        # Save individual metrics
        metrics_path = os.path.join(
            PROCESSED_DATA_DIR, 'results', f'{workflow_id}_metrics.json'
        )
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f)

        return metrics

    except TimeoutError:
        logger.error(f"Workflow {workflow_id} timed out.")
        return {'status': 'timeout'}
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {e}")
        return {'status': 'error', 'message': str(e)}
    finally:
        signal.alarm(0)

def run_sweep(args):
    """
    Runs the full pipeline for a set of corruption rates.
    Optimized for batch processing and streaming.
    """
    rates = [float(r) for r in args.corruption_rates.split(',')] if args.corruption_rates else SWEEP_RATES
    archs = args.architectures.split(',') if args.architectures else ['event_log', 'session_first']
    
    logger.info(f"Starting sweep with rates: {rates}, architectures: {archs}")

    for rate in rates:
        logger.info(f"Processing corruption rate: {rate}")
        
        # Batch generation (T012/T013)
        # Assuming we generate all workflows for this rate or reuse base generation
        # For optimization, we assume base generation is done, and we just re-execute with different corruption.
        # However, to be safe, we check existence.
        
        workflows_to_process = get_workflows_to_process(args.count, args.resume)
        
        # Batch processing loop
        batch_size = args.batch_size
        for i in range(0, len(workflows_to_process), batch_size):
            batch = workflows_to_process[i : i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: IDs {batch[0]}-{batch[-1]}")
            
            for wf_id in batch:
                # Update checkpoint before processing
                save_checkpoint({
                    'checkpoint': {
                        'last_workflow_id': wf_id,
                        'status': 'processing',
                        'current_rate': rate
                    }
                })
                
                process_single_workflow(
                    wf_id, 
                    args.seed, 
                    rate, 
                    streaming=args.streaming
                )
                
                # Update checkpoint after success
                save_checkpoint({
                    'checkpoint': {
                        'last_workflow_id': wf_id,
                        'status': 'completed',
                        'current_rate': rate
                    }
                })

        # Aggregate results for this rate
        aggregate_metrics(rate, archs)

    # Run final statistical tests
    run_statistical_tests()

def aggregate_metrics(rate: float, archs: List[str]):
    """Aggregates metrics from individual workflow results into a single file."""
    results_dir = os.path.join(PROCESSED_DATA_DIR, 'results')
    all_metrics = []
    
    # Stream through files to avoid loading all into memory at once
    for f in os.listdir(results_dir):
        if f.endswith('_metrics.json'):
            with open(os.path.join(results_dir, f), 'r') as file:
                data = json.load(file)
                data['corruption_rate'] = rate
                all_metrics.append(data)
    
    # Write aggregated file
    agg_path = os.path.join(PROCESSED_DATA_DIR, 'results', f'aggregated_metrics_rate_{rate}.json')
    with open(agg_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"Aggregated metrics for rate {rate} written to {agg_path}")

def run_pipeline(args):
    """Orchestrates the full pipeline or specific phases."""
    ensure_directories()
    
    # Phase: Generate
    if args.phase == 'generate' or args.phase is None:
        logger.info("Starting Generation Phase...")
        # T012/T013 logic: Generate batch
        generate_ground_truth_batch(args.count, args.seed)
        verify_ground_truth_hashes()
        save_checkpoint({'checkpoint': {'last_workflow_id': args.count, 'status': 'generation_complete'}})

    # Phase: Simulate (Execution + Corruption)
    if args.phase == 'simulate' or args.phase is None:
        logger.info("Starting Simulation Phase...")
        # T023/T026 logic
        injector = CorruptionInjector(corruption_rate=args.corruption_rate)
        # Note: In a real sweep, we iterate rates. Here we do single pass if not sweep.
        if args.sweep:
            run_sweep(args)
        else:
            # Single rate execution
            workflows = get_workflows_to_process(args.count, args.resume)
            for wf_id in workflows:
                process_single_workflow(wf_id, args.seed, args.corruption_rate, args.streaming)
                save_checkpoint({'checkpoint': {'last_workflow_id': wf_id, 'status': 'simulating'}})

    # Phase: Reconstruct
    if args.phase == 'reconstruct' or args.phase is None:
        logger.info("Starting Reconstruction Phase...")
        # T030/T031 logic
        # Assuming simulation is done, we reconstruct all
        # Stream through corruption map
        corruption_map = load_corruption_map()
        engine = ReconstructionEngine()
        
        for wf_id, logs in corruption_map.items():
            # Reconstruct for each architecture
            for arch in ['event_log', 'session_first']:
                engine.reconstruct(wf_id, arch, logs)
            
            # Calculate metrics
            MetricsCalculator.calculate_workflow_metrics(wf_id, logs, os.path.join(RAW_DATA_DIR, 'workflows', f'{wf_id}_ground_truth.json'))

    # Phase: Analyze
    if args.phase == 'analyze' or args.phase is None:
        logger.info("Starting Analysis Phase...")
        run_statistical_tests()
        
        # Final checksumming
        update_artifact_hashes()

def main():
    args = parse_args()
    run_pipeline(args)

if __name__ == '__main__':
    main()
