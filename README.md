# rapt-ai


## 🚀 Introduction

**Welcome to rapt-ai!**

**rapt-ai** is an open-source Retrieval-Augmented Generation (RAG) contextual chatbot designed to provide accurate and relevant responses. It combines retrieval-based models with generative AI to enhance conversations.

Simply upload a PDF document, and rapt-ai will analyze its content, allowing you to ask questions, gain insights, and have meaningful discussions based on the information in the document.
We encourage developers, contributors, and enthusiasts to collaborate and improve this project together!

## 🌟 Features
- Upload Pdf Documents
- Chat with documents
- OCR Implementation

## 📦 Installation

Clone the repository:
```sh
git clone https://github.com/balajihambeere/rapt-ai.git

cd rapt-ai
```

Install dependencies backend:
```sh
cd api

pip install -r requirements.txt
```

Install dependencies frontend:
```sh
cd chat

pip install -r requirements.txt
```

Run the backend project:
```sh
cd api

uvicorn main:app --reload --port 8100 
```

Run the frontend project:
```sh
cd chat

streamlit run app.py
```

## 💡 How to Contribute

We welcome all contributions! Follow these steps to get started:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit (`git commit -m 'Add new feature'`).
4. Push the changes (`git push origin feature-branch`).
5. Open a Pull Request (PR) with a detailed description of your changes.

### 🔖 Contribution Guidelines
- Follow the coding standards and best practices.
- Keep commits clear and descriptive.
- Update documentation if required.
- Ensure all tests pass before submitting PRs.

## 🛠️ Issues & Support

If you find any bugs or issues, please open an issue [here](https://github.com/balajihambeere/rapt-ai/issues).

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

We appreciate your support and contributions! 🎉

