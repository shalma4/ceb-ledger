from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.exception import ExceptionRecord, ExceptionStatus
from app.schemas.exception import ExceptionRecordResponse, ExceptionResolveRequest

router = APIRouter(prefix="/exceptions", tags=["Exceptions"])


@router.get("/", response_model=List[ExceptionRecordResponse])
def list_exceptions(
    status_filter: Optional[ExceptionStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(ExceptionRecord)
    if status_filter:
        query = query.filter(ExceptionRecord.status == status_filter.value)
    return query.offset(skip).limit(limit).all()


@router.patch("/{exception_id}/resolve", response_model=ExceptionRecordResponse)
def resolve_exception(
    exception_id: int,
    resolve_data: ExceptionResolveRequest,
    db: Session = Depends(get_db)
):
    exc = db.query(ExceptionRecord).filter(ExceptionRecord.id == exception_id).first()
    if not exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception with ID {exception_id} not found."
        )

    exc.status = ExceptionStatus.RESOLVED.value
    exc.resolution_notes = resolve_data.resolution_notes
    exc.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(exc)
    return exc
