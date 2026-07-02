from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class MonitorGroup:
    name: str = ""
    chat_id: int = 0


@dataclass
class Config:
    system_name: str = "监听群消息机器人"
    monitor_enabled: bool = False
    monitor_api_id: int = 0
    monitor_api_hash: str = ""
    monitor_phone: str = ""
    monitor_task_file: str = ""
    monitor_session: str = "monitor/session"
    monitor_groups: list[MonitorGroup] = field(default_factory=list)
    tgbot_task_file: str = ""


def load_config(path: str = "config.yaml") -> Config:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    system = raw.get("system") or {}
    monitor = raw.get("monitor") or {}
    tgbot = raw.get("tgbot") or {}

    groups: list[MonitorGroup] = []
    for item in monitor.get("groups") or []:
        groups.append(
            MonitorGroup(
                name=str(item.get("name") or "").strip(),
                chat_id=int(item.get("chatId") or 0),
            )
        )

    if not groups:
        legacy_name = str(monitor.get("groupName") or "").strip()
        legacy_chat_id = int(monitor.get("groupChatId") or 0)
        if legacy_name or legacy_chat_id:
            groups.append(MonitorGroup(name=legacy_name, chat_id=legacy_chat_id))

    return Config(
        system_name=str(system.get("name") or "监听群消息机器人"),
        monitor_enabled=bool(monitor.get("enabled")),
        monitor_api_id=int(monitor.get("apiId") or 0),
        monitor_api_hash=str(monitor.get("apiHash") or "").strip(),
        monitor_phone=str(monitor.get("phone") or "").strip(),
        monitor_task_file=str(monitor.get("taskFile") or "").strip(),
        monitor_session=str(monitor.get("session") or "monitor/session").strip() or "monitor/session",
        monitor_groups=groups,
        tgbot_task_file=str(tgbot.get("taskFile") or "").strip(),
    )


def task_file_path(conf: Config) -> str:
    if conf.monitor_task_file:
        return conf.monitor_task_file
    if conf.tgbot_task_file:
        return conf.tgbot_task_file
    return ""


def resolve_task_file_path(configured: str = "") -> str:
    """解析群消息写入路径，优先级：环境变量 > config.yaml > 本机默认路径。"""
    # Docker compose 注入：/data/documents/工作任务.txt（挂载到本机 ~/Documents）
    env_path = os.getenv("TASK_FILE", "").strip()
    if env_path:
        return env_path
    # config.yaml 中 monitor.taskFile / tgbot.taskFile（由 task_file_path 传入）
    if configured:
        return configured
    # 本地开发默认：~/Documents/工作任务.txt
    return str(Path.home() / "Documents" / "工作任务.txt")
