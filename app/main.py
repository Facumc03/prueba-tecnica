import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.core.node_parser import SentenceSplitter

from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

# ====== Config simple (después lo pasamos a env vars) ======
UPLOAD_DIR = "uploads"
CHROMA_DIR = "chroma_db"
COLLECTION = "docs"

app = FastAPI(title="RAG API (Chroma local)")

# ====== Inicializar Chroma persistente ======
os.makedirs(CHROMA_DIR, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
chroma_collection = chroma_client.get_or_create_collection(COLLECTION)

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# ====== Helpers ======
def ensure_dirs():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def build_index_from_files(paths: list[str]) -> int:
    reader = SimpleDirectoryReader(input_files=paths, filename_as_id=True)
    docs = reader.load_data()

    splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=150)

    VectorStoreIndex.from_documents(
        docs,
        storage_context=storage_context,
        transformations=[splitter],
        show_progress=False,
    )
    return len(docs)

# ====== API models ======
class QueryReq(BaseModel):
    q: str
    top_k: int = 5

@app.get("/health")
def health():
    return {"status": "ok", "vector_store": "chroma", "collection": COLLECTION}

@app.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)):
    ensure_dirs()
    saved = []
    skipped = 0

    for f in files:
        name = f.filename or "file"
        if not name.lower().endswith((".txt", ".pdf")):
            skipped += 1
            continue
        content = await f.read()
        path = os.path.join(UPLOAD_DIR, name)
        with open(path, "wb") as out:
            out.write(content)
        saved.append(path)

    if not saved:
        return {"ingested": 0, "skipped": skipped, "errors": ["no valid files"]}

    try:
        ing = build_index_from_files(saved)
        return {"ingested": ing, "skipped": skipped, "errors": []}
    except Exception as e:
        return {"ingested": 0, "skipped": skipped, "errors": [str(e)]}

@app.post("/query")
def query(req: QueryReq):
    if not req.q.strip():
        raise HTTPException(400, "q vacío")

    top_k = max(1, min(req.top_k, 20))

    # engine desde el vector store persistente
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context
    )
    engine = index.as_query_engine(similarity_top_k=top_k)

    resp = engine.query(req.q)

    sources = []
    for sn in getattr(resp, "source_nodes", []) or []:
        node = sn.node
        meta = node.metadata or {}
        sources.append({
            "filename": meta.get("file_name") or meta.get("filename"),
            "page": meta.get("page_label") or meta.get("page"),
            "score": float(getattr(sn, "score", 0.0) or 0.0),
            "snippet": (node.get_text() or "")[:300]
        })

    if not sources:
        return {
            "answer": "No encontré contexto relevante en los documentos para responder con evidencia.",
            "sources": [],
            "retrieval_params": {"top_k": top_k}
        }

    return {
        "answer": str(resp),
        "sources": sources,
        "retrieval_params": {"top_k": top_k}
    }