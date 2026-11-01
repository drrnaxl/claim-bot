import os
import json
from openai import OpenAI


client = OpenAI(
    api_key=os.getenv(
        "OPENAI_API_KEY"
    )
)


def generate_title(text):

    response = client.chat.completions.create(
        model="gpt-4o-mini",

        messages=[
            {
                "role": "system",

                "content":
                """
                Generate a concise UBC
                reimbursement description.

                Return JSON:
                {
                   "category":"",
                   "purpose":""
                }
                """
            },

            {
                "role": "user",
                "content": text[:10000]
            }
        ],

        response_format={
            "type": "json_object"
        }
    )

    return json.loads(
        response
        .choices[0]
        .message
        .content
    )