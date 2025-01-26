# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies for Poppler and Tesseract
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install pdf2image Pillow --no-cache-dir -r requirements.txt

# Install the spaCy model
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application code
COPY . .

# Expose port 8100 for the FastAPI app
EXPOSE 8100

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8100"]