import os
from openai import OpenAI
from dotenv import load_dotenv
import argparse

load_dotenv('key.env')


def main():

    print("Running Story Sparker")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", type=str, required=True)
    args = parser.parse_args()
    user_input = args.input
    print(f"User input: {user_input}")
    generate_story(user_input)

def generate_story(prompt: str):

    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key)

    enriched_prompt = f"Generate a short story or anecdote about {prompt}: Keep it short, no more than 200 tokens"
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=enriched_prompt,
        max_tokens=200
    )

    story_text: str = response.choices[0].text
    story_text.strip()
    last_char = story_text[-1]
    if last_char not in {".", "!", "?"}:
        story_text += "..."
    print(story_text)


if __name__ == "__main__":
    main()
