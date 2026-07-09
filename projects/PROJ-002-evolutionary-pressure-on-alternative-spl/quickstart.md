# Quick Start Guide for PROJ-002

## Initial Setup
1. Clone the repository.
2. Set up Python environment:
 ```bash
 python3.11 -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```
3. Set up R environment:
 ```bash
 chmod +x install_r_dependencies.sh
./install_r_dependencies.sh
 ```

## Verification
Verify that all dependencies are correctly installed:
```bash
python -c "import pandas, numpy, yaml, Bio, requests, tqdm, pybedtools, pyBigWig, sklearn, loguru; print('Python OK')"
Rscript -e "library(phylolm); library(ape); library(data.table); library(ggplot2); cat('R OK\n')"
```

## Next Steps
- Configure genome assemblies in `config/genomes.yaml` (Task T004)
- Implement logging infrastructure (Task T005)
- Begin User Story 1 implementation (Phase 3)

## Troubleshooting
- If R packages fail to install, ensure you have a C compiler and development headers installed.
- For Python dependency issues, try upgrading pip: `pip install --upgrade pip`