from fastapi import FastAPI
from .routes.voter_routes import router as voter_router
from .routes.candidate_routes import router as candidate_router
from .routes.vote_routes import router as vote_router
from .routes.ballot_routes import router as ballot_router

app = FastAPI(
    title="Voter Management API",
    description="A simple and fast REST API for managing voter data using FastAPI.",
    version="1.0.0",
)

app.include_router(voter_router)
app.include_router(candidate_router)
app.include_router(vote_router)
app.include_router(ballot_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Voter Management API. Navigate to /docs for API documentation."}