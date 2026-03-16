"""Chroma Cloud retriever for financial documents."""

import chromadb
from openai import OpenAI
from config.settings import (
    CHROMA_API_KEY, CHROMA_TENANT, CHROMA_DATABASE, CHROMA_COLLECTION,
    OPENAI_API_KEY, EMBEDDING_MODEL,
)


def _get_chroma_collection():
    client = chromadb.CloudClient(
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE,
        api_key=CHROMA_API_KEY,
    )
    return client.get_collection(name=CHROMA_COLLECTION)


def _embed_query(text: str) -> list[float]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
    return response.data[0].embedding


def retrieve_docs(query: str, company: str | None = None, n_results: int = 5) -> list[dict]:
    """Retrieve relevant financial documents from Chroma.

    Returns list of {"text": str, "metadata": dict, "distance": float}
    """
    collection = _get_chroma_collection()
    embedding = _embed_query(query)

    where_filter = {"company": company} if company else None

    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where=where_filter,
    )

    docs = []
    for i in range(len(results["documents"][0])):
        docs.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return docs
