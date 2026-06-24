# 故障排查记录

## 问题：腾讯云服务器部署后 Bot 无法响应 Telegram 消息

### 现象
- Bot 进程正常运行，日志显示"使用代理"、"Bot 正在启动"
- RSS 抓取正常（通过代理访问 t.me）
- 在 Telegram 上发送 `/summary` 等命令，Bot 无任何响应
- 日志中没有任何收到消息的记录

### 环境
- 服务器：腾讯云 CVM（国内节点），Ubuntu 22.04
- 代理：mihomo (clash-meta) 混合端口 7897，通过机场订阅获取节点
- 项目路径：`/opt/telegram_bot`
- python-telegram-bot 版本：22.8

---

## 根因分析

### 问题 1：代理未运行
服务器没有代理客户端，`PROXY_URL=http://127.0.0.1:7897` 指向的端口无进程监听。

**解决**：安装 mihomo 并配置机场订阅，监听 7897 端口。

### 问题 2：read_timeout 太短（30 秒）
`main.py` 中 `HTTPXRequest` 的 `read_timeout=30` 小于 Telegram 长轮询的超时（50 秒），导致长连接被提前断开。

**解决**：改为 `read_timeout=60`。

### 问题 3：SOCKS5 代理 + 长轮询不兼容
使用 `socks5://` 代理时，`python-telegram-bot` 的长轮询无法正常工作，`curl` 直接测试却可以。原因可能是 `httpx` 的 SOCKS5 实现与长连接存在兼容性问题。

**解决**：改用 HTTP 代理 `http://127.0.0.1:7897`（mihomo 混合端口同时支持 HTTP 和 SOCKS5）。

### 🔴 核心问题：getUpdates 有独立的超时配置

`python-telegram-bot` 内部维护了**两个独立的 HTTPXRequest 实例**：

| 实例 | 用途 | 默认 connect_timeout |
|---|---|---|
| `self._request[1]` | 普通 API 调用（getMe、sendMessage 等） | 自定义值 |
| `self._request[0]` | getUpdates 长轮询 | **5 秒（硬编码默认值）** |

源码 `_bot.py` 第 738 行：
```python
request = self._request[0] if endpoint == "getUpdates" else self._request[1]
```

`main.py` 中只设置了普通请求的 `HTTPXRequest`，但 `getUpdates` 使用的是 `ApplicationBuilder` 内部构建的另一个请求对象，其 `connect_timeout` 默认为 5 秒。

通过代理连接 Telegram API 时，建立连接需要的时间可能超过 5 秒，导致 `getUpdates` 持续超时，Bot 永远收不到消息。

**关键日志证据**（DEBUG 模式）：
```
# 普通请求（getMe）— 使用自定义的 connect_timeout=30
httpcore.connection:connect_tcp.started host='127.0.0.1' port=7897 ... timeout=30

# getUpdates — 使用默认的 connect_timeout=5 ！
httpcore.connection:connect_tcp.started host='api.telegram.org' port=443 ... timeout=5.0
httpcore.connection:connect_tcp.failed exception=ConnectTimeout(TimeoutError())
```

**解决**：显式创建 `get_updates_request` 并设置足够的超时：
```python
request = HTTPXRequest(proxy=PROXY_URL, connect_timeout=30, read_timeout=60, write_timeout=30)
get_updates_request = HTTPXRequest(proxy=PROXY_URL, connect_timeout=30, read_timeout=60, write_timeout=30)

builder = Application.builder().token(BOT_TOKEN)
builder = builder.request(request)
builder = builder.get_updates_request(get_updates_request)  # 关键！
```

---

## 最终配置

### 服务器
| 组件 | 配置 | 说明 |
|---|---|---|
| mihomo | `/etc/mihomo/config.yaml` | 机场订阅，混合端口 7897，systemd 自启 |
| Bot | `/opt/telegram_bot/.env` | `PROXY_URL=http://127.0.0.1:7897` |
| Bot | `/opt/telegram_bot/main.py` | `connect_timeout=30, read_timeout=60` + 独立 `get_updates_request` |

### 代理架构
```
Telegram API ← mihomo(7897) ← Bot(main.py)
                   ↑
            机场订阅（自动选择节点）
```

---

## 教训

1. **国内服务器部署 TG Bot 必须配置代理**，且代理需要作为系统服务持久运行
2. **优先使用 HTTP 代理而非 SOCKS5**，兼容性更好
3. **`python-telegram-bot` 的 getUpdates 有独立超时配置**，容易被忽略。如果自定义了 `request`，也必须同时配置 `get_updates_request`
4. 排查长轮询问题时，开启 DEBUG 日志（`LOG_LEVEL=DEBUG`）可以快速定位超时参数