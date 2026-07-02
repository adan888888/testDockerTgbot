#!/usr/bin/env bash
# 本地开发启动：个人账号监听群消息并写入 ~/Documents/工作任务.txt
#
# 用法：
#   ./script/_01.sh
#   bash script/_01.sh
#
# 注意：
#   - 需在终端运行（首次登录要输入手机号、验证码）
#   - 登录态保存在 monitor/session.session（Telethon）
#   - 确保 config.yaml 中 monitor.enabled 为 true

set -e

cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install -q -r requirements.txt

echo "项目目录: $(pwd)"
echo "启动: python run.py"
python run.py
