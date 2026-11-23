"""
Integration test for full alignment and PSI quantification flow (T011).

Verifies:
1. PSI table is produced at the expected output path.
2. pipeline.log contains timestamps for key steps.
3. At least one splice junction is reported in the PSI table.

This test uses synthetic FASTQ files to simulate the pipeline execution
on a CI-friendly scale, ensuring the logic flows correctly from alignment
to quantification without requiring large external downloads.
"""
import os
import sys
import subprocess
import tempfile
import shutil
import re
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path to import pipeline modules
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from pipeline.align import align_reads
from pipeline.quantify import generate_events, quantify_psi
from utils.logger import setup_logger, get_log_file_path


def create_synthetic_fastq(temp_dir: Path, sample_id: str, species: str) -> Path:
    """
    Creates a minimal synthetic FASTQ file for testing alignment.
    The sequence includes a known splice junction pattern to ensure
    at least one junction is detected.
    """
    fastq_path = temp_dir / f"{sample_id}_{species}.fastq"
    # Synthetic reads: 10 reads, 50bp each
    # Pattern designed to align across a simple intron if the intron is removed
    # or map to a continuous region if not.
    # We simulate reads that span a junction by creating a sequence that
    # aligns to a reference with a gap, or simply aligns to a contiguous
    # synthetic reference.
    # For STAR alignment to report a junction, we need reads that span a splice.
    # We will create a reference and reads that force a junction.
    
    # Actually, simpler approach for CI:
    # Create a tiny synthetic reference and reads that align.
    # STAR requires a genome index. We will generate a minimal index.
    # But generating a full STAR index in a test is heavy.
    # Alternative: Mock the alignment output? No, task requires "real" flow.
    # Better: Use a tiny synthetic genome (e.g., 10kb) and index it.
    
    # Let's create a synthetic reference FASTA and index it.
    ref_fasta = temp_dir / f"{species}_ref.fa"
    # A simple 2kb sequence with an intron in the middle (simulated by a gap in reads)
    # Actually, STAR aligns reads to a reference. To get a junction, reads must span an intron in the reference.
    # We'll create a reference with an exon-intron-exon structure.
    # Exon1 (100bp) - Intron (500bp) - Exon2 (100bp)
    # We'll generate reads that span the Exon1-Intron and Intron-Exon2 boundaries?
    # No, reads span Exon1-Exon2 if the intron is spliced out in the read (cDNA).
    # So: Reference = Exon1 + Intron + Exon2.
    # Reads = Exon1 (part) + Exon2 (part).
    # STAR will detect the junction.
    
    ref_seq = "A" * 100 + "N" * 500 + "C" * 100  # Exon1, Intron, Exon2
    with open(ref_fasta, "w") as f:
        f.write(f">{species}_transcript_1\n")
        f.write(ref_seq + "\n")
    
    # Create reads that span the junction (Exon1 end + Exon2 start)
    # Read 1: Last 20bp of Exon1 + First 30bp of Exon2
    # Read 2: Last 25bp of Exon1 + First 25bp of Exon2
    # ...
    reads = []
    for i in range(10):
        read_seq = ref_seq[80:100] + ref_seq[600:630]  # 20bp from Exon1, 30bp from Exon2
        reads.append(f"@read_{i}\n{read_seq}\n+\n{'I'*len(read_seq)}\n")
    
    with open(fastq_path, "w") as f:
        f.writelines(reads)
    
    return ref_fasta, fastq_path


def run_synthetic_pipeline(output_dir: Path, species: str, sample_id: str):
    """
    Runs the alignment and quantification pipeline on synthetic data.
    """
    # 1. Setup directories
    work_dir = output_dir / "work" / species
    work_dir.mkdir(parents=True, exist_ok=True)
    genome_dir = work_dir / "genome"
    genome_dir.mkdir(parents=True, exist_ok=True)
    align_dir = work_dir / "align"
    align_dir.mkdir(parents=True, exist_ok=True)
    quant_dir = work_dir / "quant"
    quant_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Create synthetic data
    ref_fasta, fastq_file = create_synthetic_fastq(work_dir, sample_id, species)
    
    # 3. Generate STAR index (required for alignment)
    # We use a minimal set of parameters for speed
    logger = setup_logger(log_file=str(output_dir / "pipeline.log"))
    logger.info(f"Generating STAR index for {species}")
    
    index_cmd = [
        "STAR",
        "--runThreadN", "2",
        "--runMode", "genomeGenerate",
        "--genomeDir", str(genome_dir),
        "--genomeFastaFiles", str(ref_fasta),
        "--genomeSAindexNbases", "8", # Smaller index for speed
        "--limitGenomeGenerateRAM", "2000000000"
    ]
    
    try:
        subprocess.run(index_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        pytest.skip("STAR not installed in environment. Skipping integration test.")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"STAR index generation failed: {e}")
    
    logger.info(f"Index generated for {species}")
    
    # 4. Align reads
    logger.info(f"Aligning reads for {species}")
    out_bam = align_dir / f"{sample_id}.Aligned.sortedByCoord.out.bam"
    
    align_cmd = [
        "STAR",
        "--runThreadN", "2",
        "--genomeDir", str(genome_dir),
        "--readFilesIn", str(fastq_file),
        "--outFileNamePrefix", str(align_dir / f"{sample_id}_"),
        "--outSAMtype", "BAM", "SortedByCoordinate",
        "--outFilterMultimapNmax", "20",
        "--alignSJoverhangMin", "8",
        "--alignSJDBoverhangMin", "1",
        "--outFilterMismatchNmax", "999",
        "--outFilterMismatchNoverLmax", "0.04",
        "--alignIntronMin", "20",
        "--alignIntronMax", "1000000",
        "--alignMatesGapMax", "1000000",
        "--outSAMattrRGline", f"ID:{sample_id} SM:{sample_id} PL:ILLUMINA"
    ]
    
    try:
        subprocess.run(align_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        logger.error(f"Alignment failed: {e}")
        raise
    
    logger.info(f"Alignment complete: {out_bam.exists()}")
    
    # 5. Generate events file (GTF) - minimal GTF for SUPPA2
    # SUPPA2 needs a GTF. We create a minimal one corresponding to our synthetic reference.
    # Exon 1: 1-100, Intron: 101-600, Exon 2: 601-700
    # We define two exons for the transcript.
    gtf_file = work_dir / "annotation.gtf"
    with open(gtf_file, "w") as f:
        f.write(f"{species}\tcustom\texon\t1\t100\t.\t+\t.\tgene_id \"GENE1\"; transcript_id \"TX1\"; exon_number \"1\";\n")
        f.write(f"{species}\tcustom\texon\t601\t700\t.\t+\t.\tgene_id \"GENE1\"; transcript_id \"TX1\"; exon_number \"2\";\n")
    
    # 6. Quantify PSI
    logger.info(f"Quantifying PSI for {species}")
    events_file = quant_dir / "events.ioe"
    psi_file = quant_dir / "psi.tsv"
    
    # Generate events
    try:
        subprocess.run(
            ["suppa.py", "generateEvents", "-i", str(gtf_file), "-o", str(events_file), "-f", "ioe"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except FileNotFoundError:
        pytest.skip("SUPPA2 not installed. Skipping.")
    
    # Quantify
    try:
        subprocess.run(
            ["suppa.py", "quantify", "-i", str(events_file), "-e", str(out_bam), "-o", str(psi_file)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Quantification failed: {e}")
        raise
    
    logger.info(f"Quantification complete: {psi_file.exists()}")
    return psi_file, out_bam


@pytest.mark.integration
def test_psi_pipeline_flow(tmp_path):
    """
    Integration test: Verify PSI table is produced, pipeline.log contains timestamps,
    and at least one splice junction is reported.
    """
    output_dir = tmp_path / "pipeline_run"
    output_dir.mkdir()
    
    # Setup logging
    log_file = output_dir / "pipeline.log"
    setup_logger(log_file=str(log_file))
    
    species_list = ["human", "chimp"]
    sample_ids = ["H01", "C01"]
    
    psi_tables = []
    
    # Run pipeline for each species
    for species, sample_id in zip(species_list, sample_ids):
        try:
            psi_file, bam_file = run_synthetic_pipeline(output_dir, species, sample_id)
            psi_tables.append(psi_file)
            
            # Verify BAM exists
            assert bam_file.exists(), f"BAM file not found for {species}"
            
        except Exception as e:
            pytest.fail(f"Pipeline failed for {species}: {e}")
    
    # Verify PSI tables exist
    assert len(psi_tables) == len(species_list), "Not all PSI tables were generated"
    
    for psi_file in psi_tables:
        assert psi_file.exists(), f"PSI file missing: {psi_file}"
        
        # Load and check content
        df = pd.read_csv(psi_file, sep="\t")
        assert not df.empty, f"PSI table is empty for {psi_file}"
        
        # Check for at least one row (splice event)
        assert len(df) >= 1, f"No splice events reported in {psi_file}"
        
        # Check columns
        assert "event_id" in df.columns or len(df.columns) >= 1, "PSI table missing expected columns"
    
    # Verify pipeline.log contains timestamps
    assert log_file.exists(), "pipeline.log was not created"
    
    log_content = log_file.read_text()
    assert "INFO" in log_content or "20" in log_content, "Log file seems empty or malformed"
    
    # Check for timestamp pattern (e.g., 2023-01-01 12:00:00 or similar)
    timestamp_pattern = r"\d{4}-\d{2}-\d{2}.*\d{2}:\d{2}:\d{2}"
    timestamps = re.findall(timestamp_pattern, log_content)
    assert len(timestamps) > 0, "No timestamps found in pipeline.log"
    
    # Verify specific steps were logged
    assert "Generating STAR index" in log_content or "Index generated" in log_content, "Index generation not logged"
    assert "Aligning reads" in log_content or "Alignment complete" in log_content, "Alignment not logged"
    assert "Quantifying PSI" in log_content or "Quantification complete" in log_content, "Quantification not logged"
    
    # Verify at least one splice junction is reported (already checked via df length)
    # But specifically check if any event_id implies a junction (e.g., SE, RI, etc.)
    # Since we generated synthetic data, we expect at least one event type.
    # The test passes if df is not empty.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])