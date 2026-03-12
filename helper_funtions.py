import json
import os
import tempfile

import faiss
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.1")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

client = OpenAI(api_key=OPENAI_API_KEY)


# Save uploaded PDF to a temp file
def save_uploaded_file(uploaded_file):
    suffix = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


# Read PDF and break it into chunks
def load_pdf(file_path):
    reader = PdfReader(file_path)
    chunks = []
    chunk_id = 1

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        page_chunks = split_text(text, chunk_size=1000, overlap=150)

        for chunk in page_chunks:
            chunks.append({
                "id": chunk_id,
                "page": page_number,
                "text": chunk
            })
            chunk_id += 1

    return chunks


# Split long text into smaller overlapping parts
def split_text(text, chunk_size=1000, overlap=150):
    text = " ".join(text.split())
    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])

        if end == len(text):
            break

        start = end - overlap

    return chunks


# Make embeddings for text chunks
def get_embeddings(texts):
    response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=texts
    )
    return [item.embedding for item in response.data]


# Build local FAISS index
def build_faiss_index(embeddings):
    matrix = np.array(embeddings, dtype="float32")
    faiss.normalize_L2(matrix)

    dim = matrix.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(matrix)
    return index


# Find the most relevant chunks for a query
def search_chunks(query, chunks, index, top_k=4):
    query_embedding = get_embeddings([query])[0]
    query_vector = np.array([query_embedding], dtype="float32")
    faiss.normalize_L2(query_vector)

    _, indices = index.search(query_vector, top_k)

    results = []
    for idx in indices[0]:
        if idx < 0:
            continue
        results.append(chunks[idx])

    return results


# Ask the model for JSON
def ask_llm_for_json(system_prompt, user_prompt):
    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return json.loads(response.output_text.strip())


# Ask the model for normal text
def ask_llm_for_text(system_prompt, user_prompt):
    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.output_text.strip()