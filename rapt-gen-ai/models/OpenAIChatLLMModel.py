from typing import List, Dict, Tuple
from pydantic import BaseModel, Field
# Define a class for the Chat Language Model
from common.config import get_openai_client


client = get_openai_client()


class OpenAIChatLLMModel(BaseModel):
    model: str = 'gpt-4o'  # Default model to use
    temperature: float = 0.0  # Default temperature for generating responses

    class Config:
        arbitrary_types_allowed = True

    # Method to generate a response from the model based on the provided prompt
    def generate(self, prompt: str, stop: List[str] = None):
        # Create a completion request to the OpenAI API with the given parameters
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            stop=stop
        )

        # Return the generated response content
        return response.choices[0].message.content
