# Install dependencies and dev dependencies
```bash
pip install -r requirements-dev.txt

pip install -r requirements.txt
```
# Run api
```bash
## Run app
uvicorn main:app --reload --port 8100
```

```bash
/Applications/workplace/gen/rapt-ai/
├── app.py
├── models.py
├── services.py
├── utils.py
└── requirements.txt
```

```bash
# # Add other dependencies as needed
spacy download en_core_web_sm

# spacy  # Replace with your preferred spaCy version
https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.6.0/en_core_web_sm-3.6.0.tar.gz


```
# run the docker file command
```bash
docker build -t rapt-gen-ai
docker build -t rapt-gen-ai . ; docker run -p 8100:8100 rapt-gen-ai
```