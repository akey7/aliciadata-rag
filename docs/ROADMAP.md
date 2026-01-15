# Roadmap of Future Steps

## 1. Containerization
- **Current**: Direct deployment on VPS
- **Trade-off**: Simpler initial deployment, harder to reproduce locally
- **Next Step**: Dockerize for reproducibility and easier local development

## 2. Concurrent User Testing
- **Current**: Single VPS designed for sequential access
- **Gap**: Unknown behavior under concurrent load
- **Next Step**: Load testing with locust.py (target: 5 concurrent users)

## 3. Evaluation Framework
- **Current**: Manual testing with sample queries
- **Gap**: No quantitative retrieval accuracy or answer quality metrics
- **Next Step**: Build evaluation dataset with 50+ Q&A pairs + ground truth
  - Metrics: Retrieval recall@5, context relevance, answer correctness
  - Baseline comparison: semantic search vs. hybrid vs. reranking

## 4. Context Window Management
- **Current**: No explicit truncation; relies on LLM context limits
- **Risk**: Long conversations could exceed context window
- **Next Step**: Implement sliding window or summarization for conversation history
