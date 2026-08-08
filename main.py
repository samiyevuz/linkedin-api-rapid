from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

from scraper import LinkedinScraper

app = FastAPI(
    title="LinkedIn Media Scraper API",
    description="API for anonymously downloading media (videos) from LinkedIn posts without cookies.",
    version="1.0.0"
)

class MediaItem(BaseModel):
    type: str
    url: str
    quality: Optional[str] = None
    title: Optional[str] = None

class LinkedinResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    media: Optional[List[MediaItem]] = None

@app.get("/", include_in_schema=False)
def root():
    return {"message": "LinkedIn Media Scraper API is running. Go to /docs for Swagger UI."}

@app.get("/api/v1/download", response_model=LinkedinResponse)
async def download_linkedin_post(url: str = Query(..., description="LinkedIn post URL")):
    """
    Extract media directly from a LinkedIn post URL anonymously.
    Note: Statistics (likes, comments) are not available in this anonymous mode.
    """
    scraper = LinkedinScraper()
    
    result = await scraper.get_media_only(url)
    
    if not result.get("success"):
        return LinkedinResponse(success=False, error=result.get("error"))
        
    return LinkedinResponse(**result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
