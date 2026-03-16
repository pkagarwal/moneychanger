from typing import Tuple, Dict

import dotenv
import os
from dotenv import load_dotenv
import requests
import json
import streamlit as st
import os
from openai import OpenAI

token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model_name = "openai/gpt-4o-mini"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

load_dotenv()
EXCHANGERATE_API_KEY = os.getenv('EXCHANGERATE_API_KEY')

def get_exchange_rate(base: str, target: str, amount: str) -> Tuple:
    """Return a tuple of (base, target, amount, conversion_result (2 decimal places))"""
    url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/pair/{base}/{target}/{amount}"
    response = json.loads(requests.get(url).text)
    conversion_result = response['conversion_result']
    return (base, target, amount, f"{conversion_result:.2f}")
    

#print(get_exchange_rate("USD", "EUR", "100")) # Example usage

def call_llm(textbox_input) -> Dict:
    """Make a call to the LLM with the textbox_input as the prompt.
       The output from the LLM should be a JSON (dict) with the base, amount and target"""
       # 1. Define a list of callable tools for the model
    tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "exchange_rate_function",
                        "description": "Convert a given amount of money from one currency to another. Each currency will be represented as a 3-letter code",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "base": {
                                    "type": "string",
                                    "description": "The base or original currency.",
                                },
                                "target": {
                                    "type": "string",
                                    "description": "The target or converted currency",
                                },
                                "amount": {
                                    "type": "string",
                                    "description": "The amount of money to convert from the base currency.",
                                },
                            },
                            "required": ["base", "target", "amount"],
                            "additionalProperties": False,
                        },
                    },
                }
            ]


    try:
        response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": textbox_input,
            }
        ],
        temperature=1.0,
        top_p=1.0,
        max_tokens=1000,
        model=model_name,
        tools = tools,
        )    
    except Exception as e:
        print(f"Exception {e} for {text}")
    else:
        return response#.choices[0].message.content

def run_pipeline(user_input):
    """Based on textbox_input, determine if you need to use the tools (function calling) for the LLM.
    Call get_exchange_rate(...) if necessary"""
    
    response = call_llm(user_input)
    #st.write(response)

    if response.choices[0].finish_reason == "tool_calls":
        # Update this
        response_args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
        base = response_args['base']
        target = response_args['target']
        amount = response_args['amount']
        _,_,_,conversion_result = get_exchange_rate(base, target, amount)
        st.write(f'{base} {amount} is {target} {conversion_result}')
        #st.write(base, target, amount)

    elif response.choices[0].finish_reason == "stop":
        # Update this
        st.write(f"(Function calling not used) and {response.choices[0].message.content}")
    else:
        st.write("NotImplemented")


# Set the title of the app
st.title("Multilingual Money Changer")

# Create a text input box
user_input = st.text_input("Enter the amount and currency: ")

# Create a submit button
if st.button("Submit"):
    # Display the content of the text box when submit is clicked
    run_pipeline(user_input)
    