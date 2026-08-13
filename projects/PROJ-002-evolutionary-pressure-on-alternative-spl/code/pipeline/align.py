"""
STAR Alignment wrapper for PROJ-002.
Executes STAR alignment with default parameters and logs duration.
"""
import subprocess
import time
import os
from pathlib import Path
from loguru import logger

from code.utils.logger import setup_logger
setup_logger("pipeline.log", level="INFO")

def align_reads(fastq_path: str, genome_dir: str, output_dir: str) -> str:
    """
    Align reads using STAR.

    Args:
        fastq_path: Path to input FASTQ file.
        genome_dir: Path to STAR genome index directory.
        output_dir: Directory for output BAM files.

    Returns:
        Path to the generated BAM file.
    """
    os.makedirs(output_dir, exist_ok=True)
    sample_name = Path(fastq_path).stem
    output_bam = os.path.join(output_dir, f"{sample_name}.Aligned.out.bam")

    logger.info(f"Starting STAR alignment for {sample_name}")
    start_time = time.time()

    # STAR command (parameters may be adjusted based on spec)
    cmd = [
        "STAR",
        "--genomeDir", genome_dir,
        "--readFilesIn", fastq_path,
        "--outFileNamePrefix", os.path.join(output_dir, sample_name + "."),
        "--outSAMtype", "BAM", "SortedByCoordinate",
        "--runThreadN", "4", # Default to 4 threads
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        duration = time.time() - start_time
        logger.info(f"Alignment complete for {sample_name}. Duration: {duration:.2f}s")

        # Validate output exists
        if not os.path.exists(output_bam):
            raise FileNotFoundError(f"BAM file not generated: {output_bam}")

        return output_bam

    except subprocess.CalledProcessError as e:
        logger.error(f"STAR alignment failed for {sample_name}: {e.stderr.decode()}")
        raise

def main():
    """
    Main entry point for alignment pipeline.
    """
    logger.info("Starting alignment pipeline.")
    # Placeholder for actual invocation logic
    logger.info("Alignment pipeline stub ready.")

if __name__ == "__main__":
    main()
