import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test the prompt building
from backend.llm import build_prompt

query = "i am suffering from pain in my chest left side."
context = "Some medical context"

messages = build_prompt(query, context)

print("System prompt:")
print(messages[0]['content'])
print("\nUser message:")
print(messages[1]['content'])