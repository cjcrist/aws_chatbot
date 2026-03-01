# factory.py  -  Agent factory file

import os
import uuid
import logging

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from ..tools import tools

logger = logging.getLogger("agent")

checkpointer = InMemorySaver()

system_prompt = (
    "You are an AWS assistant. Gather information about the user's AWS account and answer their AWS-related questions. Respond in a friendly, helpful manner."
    "If you cannot answer fully, notify the user. Use available tools to look up AWS account data when needed. Format multi-line responses appropriately."
)


def _get_model():
    model_name = os.getenv("MODEL")
    if not model_name:
        raise ValueError("MODEL is not set")
    logger.info(f"Using model {model_name}")

    if ":" not in model_name:
        model_name = f"openai:{model_name}"

    temp = os.getenv("MODEL_TEMP", "0")
    try:
        temperature = float(temp)
    except ValueError:
        temperature = 0

    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set for OpenAI model")

    return init_chat_model(model_name, temperature=temperature)


agent = None


def get_agent():
    global agent
    if agent:
        return agent

    agent = create_agent(
        model=_get_model(),
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )
    return agent


def run_agent(query: str, user_id: str):
    logger.info(f"Running agent for user query: {query}")
    chatbot = get_agent()
    payload = {"messages": [{"role": "user", "content": query}]}
    if not user_id:
        user_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": user_id}}
    response = chatbot.invoke(payload, config = config)
    logger.debug(f"Response: {response}")
    messages = response.get("messages", [])
    if not messages:
        return ""

    content = messages[-1].content
    if isinstance(content, str):
        return content
    return str(content)
