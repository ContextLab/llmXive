import argparse
import logging
import sys
import time
from pathlib import Path

# Adjust path to ensure imports work when run as module
# The project structure expects 'code' to be the root for imports
# If running via `python -m src.cli.main`, 'code' must be in sys.path
# We assume the runner sets `PYTHONPATH=code` or installs the package.
# For robustness, we add 'code' to path if not present.
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.services.ingest import fetch_and_build_subgraph, save_graph_to_parquet
from src.services.embeddings import main as embeddings_main
from src.services.analysis import run_full_analysis, save_analysis_report
from scripts.generate_analysis_report import main as report_main
from scripts.save_final_dataset import main as save_final_dataset_main
from scripts.save_graph_pipeline import main as save_graph_pipeline_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def step_ingest(args):
    """Execute the ingestion pipeline: fetch data, sample, build graph, save."""
    logger.info(f"Starting ingestion step with sample size: {args.sample_size}")
    try:
        # Fetch and build subgraph
        G = fetch_and_build_subgraph(target_size=args.sample_size, seed_node_id=args.seed_node_id)
        
        # Save graph to parquet (Task T016)
        output_path = save_graph_to_parquet(G, args.output_path)
        logger.info(f"Graph saved to {output_path}")
        
        # Run validation and save graph pipeline logic (Task T012b, T053)
        # This ensures the graph is validated and state is updated
        if args.run_validation:
            save_graph_pipeline_main()
            
        logger.info("Ingestion step completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion step failed: {e}", exc_info=True)
        sys.exit(1)

def step_embeddings(args):
    """Execute the embeddings pipeline: generate embeddings, cluster, compute novelty."""
    logger.info("Starting embeddings step.")
    try:
        # Run the main embeddings pipeline which handles filtering, embedding, clustering, novelty
        embeddings_main(batch_size=args.batch_size)
        logger.info("Embeddings step completed successfully.")
    except Exception as e:
        logger.error(f"Embeddings step failed: {e}", exc_info=True)
        sys.exit(1)

def step_analysis(args):
    """Execute the analysis pipeline: correlation, regression, correction, report."""
    logger.info("Starting analysis step.")
    try:
        # Run full statistical analysis
        metrics = run_full_analysis()
        
        # Save statistical metrics
        save_analysis_report(metrics)
        
        # Generate final report (Task T029)
        report_main()
        
        # Save final dataset (Task T024)
        save_final_dataset_main()
        
        logger.info("Analysis step completed successfully.")
    except Exception as e:
        logger.error(f"Analysis step failed: {e}", exc_info=True)
        sys.exit(1)

def step_report(args):
    """Execute the report generation step."""
    logger.info("Starting report step.")
    try:
        report_main()
        logger.info("Report step completed successfully.")
    except Exception as e:
        logger.error(f"Report step failed: {e}", exc_info=True)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="llmXive Automated Science Pipeline CLI")
    subparsers = parser.add_subparsers(dest='step', help='Pipeline steps')

    # Ingest Step
    ingest_parser = subparsers.add_parser('ingest', help='Run data ingestion pipeline')
    ingest_parser.add_argument('--sample-size', type=int, default=1000, help='Target subgraph size')
    ingest_parser.add_argument('--seed-node-id', type=str, default=None, help='Seed node ID for sampling')
    ingest_parser.add_argument('--output-path', type=str, default='data/processed/subgraph_with_clusters.parquet', help='Output path for graph')
    ingest_parser.add_argument('--run-validation', action='store_true', help='Run validation after ingestion')
    ingest_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    # Embeddings Step
    embeddings_parser = subparsers.add_parser('embeddings', help='Run embeddings and novelty pipeline')
    embeddings_parser.add_argument('--batch-size', type=int, default=64, help='Batch size for embeddings')
    embeddings_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    # Analysis Step
    analysis_parser = subparsers.add_parser('analysis', help='Run statistical analysis pipeline')
    analysis_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    # Report Step
    report_parser = subparsers.add_parser('report', help='Generate final analysis report')
    report_parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.step == 'ingest':
        step_ingest(args)
    elif args.step == 'embeddings':
        step_embeddings(args)
    elif args.step == 'analysis':
        step_analysis(args)
    elif args.step == 'report':
        step_report(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
