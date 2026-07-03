---
action_items:
- id: 08b90c655aa3
  severity: writing
  text: 'Acronyms: ''MCC'' (Matthews Correlation Coefficient), ''SSM'' (State Space
    Model), ''BPE'' (Byte-Pair Encoding), ''k-mer'', ''MoE'' (Mixture of Experts),
    ''T-enc''/''T-dec'' (Transformer-encoder/decoder), ''SN'' (Single-Nucleotide),
    ''T2T'' (Telomere-to-Telomere), ''eQTL'', ''Hi-C'', ''lncRNA'', ''TF'' (Transcription
    Factor), ''NT'' (Nucleotide Transformer), ''GUE'' (Genome Understanding Evaluation),
    ''GB'' (Genomic Benchmarks), ''PGB'' (Plant Genomics Benchmark), ''iPro'', ''iDNA'',
    ''iDHS'', ''4mC'', ''5mC'', ''6mA'', ''ReLU'', ''CNN'' (Convo'
- id: 76372f2755fd
  severity: writing
  text: 'Domain Concepts: ''Pareto frontier'', ''Spearman correlation'', ''macro-MCC''
    vs. ''micro-MCC'', ''logistic regression'', ''few-shot'' (1-shot, 10-shot), ''prokaryotic'',
    ''eukaryotic'', ''viral'', ''phage'', ''coding'', ''non-coding'', ''chromatin'',
    ''enhancer'', ''promoter'', ''splice sites'', ''histone modifications'', ''DNA
    methylation'', ''species classification'', ''regulatory'', ''TF binding'', ''lncRNA'',
    ''mouse enhancers'', ''virus/phage'', ''coding/non-coding'', ''chromatin accessibility''.
    While some are standard in genomics, their s'
- id: 7f5eab9dc3cd
  severity: writing
  text: 'Model Names: ''Mamba-SSM'', ''HyenaDNA'', ''GenomeOcean'', ''Evo'', ''DNABERT'',
    ''GENA-LM'', ''GROVER'', ''Nucleotide Transformer'', ''JanusDNA'', ''Gene42'',
    ''LucaOne'', ''OmniNA'', ''Enformer'', ''DNALongBench'', ''SPACE'', ''BioToken'',
    ''BioFM'', ''DeepGene'', ''Genomics-FM'', ''PlantCaduceus'', ''AgroNT'', ''MutBERT'',
    ''Evo2'', ''ChatNT'', ''NucleotideGPT'', ''EpiGePT'', ''ENBED'', ''HAD'', ''C.La.P.'',
    ''HybriDNA'', ''MxDNA'', ''VQDNA'', ''BMFM-DNA''. While these are proper nouns,
    the underlying architecture or data type (e.g., ''Mamba-SSM'' implying a'
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:10:42.181253Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript is dense with domain-specific terminology and acronyms that are not consistently defined upon first use, creating a barrier for non-specialist readers or those from adjacent fields (e.g., general ML or biology). While the paper aims to be a comprehensive benchmark, the reliance on unexplained jargon undermines its accessibility.

Specific instances requiring attention include:
1.  **Acronyms:** 'MCC' (Matthews Correlation Coefficient), 'SSM' (State Space Model), 'BPE' (Byte-Pair Encoding), 'k-mer', 'MoE' (Mixture of Experts), 'T-enc'/'T-dec' (Transformer-encoder/decoder), 'SN' (Single-Nucleotide), 'T2T' (Telomere-to-Telomere), 'eQTL', 'Hi-C', 'lncRNA', 'TF' (Transcription Factor), 'NT' (Nucleotide Transformer), 'GUE' (Genome Understanding Evaluation), 'GB' (Genomic Benchmarks), 'PGB' (Plant Genomics Benchmark), 'iPro', 'iDNA', 'iDHS', '4mC', '5mC', '6mA', 'ReLU', 'CNN' (Convolutional Neural Network), 'Hyena', 'StripedHyena', 'Graph-Transformer', 'BioToken'. Many of these appear in tables and figure captions without prior definition in the main text.
2.  **Domain Concepts:** 'Pareto frontier', 'Spearman correlation', 'macro-MCC' vs. 'micro-MCC', 'logistic regression', 'few-shot' (1-shot, 10-shot), 'prokaryotic', 'eukaryotic', 'viral', 'phage', 'coding', 'non-coding', 'chromatin', 'enhancer', 'promoter', 'splice sites', 'histone modifications', 'DNA methylation', 'species classification', 'regulatory', 'TF binding', 'lncRNA', 'mouse enhancers', 'virus/phage', 'coding/non-coding', 'chromatin accessibility'. While some are standard in genomics, their specific usage in the context of these benchmarks (e.g., 'mouse enhancers' as a specific task category) should be clarified.
3.  **Model Names:** 'Mamba-SSM', 'HyenaDNA', 'GenomeOcean', 'Evo', 'DNABERT', 'GENA-LM', 'GROVER', 'Nucleotide Transformer', 'JanusDNA', 'Gene42', 'LucaOne', 'OmniNA', 'Enformer', 'DNALongBench', 'SPACE', 'BioToken', 'BioFM', 'DeepGene', 'Genomics-FM', 'PlantCaduceus', 'AgroNT', 'MutBERT', 'Evo2', 'ChatNT', 'NucleotideGPT', 'EpiGePT', 'ENBED', 'HAD', 'C.La.P.', 'HybriDNA', 'MxDNA', 'VQDNA', 'BMFM-DNA'. While these are proper nouns, the underlying architecture or data type (e.g., 'Mamba-SSM' implying a State Space Model) should be briefly explained when first introduced.

The paper frequently uses abbreviations for task categories (e.g., 'Histone Modifications', 'Promoters', 'Enhancers', 'DNA Methylation', 'Splice Sites', 'lncRNA', 'Mouse Enhancers', 'TF Binding', 'Species Classification', 'Regulatory', 'Virus/Phage', 'Coding/Non-coding', 'Chromatin Accessibility') without ensuring the reader understands the specific biological or computational meaning in the context of the benchmark. For instance, 'lncRNA' is used extensively but not defined as 'long non-coding RNA' until perhaps much later or not at all in a clear, accessible way. Similarly, 'TF binding' is used without explicitly stating 'Transcription Factor binding' in all instances.

The use of '1-shot', '10-shot', and 'full-shot' is common in ML but should be explicitly defined as evaluation regimes with 1, 10, and all available labeled examples, respectively, for readers less familiar with few-shot learning terminology.

The term 'Pareto frontier' is used to describe the trade-off between model size and performance. While a standard concept in optimization, a brief explanation (e.g., 'the set of models that are not outperformed by any other model in both size and performance') would make the figure and its interpretation more accessible to a broader audience.

The distinction between 'macro-MCC' and 'micro-MCC' is crucial for understanding the benchmark's aggregation strategy but is not clearly explained in plain language. A simple definition (e.g., 'macro-MCC averages performance across categories, while micro-MCC averages across all individual tasks') would be beneficial.

The paper also uses specific dataset names (e.g., 'GUE', 'GB', 'NT', 'PGB', 'iPro', 'iDNA', 'iDHS') as prefixes for tasks without always providing a clear, accessible definition of what these datasets represent or why they are grouped under these names.

In summary, the manuscript would significantly benefit from a more consistent and explicit definition of jargon, acronyms, and domain-specific concepts upon their first appearance. This would align with the paper's goal of providing a standardized and accessible benchmark for the broader community.
