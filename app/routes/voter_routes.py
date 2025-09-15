from fastapi import APIRouter, HTTPException, status
from typing import Dict, List
from ..models import Voter

# In-memory data storage for voters
in_memory_voters: Dict[int, Voter] = {}

router = APIRouter(
    prefix="/voters",
    tags=["Voters"]
)

@router.post("/", response_model=List[Voter], status_code=status.HTTP_201_CREATED)
async def create_voters(voters: List[Voter]):
    """
    Creates one or more voters.
    """
    created_voters = []
    for voter in voters:
        if voter.voter_id in in_memory_voters:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Voter with ID {voter.voter_id} already exists."
            )
        in_memory_voters[voter.voter_id] = voter
        created_voters.append(voter)

    return created_voters

@router.get("/", response_model=List[Voter])
async def get_all_voters():
    """
    Retrieves all voters.
    """
    return list(in_memory_voters.values())

@router.get("/{voter_id}", response_model=Voter)
async def get_voter_by_id(voter_id: int):
    """
    Retrieves a single voter by their ID.
    """
    voter = in_memory_voters.get(voter_id)
    if not voter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voter with ID {voter_id} not found."
        )
    return voter

@router.put("/{voter_id}", response_model=Voter)
async def update_voter(voter_id: int, updated_voter: Voter):
    """
    Updates an existing voter.
    """
    if voter_id not in in_memory_voters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voter with ID {voter_id} not found."
        )
    in_memory_voters[voter_id] = updated_voter
    return updated_voter

@router.delete("/{voter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voter(voter_id: int):
    """
    Deletes a voter by their ID.
    """
    if voter_id not in in_memory_voters:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voter with ID {voter_id} not found."
        )
    del in_memory_voters[voter_id]
    return {}
