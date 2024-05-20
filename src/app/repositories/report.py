import asyncio
import logging
import time

from src.app.views.input.report import Detection
from src.core import config

logger = logging.getLogger(__name__)


class Report:
    def __init__(self) -> None:
        pass

    def _check_data_size(self, data: list[Detection]) -> list[Detection] | None:
        return None if len(data) > 5000 else data

    def _filter_valid_time(self, data: list[Detection]) -> list[Detection]:
        current_time = int(time.time())
        min_ts = current_time - 25200  # 7 hours ago
        max_ts = current_time + 3600  # 1 hour in the future
        # [d for d in data if min_ts < d.ts < max_ts]
        output = []

        for d in data:
            if d.ts <= min_ts:
                logger.info(
                    f"invalid: {d.ts} <= {min_ts}, now={current_time}, {d.reporter}"
                )
                continue
            if d.ts >= max_ts:
                logger.info(
                    f"invalid: {d.ts} >= {max_ts}, now={current_time}, {d.reporter}"
                )
                continue
            output.append(d)

        return output

    def _check_unique_reporter(self, data: list[Detection]) -> list[Detection] | None:
        return None if len(set(d.reporter for d in data)) > 1 else data

    async def parse_data(self, data: list[Detection]) -> list[Detection] | None:
        """
        Parse and validate a list of detection data.
        """
        data = self._check_data_size(data)
        if not data:
            logger.warning("invalid data size")
            return None

        data = self._filter_valid_time(data)
        if not data:
            logger.warning("invalid time")
            return None

        data = self._check_unique_reporter(data)
        if not data:
            logger.warning("invalid unique reporter")
            return None
        return data

    async def send_to_kafka(self, data: list[Detection]) -> None:
        detections = [d.model_dump(mode="json") for d in data]
        await asyncio.gather(
            *[config.send_queue.put(detection) for detection in detections]
        )
        return
