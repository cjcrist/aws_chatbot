#!/usr/bin/env python3

import logging
import os
import sys

from fastapi import FastAPI
from .api.routes import router
from dotenv import load_dotenv

load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger('chatbot')

app = FastAPI()

# Register routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("chatbot.main:app", host="127.0.0.1", port=8000, reload=True)
