# 云服务部署方案

## 资源需求分析

| 指标 | 需求 | 说明 |
|---|---|---|
| CPU | 1 核 | 单进程 Python，几乎无负载 |
| 内存 | 512MB - 1GB | Python 运行时约 100-200MB |
| 磁盘 | 10-20GB | SQLite 数据库 + 系统 + 日志 |
| 带宽 | 1Mbps | 抓取消息量很小 |
| 系统 | Linux (Ubuntu 22.04 / Debian 12) | 最稳定 |
| 运行 | 24×7 | 需要一直在线 |

## 方案一：国内云 + 代理（推荐，最便宜）

Bot 部署在国内，通过代理访问 Telegram。

| 厂商 | 推荐机型 | 月费 | 备注 |
|---|---|---|---|
| 阿里云 ECS | ecs.e-c1m1.large (1核1G) | ~¥50/月 | 新用户有 3 年优惠 |
| 腾讯云 CVM | 轻量应用服务器 (1核1G) | ~¥40/月 | 新用户 ¥28/年 |
| 华为云 HECS | 云耀云服务器 (1核1G) | ~¥40/月 | 新用户优惠 |

**优点：** 便宜，国内访问 DeepSeek API 和微信 Webhook 延迟低
**缺点：** 需要配置代理访问 Telegram API

## 方案二：海外云（无需代理）

Bot 部署在海外，直连 Telegram。

| 厂商 | 推荐机型 | 月费 | 备注 |
|---|---|---|---|
| AWS Lightsail | 1核512MB | $3.5/月 (~¥25) | 稳定可靠 |
| Vultr | 1核1G | $6/月 (~¥43) | 日本/新加坡节点延迟低 |
| BandwagonHost | 1核512MB | ~$25/年 (~¥180/年) | CN2 GIA 线路，回国速度快 |
| DigitalOcean | 1核512MB | $4/月 (~¥29) | 送 $200 新用户额度 |

**优点：** 无需代理，直连 Telegram
**缺点：** 访问 DeepSeek API 和微信 Webhook 略慢（但都能通）

## 方案三：阿里云香港/新加坡（折中）

| 节点 | 月费 | 特点 |
|---|---|---|
| 阿里云香港轻量 | ~¥24/月 | 直连 TG，国内访问也快 |

**优点：** 既不用代理，又和国内互通良好

## 推荐方案

> **腾讯云轻量应用服务器 + 香港节点**，新用户 ¥28/年，性价比最高。

## 部署步骤（以 Ubuntu 为例）

### 1. 连接服务器

```bash
ssh root@你的服务器IP
```

### 2. 安装 Python 和依赖

```bash
apt update && apt install -y python3 python3-pip python3-venv
```

### 3. 上传项目

```bash
# 在本地执行，将项目上传到服务器
scp -r telegram_bot/ root@你的服务器IP:/opt/
```

### 4. 安装依赖

```bash
cd /opt/telegram_bot
pip install -r requirements.txt
```

### 5. 配置 .env

```bash
vim .env
# 填入配置（海外服务器不需要填 PROXY_URL）
```

### 6. 使用 systemd 保持运行

```bash
cat > /etc/systemd/system/telegram-bot.service << 'EOF'
[Unit]
Description=Telegram Bot - AI Summary
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram_bot
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable telegram-bot
systemctl start telegram-bot
```

### 7. 查看状态

```bash
systemctl status telegram-bot   # 查看运行状态
journalctl -u telegram-bot -f   # 查看实时日志
```

## 日常维护

```bash
systemctl restart telegram-bot  # 重启
systemctl stop telegram-bot     # 停止
systemctl start telegram-bot    # 启动
```

## 费用预估

| 方案 | 首年费用 |
|---|---|
| 腾讯云轻量（国内） | ~¥28（新用户） |
| 腾讯云轻量（香港） | ~¥288/年 |
| AWS Lightsail | ~$42/年 (~¥300) |
| BandwagonHost | ~$25/年 (~¥180) |