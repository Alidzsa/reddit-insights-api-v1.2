from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
import os

API_KEY_NAME = "X-API-Key"
# For MVP, we use a simple environment variable or a default key
API_KEY = os.getenv("REDDIT_INSIGHTS_API_KEY", "free-beta-key-2026")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(header_key: str = Security(api_key_header)):
    if header_key == API_KEY:
        return header_key
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials. Please provide a valid X-API-Key."
    )
