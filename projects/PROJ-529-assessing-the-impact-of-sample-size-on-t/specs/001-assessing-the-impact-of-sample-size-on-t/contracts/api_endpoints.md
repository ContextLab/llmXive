# API Contracts: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Endpoints

### Data Acquisition
- `GET /api/v1/meta-analyses` - List all meta-analyses
- `GET /api/v1/meta-analyses/{meta_id}` - Get specific meta-analysis
- `POST /api/v1/download` - Trigger data download from Cochrane/Campbell

### Subsampling
- `POST /api/v1/subsample` - Generate bootstrap subsamples for given k values
- `GET /api/v1/subsamples/{meta_id}` - List all subsamples for a meta-analysis

### Metrics
- `GET /api/v1/metrics/{meta_id}` - Get stability metrics for a meta-analysis
- `POST /api/v1/metrics/calculate` - Calculate metrics for all meta-analyses

### Analysis
- `POST /api/v1/analysis/threshold` - Detect threshold for stability
- `GET /api/v1/analysis/plots` - Retrieve diagnostic plots