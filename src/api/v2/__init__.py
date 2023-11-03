from fastapi import APIRouter

from . import feedback, player, prediction, report

router = APIRouter()
router.include_router(player.router)
router.include_router(prediction.router)
router.include_router(report.router)
router.include_router(feedback.router)
