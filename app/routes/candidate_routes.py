from fastapi import APIRouter, HTTPException, status
from typing import Dict, List
from ..models import Candidate

# In-memory data storage for candidates
in_memory_candidates: Dict[int, Candidate] = {}

router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"]
)

@router.post("/", response_model=List[Candidate], status_code=status.HTTP_201_CREATED)
async def register_candidates(candidates: List[Candidate]):
    """
    Register one or multiple candidates for the election.
    """
    created_candidates = []
    for candidate in candidates:
        if candidate.candidate_id in in_memory_candidates:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Candidate with ID {candidate.candidate_id} already exists."
            )
        in_memory_candidates[candidate.candidate_id] = candidate
        created_candidates.append(candidate)
    return created_candidates

@router.get("/", response_model=List[Candidate])
async def list_candidates():
    """
    Get all registered candidates.
    """
    return list(in_memory_candidates.values())
