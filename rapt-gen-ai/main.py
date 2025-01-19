
from fastapi import FastAPI, UploadFile, File
from typing import List
from models.metadata import Metadata
from services.pinecone_service import batch_upload_texts, delete_texts_from_index, index_texts, query_index

app = FastAPI()


@app.post("/index_texts/")
async def index_texts_endpoint(metadata: Metadata, file: UploadFile = File(...)):
    pdf_path = f"/tmp/{file.filename}"
    with open(pdf_path, "wb") as f:
        f.write(await file.read())
    num_indexed = index_texts(pdf_path, metadata.model_dump())
    return {"indexed_paragraphs": num_indexed}


@app.post("/query_index/")
async def query_index_endpoint(query: str, top_k: int = 5):
    results = query_index(query, top_k)
    return {"results": results}


@app.post("/delete_texts/")
async def delete_texts_endpoint(text_ids: List[str]):
    delete_texts_from_index(text_ids)
    return {"deleted_texts": text_ids}


@app.post("/batch_upload_texts/")
async def batch_upload_texts_endpoint(metadata_list: List[Metadata], files: List[UploadFile] = File(...)):
    pdf_paths = []
    for file in files:
        pdf_path = f"/tmp/{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(await file.read())
        pdf_paths.append(pdf_path)
    total = batch_upload_texts(
        pdf_paths, [metadata.model_dump() for metadata in metadata_list])
    return {"batch_uploaded_paragraphs": total}
