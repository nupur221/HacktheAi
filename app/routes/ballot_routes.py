from fastapi import APIRouter, HTTPException, status
from typing import Dict, List
from pydantic import BaseModel
from datetime import datetime
import random

router = APIRouter(
    prefix="/api",
    tags=["Ballots & Analytics"]
)

# ----------------------------
# Data Models
# ----------------------------

class EncryptedBallot(BaseModel):
    voter_id: int
    candidate_id: int
    ciphertext: str   # simulated encrypted vote
    proof: str        # simulated zero-knowledge proof


class RankedBallot(BaseModel):
    voter_id: int
    ranking: List[int]   # list of candidate IDs in ranked order


# Storage
encrypted_ballots: List[EncryptedBallot] = []
ranked_ballots: List[RankedBallot] = []
encrypted_voter_set = set()
ranked_voter_set = set()


# ----------------------------
# Q16: Encrypted Ballot
# ----------------------------
@router.post("/ballots/encrypted", status_code=status.HTTP_201_CREATED)
async def submit_encrypted_ballot(ballot: EncryptedBallot):
    if ballot.voter_id in encrypted_voter_set:
        raise HTTPException(status_code=409, detail="Voter has already submitted an encrypted ballot.")

    if not ballot.ciphertext or not ballot.proof:
        raise HTTPException(status_code=400, detail="Invalid encrypted ballot.")

    encrypted_ballots.append(ballot)
    encrypted_voter_set.add(ballot.voter_id)

    return {"message": "Encrypted ballot submitted successfully", "total_ballots": len(encrypted_ballots)}


# ----------------------------
# Q17: Homomorphic Tally
# ----------------------------
@router.post("/results/homomorphic")
async def homomorphic_tally():
    if not encrypted_ballots:
        raise HTTPException(status_code=404, detail="No encrypted ballots found.")

    tally: Dict[int, int] = {}
    for ballot in encrypted_ballots:
        tally[ballot.candidate_id] = tally.get(ballot.candidate_id, 0) + 1

    return {
        "tally": tally,
        "proof": "simulated-homomorphic-proof",
        "total_ballots": len(encrypted_ballots)
    }


# ----------------------------
# Q18: Differential Privacy Analytics
# ----------------------------
class DPQuery(BaseModel):
    candidate_id: int
    epsilon: float

@router.post("/analytics/dp")
async def differential_privacy_query(query: DPQuery):
    count = sum(1 for b in encrypted_ballots if b.candidate_id == query.candidate_id)
    noise = random.gauss(0, 1.0 / query.epsilon if query.epsilon > 0 else 1.0)
    noisy_count = max(0, round(count + noise))

    return {
        "candidate_id": query.candidate_id,
        "true_count": count,
        "noisy_count": noisy_count,
        "epsilon": query.epsilon
    }


# ----------------------------
# Q19: Ranked-Choice / Condorcet (Schulze Method)
# ----------------------------
@router.post("/ballots/ranked", status_code=status.HTTP_201_CREATED)
async def submit_ranked_ballot(ballot: RankedBallot):
    if ballot.voter_id in ranked_voter_set:
        raise HTTPException(status_code=409, detail="Voter has already submitted a ranked ballot.")

    ranked_ballots.append(ballot)
    ranked_voter_set.add(ballot.voter_id)

    return {"message": "Ranked ballot submitted successfully", "total_ranked": len(ranked_ballots)}


@router.post("/results/schulze")
async def schulze_winner():
    """
    Compute Schulze method winners from ranked ballots (simplified).
    """
    if not ranked_ballots:
        raise HTTPException(status_code=404, detail="No ranked ballots submitted.")

    # Collect candidates
    candidates = set()
    for ballot in ranked_ballots:
        candidates.update(ballot.ranking)
    candidates = list(candidates)

    # Initialize pairwise preference matrix
    pairwise: Dict[int, Dict[int, int]] = {c: {d: 0 for d in candidates if d != c} for c in candidates}

    # Count preferences
    for ballot in ranked_ballots:
        for i, ci in enumerate(ballot.ranking):
            for cj in ballot.ranking[i+1:]:
                pairwise[ci][cj] += 1

    # Compute strongest paths (Floyd–Warshall adaptation)
    strength = {c: {d: 0 for d in candidates} for c in candidates}
    for c in candidates:
        for d in candidates:
            if c != d and pairwise[c][d] > pairwise[d][c]:
                strength[c][d] = pairwise[c][d]

    for i in candidates:
        for j in candidates:
            if i != j:
                for k in candidates:
                    if i != k and j != k:
                        strength[j][k] = max(strength[j][k], min(strength[j][i], strength[i][k]))

    # Determine winner(s)
    winners = []
    for c in candidates:
        if all(strength[c][d] >= strength[d][c] for d in candidates if d != c):
            winners.append(c)

    return {"winners": winners, "audit_trail": pairwise}


# ----------------------------
# Q20: Risk-Limiting Audit (RLA)
# ----------------------------
class AuditRequest(BaseModel):
    total_ballots: int
    risk_limit: float  # e.g., 0.1 for 10%

@router.post("/audits/plan")
async def risk_limiting_audit(request: AuditRequest):
    """
    Produce a ballot-polling audit plan with Kaplan–Markov sequential test (simulated).
    """
    if request.total_ballots <= 0:
        raise HTTPException(status_code=400, detail="Invalid total ballot count.")

    sample_size = int(request.total_ballots * request.risk_limit) + 1

    return {
        "total_ballots": request.total_ballots,
        "risk_limit": request.risk_limit,
        "recommended_sample_size": sample_size,
        "method": "Kaplan–Markov (simulated)"
    }
