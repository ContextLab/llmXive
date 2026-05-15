---
direction: Serving
title: Orca: A Distributed Serving System for Transformer-Based Generative Models
arxiv_id: none
source_url: https://www.usenix.org/conference/osdi22/presentation/yu
markdown_new_url: http://markdown.new/https://www.usenix.org/conference/osdi22/presentation/yu
core_reference: no
fetch_status: ok
---


Title: Orca: A Distributed Serving System for Transformer-Based Generative Models

URL Source: https://www.usenix.org/conference/osdi22/presentation/yu

Markdown Content:
# Orca: A Distributed Serving System for Transformer-Based Generative Models

Gyeong-In Yu and Joo Seong Jeong, _Seoul National University;_ Geon-Woo Kim, _FriendliAI and Seoul National University;_ Soojeong Kim, _FriendliAI;_ Byung-Gon Chun, _FriendliAI and Seoul National University_

Large-scale Transformer-based models trained for generation tasks (e.g., GPT-3) have recently attracted huge interest, emphasizing the need for system support for serving models in this family. Since these models generate a next token in an autoregressive manner, one has to run the model multiple times to process an inference request where each iteration of the model generates a single output token for the request. However, existing systems for inference serving do not perform well on this type of workload that has a multi-iteration characteristic, due to their inflexible scheduling mechanism that cannot change the current batch of requests being processed; requests that have finished earlier than other requests in a batch cannot return to the client, while newly arrived requests have to wait until the current batch completely finishes.

In this paper, we propose iteration-level scheduling, a new scheduling mechanism that schedules execution at the granularity of iteration (instead of request) where the scheduler invokes the execution engine to run only a single iteration of the model on the batch. In addition, to apply batching and iteration-level scheduling to a Transformer model at the same time, we suggest selective batching, which applies batching only to a selected set of operations. Based on these two techniques, we have implemented a distributed serving system called ORCA, with additional designs for scalability to models with hundreds of billions of parameters. Our evaluation on a GPT-3 175B model shows that ORCA can significantly outperform NVIDIA FasterTransformer in terms of both latency and throughput: 36:9× throughput improvement at the same level of latency.

OSDI '22 Open Access Sponsored by NetApp

## Open Access Media

USENIX is committed to Open Access to the research presented at our events. Papers and proceedings are freely available to everyone once the event begins. Any video, audio, and/or slides that are posted after the event are also free and open to everyone. [Support USENIX](/annual-fund) and our commitment to Open Access.



BibTeX

@inproceedings {280922,  
 author = {Gyeong-In Yu and Joo Seong Jeong and Geon-Woo Kim and Soojeong Kim and Byung-Gon Chun},  
 title = {Orca: A Distributed Serving System for {Transformer-Based} Generative Models},  
 booktitle = {16th USENIX Symposium on Operating Systems Design and Implementation (OSDI 22)},  
 year = {2022},  
 isbn = {978-1-939133-28-1},  
 address = {Carlsbad, CA},  
 pages = {521--538},  
 url = {https://www.usenix.org/conference/osdi22/presentation/yu},  
 publisher = {USENIX Association},  
 month = jul  
}  

[Download](/biblio/export/bibtex/280922)

 [osdi22-yu.pdf](https://www.usenix.org/system/files/osdi22-yu.pdf)

## Presentation Video 