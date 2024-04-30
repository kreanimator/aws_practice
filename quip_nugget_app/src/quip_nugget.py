import os

from dotenv import load_dotenv
from openai import OpenAI
from typing import List


import argparse
import re

load_dotenv('key.env')
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)


MAX_INPUT_LENGTH = 32


def main():

    print("Running Quip Nugget")
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", type=str, required=True)
    args = parser.parse_args()
    user_input = args.input
    print(f"User input: {user_input}")
    if validate_input(user_input):
        joke_result = generate_joke(user_input)
        fact_result = generate_fact(user_input)
        keyword_result = generate_keywords(user_input)
        print(f"Joke: {joke_result} \nInteresting fact: {fact_result} \nKeywords: {keyword_result}")
    else:
        raise ValueError(f"Input is too long. Must be under {12} symbols! Submitted input is {len(user_input)}")


def validate_input(prompt: str) -> bool:
    return len(prompt) <= MAX_INPUT_LENGTH


def generate_joke(prompt: str) -> str:

    enriched_prompt = f"Generate a joke about {prompt}:"
    print(enriched_prompt)
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=enriched_prompt,
        max_tokens=32
    )

    joke_text: str = response.choices[0].text.strip()
    # joke_text = joke_text.replace('\n', ' ')
    last_char = joke_text[-1]
    if last_char not in {".", "!", "?"}:
        joke_text += "..."

    return joke_text


def generate_fact(prompt: str) -> str:

    enriched_prompt = f"Generate a fan fact about {prompt}:"
    print(enriched_prompt)

    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=enriched_prompt,
        max_tokens=32
    )

    fact_text: str = response.choices[0].text.strip()
    last_char = fact_text[-1]
    if last_char not in {".", "!", "?"}:
        fact_text += "..."

    return fact_text


def generate_keywords(prompt: str) -> List[str]:

    enriched_prompt = f"Generate related branding keywords for {prompt}:"
    print(enriched_prompt)
    response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=enriched_prompt,
        max_tokens=32
    )

    keywords_text = response.choices[0].text.strip()
    keywords_text = re.sub(r'\d+\.', '', keywords_text)
    keywords_text = re.sub(r'\s+', ' ', keywords_text)
    keywords_list = keywords_text.strip().split()
    keywords_list = [k.lower() for k in keywords_list]

    return keywords_list


if __name__ == "__main__":
    main()
