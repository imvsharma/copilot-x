from fastapi import APIRouter, Request, Response

from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness/readiness",
    responses={503: {"description": "One or more dependencies unavailable"}},
)
async def health(request: Request, response: Response) -> HealthResponse:
    mongo_db = getattr(request.app.state, "mongo_db", None)
    mongo_status = "ok" if mongo_db is not None else "down"
    redis_client = getattr(request.app.state, "redis", None)
    redis_status = "skipped"
    if redis_client is not None:
        try:
            await redis_client.ping()
            redis_status = "ok"
        except Exception:
            redis_status = "down"

    # Redis was configured (client exists) but must be reachable; skipped = optional cache off
    unhealthy = mongo_status == "down" or redis_status == "down"
    overall = "unhealthy" if unhealthy else "ok"
    if unhealthy:
        response.status_code = 503

    return HealthResponse(
        status=overall,
        mongodb=mongo_status,
        redis=redis_status,
    )
