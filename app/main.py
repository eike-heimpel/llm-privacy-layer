from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Privacy Container",
    description="API for anonymizing and deanonymizing data for OpenWebUI",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your OpenWebUI URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router from api module
app.include_router(router.router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010) 