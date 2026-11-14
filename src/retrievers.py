"""Retrieval methods: Dense (ChromaDB Day 6), Lexical (BM25), and Hybrid (RRF)."""
import math
import re
from typing import Any
import chromadb
from sentence_transformers import SentenceTransformer

class DenseRetriever:
    """Phương pháp 1: Dense Retrieval dùng ChromaDB và all-MiniLM-L6-v2 từ Day 6."""
    def __init__(self, chroma_path: str, collection_name: str = "strategy_B", model_name: str = "all-MiniLM-L6-v2"):
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_collection(collection_name)
        self.embedder = SentenceTransformer(model_name)

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        query_vec = self.embedder.encode(query).tolist()
        chroma_filter = filters if filters else None
        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            where=chroma_filter
        )
        hits = []
        if results and results["ids"] and results["ids"][0]:
            for cid, doc, meta, dist in zip(results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0]):
                score = round(1.0 - dist, 4) if dist is not None else 0.0
                hits.append({
                    "id": cid,
                    "text": doc,
                    "source_id": meta.get("document_id", "fao_seaweed_guide"),
                    "source": meta.get("source", "data/fao_seaweed_guide.pdf"),
                    "page": meta.get("page", 1),
                    "score": score,
                    "metadata": meta
                })
        return hits


class BM25Retriever:
    """Phương pháp 2: Lexical BM25 Retrieval chạy trực tiếp trên corpus chunks."""
    def __init__(self, chunks: list[dict[str, Any]]):
        self.chunks = chunks
        self.doc_len = [len(self._tokenize(c["text"])) for c in chunks]
        self.avgdl = sum(self.doc_len) / max(len(chunks), 1)
        self.k1 = 1.5
        self.b = 0.75
        self.df = {}
        self.doc_freqs = []
        for c in chunks:
            tokens = self._tokenize(c["text"])
            freqs = {}
            for t in tokens:
                freqs[t] = freqs.get(t, 0) + 1
            self.doc_freqs.append(freqs)
            for t in set(tokens):
                self.df[t] = self.df.get(t, 0) + 1

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        q_tokens = self._tokenize(query)
        scores = []
        N = len(self.chunks)
        for idx, c in enumerate(self.chunks):
            # Kiểm tra metadata filter nếu có
            if filters:
                match = all(c.get("metadata", {}).get(k) == v or c.get(k) == v for k, v in filters.items())
                if not match:
                    continue
            score = 0.0
            freqs = self.doc_freqs[idx]
            d_len = self.doc_len[idx]
            for t in q_tokens:
                if t in freqs:
                    n_t = self.df.get(t, 0)
                    idf = math.log((N - n_t + 0.5) / (n_t + 0.5) + 1.0)
                    tf = freqs[t]
                    num = tf * (self.k1 + 1)
                    denom = tf + self.k1 * (1 - self.b + self.b * (d_len / self.avgdl))
                    score += idf * (num / denom)
            if score > 0:
                scores.append((score, c))

        scores.sort(key=lambda x: x[0], reverse=True)
        top = scores[:top_k]
        return [{**item, "score": round(sc, 4)} for sc, item in top]


class HybridRRFRetriever:
    """Phương pháp 3: Kết hợp Dense và BM25 bằng Reciprocal Rank Fusion (RRF)."""
    def __init__(self, dense_retriever: DenseRetriever, bm25_retriever: BM25Retriever, k: int = 60):
        self.dense = dense_retriever
        self.bm25 = bm25_retriever
        self.k = k

    def search(self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        dense_hits = self.dense.search(query, filters=filters, top_k=top_k * 2)
        bm25_hits = self.bm25.search(query, filters=filters, top_k=top_k * 2)

        rrf_scores = {}
        chunk_map = {}

        for rank, hit in enumerate(dense_hits, start=1):
            cid = hit["id"]
            chunk_map[cid] = hit
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.k + rank))

        for rank, hit in enumerate(bm25_hits, start=1):
            cid = hit["id"]
            if cid not in chunk_map:
                chunk_map[cid] = hit
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.k + rank))

        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:top_k]
        return [{**chunk_map[cid], "score": round(rrf_scores[cid], 5)} for cid in sorted_ids]