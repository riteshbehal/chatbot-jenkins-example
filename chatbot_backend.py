"""Backend logic for the Streamlit Bedrock chatbot."""

import os
from functools import lru_cache

from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain_aws import ChatBedrockConverse


DEFAULT_MODEL_ID = "amazon.nova-pro-v1:0"
DEFAULT_AWS_REGION = "us-east-1"


def _get_float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@lru_cache(maxsize=1)
def get_llm():
    """Create the Bedrock chat model once and reuse it.

    Credentials are loaded from the standard AWS provider chain. On EC2, the
    recommended setup is to attach an IAM role to the Jenkins/hosting instance.
    For local development, set AWS_PROFILE if you want to use an AWS CLI profile.
    """

    aws_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION", DEFAULT_AWS_REGION)
    model_id = os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
    aws_profile = os.getenv("AWS_PROFILE")

    llm_kwargs = {
        "model": model_id,
        "region_name": aws_region,
        "temperature": _get_float_env("LLM_TEMPERATURE", 0.3),
        "max_tokens": _get_int_env("LLM_MAX_TOKENS", 1000),
    }

    # Do not force profile usage inside Docker. Only use it when explicitly set.
    if aws_profile:
        llm_kwargs["credentials_profile_name"] = aws_profile

    return ChatBedrockConverse(**llm_kwargs)


def get_memory():
    """Create memory for one Streamlit user session."""
    return ConversationSummaryBufferMemory(
        llm=get_llm(),
        max_token_limit=_get_int_env("MEMORY_MAX_TOKEN_LIMIT", 2000),
        return_messages=True,
    )


def generate_response(input_text, memory):
    """Generate a chatbot response using LangChain conversation memory."""
    conversation = ConversationChain(
        llm=get_llm(),
        memory=memory,
        verbose=False,
    )

    response = conversation.invoke({"input": input_text})
    return response["response"]
