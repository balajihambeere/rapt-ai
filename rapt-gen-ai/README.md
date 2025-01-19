```bash
pip install openai
pip install pinecone-client
pip install tqdm

pip install uvicorn python-dotenv 

pip install PyPDF2

pip install "fastapi[standard]"
```


```bash
/Applications/workplace/gen/rapt-ai/
├── app.py
├── models.py
├── services.py
├── utils.py
└── requirements.txt
```


# Run post method
http://localhost:8000/index_texts/

To use Postman to run the selected endpoint, follow these steps:

Open Postman: Launch the Postman application.

### Create a New Request:

Click on the "New" button and select "Request".
Name your request and save it to a collection if desired.
Set the Request Type and URL:

Set the request type to POST.
Enter the URL for your endpoint. If your server is running locally, it might look something like http://localhost:8000/index_texts/.
Set the Headers:

Click on the "Headers" tab.
Add a header with the key Content-Type and value multipart/form-data.
Set the Body:

Click on the "Body" tab.
Select form-data.
Add two key-value pairs:
Key: metadata, Type: Text, Value: JSON string representing the Metadata object.
Key: file, Type: File, Value: Select the file you want to upload.
Send the Request:

Click the "Send" button.
Check the response in the lower part of the Postman window.


Example
Assuming your Metadata object looks like this:

```json
 {"document_id": "doc123", "date_uploaded": "2025-01-19"}
```
Your Postman setup should look like this:

URL: http://localhost:8000/index_texts/
Headers:
Content-Type: multipart/form-data
Body:
metadata: {"key1": "value1", "key2": "value2"}
file: [Select your file]
After setting this up, click "Send" to make the request. The