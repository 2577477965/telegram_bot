"""
代理模块
当未配置 PROXY_URL 时，尝试自动启动 Shadowsocks 代理。
"""
import json
import os
import socket
import subprocess
import time
import sys

from utils import setup_logger

logger = setup_logger("proxy")

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "daili.json")
SS_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "ss_config.json")
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 1080

_sslocal_proc = None


def _write_ss_config() -> dict | None:
    """从 daili.json 读取配置，写入 sslocal 格式的配置文件"""
    if not os.path.exists(CONFIG_FILE):
        return None

    try:
        with open(CONFIG_FILE, "r") as f:
            raw = json.load(f)
    except Exception:
        return None

    config = {
        "server": raw["host"],
        "server_port": int(raw["port"]),
        "local_address": LOCAL_HOST,
        "local_port": LOCAL_PORT,
        "password": raw["password"],
        "method": "aes-256-cfb",
        "timeout": 300,
    }

    with open(SS_CONFIG_FILE, "w") as f:
        json.dump(config, f)

    return config


def start_sslocal() -> bool:
    """启动本地 Shadowsocks 代理"""
    global _sslocal_proc

    config = _write_ss_config()
    if not config:
        return False

    logger.info(f"尝试启动 Shadowsocks 代理: socks5://{LOCAL_HOST}:{LOCAL_PORT}")

    try:
        _sslocal_proc = subprocess.Popen(
            [sys.executable, "-m", "shadowsocks.local", "-c", SS_CONFIG_FILE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(20):
            time.sleep(0.5)
            if is_proxy_ready():
                logger.info("Shadowsocks 代理就绪 ✓")
                return True

        logger.warning("代理启动超时")
        return False
    except Exception as e:
        logger.error(f"启动代理失败: {e}")
        return False


def get_proxy_url() -> str:
    """获取代理 URL"""
    return f"socks5://{LOCAL_HOST}:{LOCAL_PORT}"


def is_proxy_ready() -> bool:
    """检查本地代理是否可用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((LOCAL_HOST, LOCAL_PORT))
        sock.close()
        return result == 0
    except Exception:
        return False