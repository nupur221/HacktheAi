from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from ..models import Candidate, Voter

# Import in-memory storage (from candidate & voter modules)
from .candidate_routes import in_memory_candidates
from .voter_routes import in_memory_voters

router = APIRouter(
    prefix="/votes",
    tags=["Voting"]
)

# Track votes: candidate_id -> number of votes (weighted included)
candidate_votes: Dict[int, int] = {}

# Track which voters have already voted
voter_voted: Dict[int, bool] = {}

# Track vote timeline: candidate_id -> list of vote events
class VoteRecord(BaseModel):
    voter_id: int
    timestamp: datetime
    weight: int = 1

vote_timeline: Dict[int, List[VoteRecord]] = {}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def cast_vote(voter_id: int, candidate_id: int):
    """
    Cast a vote for a candidate with validation to prevent duplicate voting.
    """
    # Check if voter exists
    if voter_id not in in_memory_voters:
        raise HTTPException(status_code=404, detail="Voter not found.")

    # Check if voter is 18+
    if in_memory_voters[voter_id].age < 18:
        raise HTTPException(status_code=403, detail="Voter must be at least 18 years old.")

    # Check if candidate exists
    if candidate_id not in in_memory_candidates:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Prevent double voting
    if voter_voted.get(voter_id, False):
        raise HTTPException(status_code=409, detail="Voter has already cast a vote.")

    # Cast vote (weight = 1)
    candidate_votes[candidate_id] = candidate_votes.get(candidate_id, 0) + 1
    voter_voted[voter_id] = True

    # Add timestamp to vote timeline
    record = VoteRecord(voter_id=voter_id, timestamp=datetime.utcnow(), weight=1)
    vote_timeline.setdefault(candidate_id, []).append(record)

    return {"message": f"Voter {voter_id} successfully voted for candidate {candidate_id}"}


class WeightedVoteRequest(BaseModel):
    voter_id: int
    candidate_id: int
    profile_updated: bool  # Example condition for weighting


@router.post("/weighted", status_code=status.HTTP_201_CREATED)
async def cast_weighted_vote(request: WeightedVoteRequest):
    """
    Cast a weighted vote based on voter profile update status.
    """
    voter_id = request.voter_id
    candidate_id = request.candidate_id
    profile_updated = request.profile_updated

    # Check if voter exists
    if voter_id not in in_memory_voters:
        raise HTTPException(status_code=404, detail="Voter not found.")

    # Check if voter is 18+
    if in_memory_voters[voter_id].age < 18:
        raise HTTPException(status_code=403, detail="Voter must be at least 18 years old.")

    # Check if candidate exists
    if candidate_id not in in_memory_candidates:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Prevent double voting
    if voter_voted.get(voter_id, False):
        raise HTTPException(status_code=409, detail="Voter has already cast a vote.")

    # Determine weight
    weight = 2 if profile_updated else 1

    # Cast weighted vote
    candidate_votes[candidate_id] = candidate_votes.get(candidate_id, 0) + weight
    voter_voted[voter_id] = True

    # Add timestamp with weight
    record = VoteRecord(voter_id=voter_id, timestamp=datetime.utcnow(), weight=weight)
    vote_timeline.setdefault(candidate_id, []).append(record)

    return {"message": f"Voter {voter_id} cast a weighted vote ({weight}) for candidate {candidate_id}"}


@router.get("/candidate/{candidate_id}/votes")
async def get_candidate_votes(candidate_id: int):
    """
    Get the vote count for a specific candidate.
    """
    if candidate_id not in in_memory_candidates:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    return {
        "candidate_id": candidate_id,
        "name": in_memory_candidates[candidate_id].name,
        "votes": candidate_votes.get(candidate_id, 0)
    }


@router.get("/candidates/party/{party_name}")
async def filter_candidates_by_party(party_name: str):
    """
    Filter candidates by political party.
    """
    filtered = [
        candidate for candidate in in_memory_candidates.values()
        if candidate.party.lower() == party_name.lower()
    ]
    if not filtered:
        raise HTTPException(status_code=404, detail="No candidates found for this party.")
    return filtered


@router.get("/results")
async def voting_results():
    """
    Get complete voting results (leaderboard).
    """
    results = [
        {
            "candidate_id": c.candidate_id,
            "name": c.name,
            "party": c.party,
            "votes": candidate_votes.get(c.candidate_id, 0)
        }
        for c in in_memory_candidates.values()
    ]

    # Sort by votes (descending)
    results = sorted(results, key=lambda x: x["votes"], reverse=True)
    return results


@router.get("/results/winner")
async def get_winner():
    """
    Get the winning candidate(s), handling ties appropriately.
    """
    if not candidate_votes:
        raise HTTPException(status_code=404, detail="No votes have been cast yet.")

    # Find max vote count
    max_votes = max(candidate_votes.values(), default=0)

    # Collect all candidates with max votes (handle tie)
    winners = [
        {
            "candidate_id": c.candidate_id,
            "name": c.name,
            "party": c.party,
            "votes": candidate_votes.get(c.candidate_id, 0)
        }
        for c in in_memory_candidates.values()
        if candidate_votes.get(c.candidate_id, 0) == max_votes
    ]

    return {"winners": winners, "max_votes": max_votes}


@router.get("/timeline/{candidate_id}")
async def get_vote_timeline(candidate_id: int):
    """
    Get the timeline of votes for a specific candidate.
    """
    if candidate_id not in in_memory_candidates:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    timeline = vote_timeline.get(candidate_id, [])
    return {
        "candidate_id": candidate_id,
        "name": in_memory_candidates[candidate_id].name,
        "timeline": [
            {"voter_id": r.voter_id, "timestamp": r.timestamp.isoformat(), "weight": r.weight}
            for r in timeline
        ]
    }


@router.get("/range")
async def get_votes_in_range(
    candidate_id: int,
    from_time: datetime = Query(..., alias="from"),
    to_time: datetime = Query(..., alias="to")
):
    """
    Get votes for a candidate within a specific time range.
    """
    if candidate_id not in in_memory_candidates:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    timeline = vote_timeline.get(candidate_id, [])
    filtered = [
        {"voter_id": r.voter_id, "timestamp": r.timestamp.isoformat(), "weight": r.weight}
        for r in timeline
        if from_time <= r.timestamp <= to_time
    ]

    return {
        "candidate_id": candidate_id,
        "name": in_memory_candidates[candidate_id].name,
        "votes_in_range": filtered,
        "total_weight": sum(r["weight"] for r in filtered)
    }
