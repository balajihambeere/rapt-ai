from crewai import Agent, Task, Crew
# from crewai import tools as Tool
from crewai.tools.base_tool import BaseTool
from pydantic import BaseModel
from typing import List, Tuple, Any
import datetime
from doc_handler.document_retrieval import DocumentRetrieval
from models.OpenAIChatLLMModel import OpenAIChatLLMModel
# from OpenAIChatLLMModel import OpenAIChatLLMModel


class DocumentRetrievalTool(BaseTool):
    name: str = "Document Retrieval Tool"
    description: str = "A tool for retrieving documents from the knowledge base"

    def _run(self, query: str) -> str:
        # Implement your document retrieval logic here
        # This method must be implemented since it's required by BaseTool
        try:
            # Your document retrieval implementation
            # For example:
            return DocumentRetrieval().query_index(query)
            # return "Retrieved document content"
        except Exception as e:
            return f"Error retrieving document: {str(e)}"


# Define tools
document_retrieval_tool = DocumentRetrievalTool()

# # Define tools
# document_retrieval_tool = BaseTool(
#     name="RetrieveContext",
#     description="Fetches relevant documents based on user queries.",
#     func=lambda query: DocumentRetrieval().query_index(query)
# )

# Define Agents
retriever_agent = Agent(
    role="RetrieverAgent",
    goal="Retrieve the most relevant documents based on user queries.",
    backstory="I am a specialized agent focused on retrieving relevant documents from the knowledge base. I use advanced search and retrieval techniques to find the most pertinent information.",
    tools=[document_retrieval_tool],
    verbose=True
)

reasoning_agent = Agent(
    role="ReasoningAgent",
    goal="Analyze the retrieved documents and extract meaningful information.",
    backstory="I am an analytical agent that processes retrieved documents to extract key insights and meaningful patterns. I excel at understanding context and identifying important information.",
    verbose=True
)

response_agent = Agent(
    role="ResponseAgent",
    goal="Generate a structured and informative response based on the extracted context.",
    backstory="I am a communication specialist that transforms analyzed information into clear, well-structured responses. I ensure the final output is coherent and directly addresses the user's query.",
    verbose=True
)

# Define Prompt Template
PROMPT_TEMPLATE = """
Today is {today}. Use the provided context to answer the user's question accurately. 

## User Query:
{user_input}

## Retrieved Context:
{context}

## Assistant Thought:
{assistant_thought}

## Final Response:
"""

class CrewRAGBotModel(BaseModel):
    llm: Any = OpenAIChatLLMModel(temperature=0.7, model="gpt-4o")
    conversation_history: List[Tuple[str, str]] = []

    def run(self, query: str) -> str:
        # Create Crew instance
        crew = Crew(
            agents=[retriever_agent, reasoning_agent, response_agent]
        )

        # Step 1: Retrieval
        retrieval_task = Task(
            description="Retrieve relevant context for the user's query.",
            agent=retriever_agent,
            input=query
        )
        retrieved_data = crew.execute([retrieval_task])
        context = retrieved_data[0] if retrieved_data else "No relevant context found."

        # Step 2: Reasoning
        reasoning_task = Task(
            description="Analyze the retrieved context to extract key details.",
            agent=reasoning_agent,
            input=context
        )
        reasoning_output = crew.execute([reasoning_task])

        # Step 3: Response Generation
        prompt = PROMPT_TEMPLATE.format(
            today=datetime.date.today(),
            user_input=query,
            context=context,
            assistant_thought=reasoning_output[0] if reasoning_output else "No additional thoughts.",
        )
        response = self.llm.generate(prompt, stop=["Final Response:"])

        # Store in history
        self.conversation_history.append((query, response))

        return response
