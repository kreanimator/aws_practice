import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('key.env')

api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)


subject = 'Lost in the forest at night.'
prompt = f'Generate a cool story for "{subject}"'

# Generate text completion
response = client.completions.create(
    model="davinci-002",
    prompt=prompt,
    max_tokens=32
)

# Print the generated response
print(response.choices[0].text.strip())
