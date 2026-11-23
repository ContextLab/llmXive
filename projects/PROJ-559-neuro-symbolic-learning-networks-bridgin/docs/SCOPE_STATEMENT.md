# Project Scope Statement: Neuro-Symbolic Learning Networks

## 1. Project Overview
This project, **Neuro-Symbolic Learning Networks: Bridging Neural and Symbolic Reasoning in Education**, aims to investigate the pedagogical impact of combining neural and symbolic reasoning systems in generating educational explanations.

## 2. Dataset Scope
The project is strictly limited to the use of the **ASSISTments 2009-2010** dataset.

### 2.1 Included Data
- **Source**: Hugging Face Datasets (`assistments/2009-2010`)
- **Format**: Raw CSV (`data/raw/assistments.csv`)
- **Content**: Student interaction logs including problem IDs, correctness, response times, and skill tags.

### 2.2 Excluded Data
- **Khan Academy Dataset**: As decided in the implementation planning phase (Plan.md summary), the Khan Academy dataset has been **excluded** from the project scope.
- **Reasoning**: The exclusion was made to reduce initial scope complexity, focus validation efforts on a single, well-documented educational dataset, and ensure the pipeline can be successfully executed within the allocated computational and time constraints.

## 3. Implementation Boundaries
- **Phase 1 (Setup)**: Project structure and tooling.
- **Phase 2 (Foundational)**: Core infrastructure, schema definitions, and mandatory calibration logic (T031-T033).
- **Phase 3 (User Story 1)**: Generation of three distinct explanation artifacts (neural, symbolic, neuro-symbolic).
- **Phase 4 (User Story 2)**: Simulation of student interactions using a BKT model.
- **Phase 5 (User Story 3)**: Comparative analysis (mixed-effects regression, effect sizes).

## 4. Constraints
- **Computational**: All model inference must run on CPU (or a single free-tier GPU if explicitly offloaded) with a maximum RAM usage of 7GB.
- **Data Integrity**: No synthetic or placeholder data will be used to replace missing real-world datasets. The pipeline must fail loudly if required real data is not available.
- **Timeouts**: All external data fetch operations must adhere to a 300-second timeout limit.

## 5. Approval
This scope statement supersedes any previous mentions of the Khan Academy dataset in early drafts. All future development and testing must align with the ASSISTments-only scope.
