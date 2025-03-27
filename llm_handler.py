from enum import Enum
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class CADResponse(BaseModel):
    code: str
    parameters: dict
    description: Optional[str] = None

class CADCopilot:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    def generate_code(self, prompt: str) -> CADResponse:
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-2024-04-09",
            response_format={"type": "json_object"},
            messages=[{
                "role": "system",
                "content": """You are a CadQuery code generator. Always return JSON with:
- "code": Valid Python code using CadQuery
- "parameters": Adjustable variables with min/max values
- "description": Brief explanation (optional)

Example Response:
```json
{
  "code": "result = (cq.Workplane('XY').box(20, 20, 5).edges('|Z').fillet(2))",
  "parameters": {
    "width": {"value": 20, "min": 10, "max": 50},
    "height": {"value": 20, "min": 10, "max": 50},
    "thickness": {"value": 5, "min": 2, "max": 10},
    "fillet_radius": {"value": 2, "min": 1, "max": 5}
  },
  "description": "A rectangular plate with filleted edges"
}
```"""
            }, {
                "role": "user",
                "content": prompt
            }],
            temperature=0.3
        )
        
        try:
            import json
            raw = response.choices[0].message.content
            return CADResponse(**json.loads(raw))
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {str(e)}")