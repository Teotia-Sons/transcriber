from typing import cast

import litellm
from litellm import ModelResponse

from config import Config

PUNCTUATION_PROMPT = """Fix punctuation and capitalization in the following spoken text.

Text to fix: {text}

Return only the corrected text without any explanations or markdown formatting.

Corrected text:"""


def fix_punctuation(text: str) -> str:
    response = cast(ModelResponse, litellm.completion(
        model="cerebras/gpt-oss-120b",
        api_key=Config.CEREBRAS_API_KEY,
        messages=[
            {"role": "user", "content": PUNCTUATION_PROMPT.format(text=text)}
        ],
        temperature=0.0,
    ))

    content = response.choices[0].message.content
    assert content is not None
    return content.strip()
