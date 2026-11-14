"""Export Day 6 Strategy B chunks from ChromaDB to data/chunks.json for Day 7."""
import json
from pathlib import Path
import chromadb

def main():
    chroma_path = "D:/LAB AI/lab06/K5-L3A-DAY06-2A202603617-DataIngestion/starter/results/chroma"
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection("strategy_B")
    
    # Get all items from the collection
    results = collection.get(include=["documents", "metadatas"])
    ids = results["ids"]
    docs = results["documents"]
    metadatas = results["metadatas"]
    
    chunks = []
    for cid, doc, meta in zip(ids, docs, metadatas):
        c = {
            "id": cid,
            "text": doc,
            "source_id": meta.get("document_id", "fao_seaweed_guide"),
            "source": meta.get("source", "data/fao_seaweed_guide.pdf"),
            "page": meta.get("page", 1),
            "metadata": {
                "chapter": meta.get("chapter", ""),
                "category": meta.get("category", ""),
                "strategy": meta.get("strategy", "by_paragraph")
            }
        }
        chunks.append(c)
        
    out_path = Path("data/chunks.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported {len(chunks)} chunks to {out_path}")

if __name__ == "__main__":
    main()
