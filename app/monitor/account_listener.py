from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from telethon import TelegramClient, events
from telethon.tl.custom.dialog import Dialog

from app.config import Config, MonitorGroup, resolve_task_file_path, task_file_path
from app.tools.task_file import append_group_message

logger = logging.getLogger(__name__)


@dataclass
class GroupTarget:
    name: str
    chat_id: int


async def run_monitor(conf: Config) -> None:
    if not conf.monitor_api_id or not conf.monitor_api_hash:
        raise ValueError("请在 config.yaml 的 monitor 段填写 apiId 和 apiHash（https://my.telegram.org/apps）")

    groups = conf.monitor_groups
    if not groups:
        raise ValueError("请在 config.yaml 的 monitor 段填写 groups，或 groupName / groupChatId")

    task_file = resolve_task_file_path(task_file_path(conf))
    session_path = conf.monitor_session.strip() or "monitor/session"
    if session_path.endswith(".json"):
        session_path = session_path[:-5]
    Path(session_path).parent.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(session_path, conf.monitor_api_id, conf.monitor_api_hash)
    if conf.monitor_phone:
        await client.start(phone=conf.monitor_phone)
    else:
        # 未配置 phone 且无 session 时，Telethon 会在终端交互式询问手机号/验证码。
        await client.start()

    targets = await _resolve_group_targets(client, groups)
    target_ids = {target.chat_id for target in targets}
    target_by_id = {target.chat_id: target.name for target in targets}

    me = await client.get_me()
    display_name = me.first_name or "unknown"
    if me.username:
        display_name = f"{display_name} (@{me.username})"
    logger.info("个人账号 %s 已就绪，等待群消息...", display_name)

    @client.on(events.NewMessage(chats=list(target_ids)))
    async def handle_message(event: events.NewMessage.Event) -> None:
        chat_id = event.chat_id
        group_name = target_by_id.get(chat_id, "")
        text = (event.raw_text or "").strip() or "[非文本消息]"
        sender_name = _format_sender(await event.get_sender())

        try:
            append_group_message(task_file, group_name, sender_name, text)
        except OSError as exc:
            logger.error("写入工作任务失败: %s", exc)
            return

        logger.info("[%s] %s: %s", group_name, sender_name, text)

    await client.run_until_disconnected()


async def _resolve_group_targets(client: TelegramClient, groups: list[MonitorGroup]) -> list[GroupTarget]:
    need_lookup = any(group.chat_id == 0 and group.name for group in groups)
    dialogs: list[Dialog] | None = None
    if need_lookup:
        dialogs = [dialog async for dialog in client.iter_dialogs(limit=100)]

    targets: list[GroupTarget] = []
    for group in groups:
        name = group.name.strip()
        chat_id = group.chat_id
        if chat_id == 0:
            if not name:
                raise ValueError("监听群需填写 name 或 chatId")
            if dialogs is None:
                dialogs = [dialog async for dialog in client.iter_dialogs(limit=100)]
            chat_id = _find_group_chat_id(dialogs, name)
        if not name:
            name = f"chat:{chat_id}"
        targets.append(GroupTarget(name=name, chat_id=chat_id))
    return targets


def _find_group_chat_id(dialogs: list[Dialog], title: str) -> int:
    for dialog in dialogs:
        if dialog.name and dialog.name.lower() == title.lower():
            return dialog.id
    raise ValueError(f'未找到名为 "{title}" 的群，请确认个人账号已加入该群')


def _format_sender(sender) -> str:
    if sender is None:
        return "unknown"
    username = getattr(sender, "username", None)
    if username:
        return f"@{username}"

    first_name = getattr(sender, "first_name", "") or ""
    last_name = getattr(sender, "last_name", "") or ""
    name = f"{first_name} {last_name}".strip()
    if name:
        return name

    sender_id = getattr(sender, "id", None)
    if sender_id is not None:
        return f"user:{sender_id}"
    return "unknown"
