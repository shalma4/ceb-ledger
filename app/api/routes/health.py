from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
def check_health():
    return {"status": "ok", "service": "CEB-Ledger"}
