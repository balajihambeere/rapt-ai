import io
import uuid
from pydantic import BaseModel
from fastapi import Depends, FastAPI, Query, UploadFile, File, Form

from models.CrewRAGBotModel import CrewRAGBotModel
from database import lifespan
from models.metadata import Metadata
import json
import numpy as np
from models.OpenAIChatLLMModel import OpenAIChatLLMModel
from models.RagBotModel import RagBotModel
from doc_handler.document_retrieval import DocumentRetrieval  # Add this import
import os  # Add this import
from datetime import datetime  # Add this import
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image


app = FastAPI(lifespan=lifespan)

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


def convert_to_pdf(file: UploadFile, pdf_path: str):
    """Convert non-PDF files to PDF format."""
    print(f"Converting {file.filename} to PDF")

    # Read the file content into memory
    file_content = file.file.read()

    if file.filename.lower().endswith(('.jpeg', '.jpg', '.png')):
        print("Converting image to PDF")
        # Use BytesIO to handle the file content in memory
        image = Image.open(io.BytesIO(file_content))
        image.save(pdf_path, "PDF", resolution=100.0)

    elif file.content_type.startswith('image/'):
        # Reset file pointer since we read it above
        image = Image.open(io.BytesIO(file_content))
        image.save(pdf_path, "PDF", resolution=100.0)

    elif file.content_type == 'text/plain':
        c = canvas.Canvas(pdf_path, pagesize=letter)
        # Decode the file content we read earlier
        text = file_content.decode('utf-8')
        c.drawString(100, 750, text)
        c.save()

    else:
        raise ValueError("Unsupported file type for conversion to PDF")

    # Reset the file pointer for any subsequent operations
    file.file.seek(0)


@app.post("/index_texts/")
async def index_texts_endpoint(metadata: str = Form(...), file: UploadFile = File(...)):
    # Parse the metadata string into a dictionary
    metadata_dict = json.loads(metadata)

    # Convert to your metadata model
    metadata_obj = Metadata(**metadata_dict)
    if 'date_uploaded' not in metadata_dict:
        metadata_dict['date_uploaded'] = datetime.now().isoformat()
    metadata_obj = Metadata(**metadata_dict)
    if not metadata_obj.date_uploaded:
        metadata_obj.date_uploaded = datetime.now().isoformat()
    # Ensure the /tmp directory exists
    os.makedirs("/tmp", exist_ok=True)

    pdf_path = f"/tmp/{file.filename}.pdf"
    if not file.filename.lower().endswith('.pdf'):
        convert_to_pdf(file, pdf_path)
    else:
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

    document_retrieval = DocumentRetrieval()
    num_indexed = document_retrieval.index_texts(
        pdf_path, metadata_obj.model_dump())
    return {"indexed_paragraphs": num_indexed}


@app.post("/query_index/")
async def query_index_endpoint(request: ConversationRequest) -> ConversationResponse:
    """Handles user queries using CrewAI-enhanced RAG model."""
    message = request.text

    # Generate new conversation ID if not provided
    if not request.conversation_id:
        request.conversation_id = str(uuid.uuid4())

    # Initialize conversation if not existing
    if request.conversation_id not in conversations:
        conversations[request.conversation_id] = CrewRAGBotModel()

    bot = conversations[request.conversation_id]
    
    # Generate response using CrewAI pipeline
    response = bot.run(message)

    return ConversationResponse(response=response, conversation_id=request.conversation_id)


# @app.get("/usages/")
# def read_usages(
#     session: SessionDep,
#     offset: int = 0,
#     limit: Annotated[int, Query(le=100)] = 100,
# ) -> list[Usage]:
#     usages = session.exec(np.select(Usage).offset(offset).limit(limit)).all()
#     return usages


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
