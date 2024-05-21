import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware

from src import api
from src.core import config
from src.core.fastapi.dependencies import _kafka
from src.core.fastapi.middleware.logging import LoggingMiddleware

logger = logging.getLogger(__name__)


def init_routers(_app: FastAPI) -> None:
    _app.include_router(api.router)


def make_middleware() -> list[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=[
                "http://osrsbotdetector.com/",
                "https://osrsbotdetector.com/",
                "http://localhost",
                "http://localhost:8080",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(LoggingMiddleware),
    ]
    return middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup initiated")
    config.producer = await _kafka.kafka_producer()
    config.send_queue = asyncio.Queue(maxsize=500)
    asyncio.create_task(
        _kafka.send_messages(
            topic="report",
            producer=config.producer,
            send_queue=config.send_queue,
            shutdown_event=config.sd_event,
        )
    )
    yield
    config.sd_event.set()
    await config.producer.stop()


def create_app() -> FastAPI:
    _app = FastAPI(
        title="Bot-Detector-API",
        description="Bot-Detector-API",
        middleware=make_middleware(),
        lifespan=lifespan,
    )
    init_routers(_app=_app)
    return _app


app = create_app()


@app.get("/")
async def root():
    return {"message": "Hello World"}
