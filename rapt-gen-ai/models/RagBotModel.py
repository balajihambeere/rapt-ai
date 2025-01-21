from pydantic import BaseModel
from typing import Dict, Optional, Any
from typing import List, Dict, Tuple
from services.pinecone_service import query_index
import datetime


# Prompt Template for RAG Bot
PROMPT_TEMPLATE = """
Today is {today}. Use the provided context to answer the user's question. If no context is available, respond appropriately.

[START]
User Input: {user_input}
Context: {context}
Context Score: {context_score}
Assistant Thought: {assistant_thought}
Assistant Response: {assistant_response}
[END]
"""

# RAG Bot Implementation


class RagBotModel(BaseModel):
    llm: any
    prompt_template: str = PROMPT_TEMPLATE
    user_inputs: List[str] = []
    ai_responses: List[str] = []
    contexts: List[Dict[str, Any]] = []
    verbose: bool = False
    threshold: float = 0.5

    class Config:  # Use this for Pydantic V1
        arbitrary_types_allowed = True

    def run(self, query: str) -> str:
        # Log user input
        self.user_inputs.append(query)

        # Query Pinecone
        matches = query_index(query)

        if matches:
            # loop through matches and add to contexts
            for match in matches:
                # if match["score"] >= self.threshold:
                #     self.contexts.append(match["metadata"]["text"])
                self.contexts.append(match["metadata"]["text"])
            top_context = self.contexts

            # print('top_context', top_context)
            # get score which is greater than threshold
            context_score = matches[0]["score"]
            context_thought = "This context has sufficient information to answer the question."
        else:
            top_context = "NO CONTEXT FOUND"
            context_score = 0
            context_thought = "No relevant context was found."

        # Prepare prompt
        prompt = self.prompt_template.format(
            today=datetime.date.today(),
            user_input=query,
            context=top_context,
            context_score=context_score,
            assistant_thought=context_thought,
            assistant_response="",
        )

        if self.verbose:
            print("Generated Prompt:")
            print(prompt)

        print('prompt', prompt)
        # Generate response
        response = self.llm.generate(prompt, stop=["[END]"])
        self.ai_responses.append(response)

        return response
