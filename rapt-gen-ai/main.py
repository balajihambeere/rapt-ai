from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form
from typing import List
from models.metadata import Metadata
import json
import numpy as np
from models.OpenAIChatLLMModel import OpenAIChatLLMModel
from models.RagBotModel import RagBotModel
from doc_handler.document_retrieval import DocumentRetrieval  # Add this import


app = FastAPI()

conversations = {}


class ConversationRequest(BaseModel):
    text: str
    temperature: float = 0.1
    threshold: float = 0.3
    namespace: str = "default"
    conversation_id: str = None


class ConversationResponse(BaseModel):
    response: str
    conversation_id: str


def sanitize_results(results):
    return [
        {
            "id": result["id"],
            "metadata": result["metadata"],
            "score": result["score"]
        }
        for result in results
    ]


@app.post("/index_texts/")
async def index_texts_endpoint(metadata: str = Form(...), file: UploadFile = File(...)):
    # Parse the metadata string into a dictionary
    metadata_dict = json.loads(metadata)
    # Convert to your metadata model
    metadata_obj = Metadata(**metadata_dict)
    

    pdf_path = f"/tmp/{file.filename}"
    with open(pdf_path, "wb") as f:
        f.write(await file.read())
    document_retrieval = DocumentRetrieval()
    num_indexed = document_retrieval.index_texts(
        pdf_path, metadata_obj.model_dump())
    return {"indexed_paragraphs": num_indexed}


@app.post("/query_index/")
async def query_index_endpoint(request: ConversationRequest):
    message = request.text
    temperature = request.temperature
    threshold = request.threshold
    # Generate a new conversation_id if not provided
    if request.conversation_id is None:
        request.conversation_id = str(uuid.uuid4())

    if request.conversation_id not in conversations:
        conversations[request.conversation_id] = RagBotModel(
            llm=OpenAIChatLLMModel(
                temperature=temperature, model='gpt-4o'), stop_pattern=['[END]'], verbose=True,
            threshold=threshold)
    bot = conversations[request.conversation_id]
    response = bot.run(message)

    return ConversationResponse(response=response, conversation_id=request.conversation_id)


# @app.post("/delete_texts/")
# async def delete_texts_endpoint(text_ids: List[str]):
#     delete_texts_from_index(text_ids)
#     return {"deleted_texts": text_ids}


# @app.post("/batch_upload_texts/")
# async def batch_upload_texts_endpoint(metadata_list: List[Metadata], files: List[UploadFile] = File(...)):
#     pdf_paths = []
#     for file in files:
#         pdf_path = f"/tmp/{file.filename}"
#         with open(pdf_path, "wb") as f:
#             f.write(await file.read())
#         pdf_paths.append(pdf_path)
#     total = batch_upload_texts(
#         pdf_paths, [metadata.model_dump() for metadata in metadata_list])
#     return {"batch_uploaded_paragraphs": total}
