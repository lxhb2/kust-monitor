---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 30440220489ef37857ea271f243a180c8d3c80fab9137a6fc9017188834781ad7fa6060e022018b3948fe4ff1d1850a0f95b81dfa3ea425af65b8477ab91d1bb6d1e745b3ed4
    ReservedCode2: 3045022100bd58ed3262fc934a9ebd16f3eef7d554a753a5828f501b90da80064b44f75e8902202563ab7dd90c97ce8e2c83973c6a49a89bfa0b78f8051e96459ee493b9cd9d3b
---

# 昆工研招网监控助手

这是一个用于监控昆明理工大学研究生招生通告的Python程序，可以自动检测新通告并通过飞书发送通知。支持本地运行和GitHub Actions云端运行。

## 功能特点

- 自动监控昆明理工大学研究生招生网站
- 智能检测新通告，避免重复通知
- 飞书群机器人实时推送
- 支持Markdown格式消息，带点击链接
- 错误重试机制，稳定运行
- 支持本地运行和GitHub Actions云端运行

## 两种运行方式

### 方式一：GitHub Actions 云端运行（推荐）

#### 1. 创建GitHub仓库

点击 [Use this template](https://github.com/new?template_repository=kust-monitor) 创建新仓库，或Fork本项目。

#### 2. 配置飞书Webhook

1. 在飞书中创建群机器人，获取Webhook地址
2. 进入GitHub仓库 → **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**
4. 名称填写：`FEISHU_WEBHOOK`
5. 值填写：你的飞书Webhook地址
6. 点击 **Add secret**

#### 3. 启用GitHub Actions

1. 进入仓库的 **Actions** 页面
2. 如果看到 "Workflows disabled"提示，点击 **Enable GitHub Actions**
3. 或者提交一次代码来触发Actions

#### 4. 等待运行

- 默认每15分钟检查一次
- 可以在 **Actions** 页面查看运行日志
- 发现新通告会自动发送到飞书群

#### 5. 手动触发（可选）

如需立即检查，可以进入 **Actions** → **昆工研招网监控** → **Run workflow**

---

### 方式二：本地运行

#### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/kust-monitor.git
cd kust-monitor
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置飞书Webhook

编辑 `config.json`，替换 `feishu_webhook` 为你的飞书Webhook地址：

```json
{
    "feishu_webhook": "你的Webhook地址",
    "check_interval": 300,
    "max_items": 10,
    "timeout": 10
}
```

#### 4. 运行程序

```bash
python main.py
```

#### 5. 后台运行（可选）

```bash
# Linux/Mac
nohup python main.py > monitor.log 2>&1 &

# Windows
start /b python main.py
```

## 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| feishu_webhook | 飞书Webhook地址 | 必填 |
| check_interval | 检查间隔（秒） | 300（5分钟） |
| max_items | 每次检查的文章数 | 10 |
| timeout | 请求超时时间 | 10秒 |

## GitHub Secrets 配置

在GitHub仓库的 **Settings** → **Secrets and variables** → **Actions** 中配置：

| 变量名 | 说明 | 必填 |
|--------|------|------|
| FEISHU_WEBHOOK | 飞书机器人Webhook地址 | 是 |
| CHECK_INTERVAL | 检查间隔（秒），可选 | 否 |
| MAX_ITEMS | 每次检查数量，可选 | 否 |

## 工作流程

- 每15分钟自动运行一次（可在 `.github/workflows/monitor.yml` 中修改）
- 检测昆明理工大学研究生招生网站
- 对比历史记录，发现新通告
- 发送飞书通知，包含标题、时间和链接

## 常见问题

### Q: GitHub Actions没有运行？
A: 进入仓库的 **Actions** 页面，手动启用Actions，或提交一次代码。

### Q: 收不到通知？
A:
1. 检查GitHub Secrets中的FEISHU_WEBHOOK是否正确
2. 在Actions日志中查看是否有错误
3. 测试Webhook地址是否有效

### Q: 如何修改检查频率？
A: 编辑 `.github/workflows/monitor.yml` 中的 cron 表达式：
```yaml
schedule:
  - cron: '*/15 * * * *'  # 每15分钟
  - cron: '*/30 * * * *'  # 每30分钟
  - cron: '0 * * * *'     # 每小时
```

## 项目结构

```
kust-monitor/
├── .github/
│   └── workflows/
│       └── monitor.yml      # GitHub Actions配置
├── main.py                  # 主程序
├── scraper.py               # 网页爬虫
├── notifier.py              # 飞书通知
├── config.json              # 配置文件（本地用）
├── requirements.txt         # 依赖
└── README.md                # 说明文档
```

## 许可证

MIT License
# kust-monitor
# kust-monitor
