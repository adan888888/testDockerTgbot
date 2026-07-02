from __future__ import annotations

import logging
from datetime import datetime

from fastapi import FastAPI

from app.config import Config

logger = logging.getLogger(__name__)


def create_app(conf: Config) -> FastAPI:
    app = FastAPI(title="python-robot", version="1.0.0")

    @app.get("/")
    def health():
        return {
            "code": 0,
            "msg": "服务运行中",
            "data": {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": conf.system_name,
                "monitor": conf.monitor_enabled,
                "runtime": "python",
            },
        }

    return app
