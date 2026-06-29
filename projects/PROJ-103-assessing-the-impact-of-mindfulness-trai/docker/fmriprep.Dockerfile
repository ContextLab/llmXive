# fMRIPrep Docker Configuration for Mindfulness-DMN Study
# PROJ-103: Assessing the Impact of Mindfulness Training on Default Mode Network Activity
#
# This Dockerfile extends the official fMRIPrep image with project-specific
# configurations for CPU-limited execution suitable for GitHub Actions free tier.
#
# Resource constraints are applied at runtime via docker-compose.yml or run script.
# See: https://fmriprep.org/en/stable/installation.html#docker
#
# Constitution Principle VI: AAL atlas will be used (Yeo atlas flagged for kickback)
#
# Build command:
#   docker build -f docker/fmriprep.Dockerfile -t fmriprep-mindfulness:latest .
#
# Run with resource constraints (example for 2 cores, 4GB RAM):
#   docker run --rm -it \
#     --cpus=2.0 \
#     --memory=4g \
#     --shm-size=2g \
#     -v /path/to/data:/data:ro \
#     -v /path/to/output:/output \
#     fmriprep-mindfulness:latest /data /output participant --participant-label sub-01

FROM nipreps/fmriprep:23.1.3

LABEL maintainer="llmXive Research Team <research@llmxive.org>"
LABEL version="1.0.0"
LABEL description="fMRIPrep container for mindfulness-DMN connectivity study with CPU-limited settings"
LABEL project="PROJ-103-assessing-the-impact-of-mindfulness-trai"

# =============================================================================
# ENVIRONMENT CONFIGURATION
# =============================================================================

# Disable parallel processing by default (override at runtime for constrained CPU)
ENV OMP_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1
ENV VECLIB_MAXIMUM_THREADS=1
ENV NUMBA_NUM_THREADS=1

# Memory limits for internal processes
ENV FMRIPREP_MEMORY_LIMIT=4096
ENV FMRIPREP_THREAD_COUNT=2

# fMRIPrep specific environment variables
ENV FMRIPREP_LOG_LEVEL=INFO
ENV FMRIPREP_SKIP_BIDS_VALIDATION=false
ENV FMRIPREP_WORK_DIR=/work

# Atlas configuration per Constitution Principle VI (AAL over Yeo)
ENV FMRIPREP_DEFAULT_ATLAS=AAL

# Create necessary directories
RUN mkdir -p /work /scratch /opt/conda/envs/fmriprep

# Install additional Python packages for project-specific utilities
RUN pip install --no-cache-dir \
    nilearn>=0.10.0 \
    nibabel>=5.0.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0 \
    scipy>=1.10.0 \
    statsmodels>=0.14.0 \
    matplotlib>=3.7.0

# =============================================================================
# HEALTH CHECK
# =============================================================================

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import nilearn; import nibabel; print('fMRIPrep dependencies OK')"

# =============================================================================
# WORKSPACE SETUP
# =============================================================================

WORKDIR /work

# =============================================================================
# ENTRYPOINT
# =============================================================================

# fMRIPrep entrypoint handles BIDS dataset processing
# Usage: fmriprep <bids-dir> <output-dir> <level> [options]
ENTRYPOINT ["/opt/conda/bin/fmriprep"]

# =============================================================================
# DOCUMENTATION
# =============================================================================
#
# RESOURCE CONSTRAINTS (Applied at runtime, not in Dockerfile):
#
# CPU Limits:
#   --cpus=2.0           Limit to 2 CPU cores (GitHub Actions free tier compatible)
#   --cpuset-cpus=0,1    Pin to specific cores if needed
#   OMP_NUM_THREADS=1    Disable OpenMP parallelization per thread
#
# Memory Limits:
#   --memory=4g          Limit container to 4GB RAM
#   --memory-swap=4g     Prevent swap usage
#   --shm-size=2g        Shared memory for multiprocessing
#
# fMRIPrep Specific:
#   --nprocs=2           Number of parallel processes (matches CPU limit)
#   --omp-nthreads=1     OpenMP threads per process
#   --mem-mb=4000        Memory in MB
#   --low-mem            Enable low-memory mode
#   --notrack            Disable resource tracking
#
# Example docker-compose.yml constraints:
#   services:
#     fmriprep:
#       deploy:
#         resources:
#           limits:
#             cpus: '2.0'
#             memory: 4G
#
# Example run command for GitHub Actions:
#   docker run --rm \
#     --cpus=2.0 \
#     --memory=4g \
#     --shm-size=2g \
#     --nprocs=2 \
#     --omp-nthreads=1 \
#     --mem-mb=4000 \
#     --low-mem \
#     -v data/raw:/data:ro \
#     -v data/processed:/output \
#     fmriprep-mindfulness:latest \
#     /data /output participant --participant-label $SUBJECT_ID
#