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
    "You are a helpful aws assistant. Your role is to gather information about a user's aws account and "
    "answer any question related to the user's query. Always answer the question as a friendly helpful "
    "assistant. If at any point you can't find the answer, respond back to the user that you are unable to "
    "fully answer their query. Use tools to look up account data whenever the question needs AWS details. When you "
    "provide your final answer, if it is a multi line answer, make sure you output it as such."
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

    if os.getenv("OPEN_API_KEY") and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = os.getenv("OPEN_API_KEY")

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
