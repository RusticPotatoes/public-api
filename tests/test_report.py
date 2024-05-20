import os
import sys
import time
from typing import Optional

import pytest
from httpx import AsyncClient
from pydantic import BaseModel
from pydantic.fields import Field

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

example_data = {
    "reporter": "player1",
    "reported": "player2",
    "region_id": 1,
    "x_coord": 100,
    "y_coord": 200,
    "z_coord": 300,
    "ts": int(time.time()),  # current timestamp
    "manual_detect": 0,
    "on_members_world": 0,
    "on_pvp_world": 0,
    "world_number": 350,
    "equipment": {
        "equip_head_id": 10,
        "equip_amulet_id": 20,
        "equip_torso_id": 30,
        "equip_legs_id": 40,
        "equip_boots_id": 50,
        "equip_cape_id": 60,
        "equip_hands_id": 70,
        "equip_weapon_id": 80,
        "equip_shield_id": 90,
    },
    "equip_ge_value": 1000,
}


@pytest.mark.asyncio
async def test_valid_report(custom_client):
    global example_data
    endpoint = "/v2/report"
    _data = example_data.copy()
    _data["ts"] = int(time.time())

    # Example of a valid detection data
    detection_data = [_data]

    async with custom_client as client:
        client: AsyncClient
        response = await client.post(endpoint, json=detection_data)
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_invalid_ts_high_report(custom_client):
    global example_data
    endpoint = "/v2/report"
    _data = example_data.copy()
    _data["ts"] = int(time.time()) + 3700

    # Example of a valid detection data
    detection_data = [_data]

    async with custom_client as client:
        client: AsyncClient
        response = await client.post(endpoint, json=detection_data)
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_invalid_ts_low_report(custom_client):
    global example_data
    endpoint = "/v2/report"
    _data = example_data.copy()
    _data["ts"] = int(time.time()) - 25300

    # Example of a valid detection data
    detection_data = [_data]

    async with custom_client as client:
        client: AsyncClient
        response = await client.post(endpoint, json=detection_data)
        assert response.status_code == 400
