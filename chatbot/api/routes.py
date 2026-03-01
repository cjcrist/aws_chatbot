# routes.py

import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..agents import factory

logger = logging.getLogger("api")

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    user_id: str | None = None


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request):
    user_id = payload.user_id or request.headers.get("x-user-id")
    logger.info(f"Received chat request with user_id {user_id}")
    answer = factory.run_agent(payload.query, user_id=user_id)
    return {"answer": answer}
