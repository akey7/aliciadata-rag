# Evaluation Plan

## Overview

### Current Limitations

Given 3000-character chunks, 300-character overlap, top-15 contexts, my risks are:
- Too much irrelevant context in the top 15 chunks
- Appearance that “answer looks plausible” but is weakly supported

### RAGAS

**Why:** Purpose-built for RAG, LangChain-native, generates synthetic test sets
**Key Metrics:**
- **Faithfulness:** Does the answer stay true to retrieved context? (hallucination detection)
- **Answer Relevancy:** Does the answer address the question?
- **Context Relevancy:** Are retrieved chunks actually relevant to the question?
- **Context Recall:** Did retrieval find all necessary information?

### Evaluation Considerations

**Problems:** This is a side project and I have limited time to generate gold-standard answers spanning 233 papers. My budget is also limited, so I can't generate answers to thousands of questions.

**Potential Solution**: Use a state-of-the-art frontier model as an LLM judge to atuomate the process. This won't be as good as a human in the loop, but could fit within my time constraints.
