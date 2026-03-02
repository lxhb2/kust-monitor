# -*- coding: utf-8 -*-
"""
昆明理工大学研究生招生监控主程序
定时检查网站并发送飞书通知
支持本地运行和GitHub Actions云端运行
"""

import json
import os
import time
import logging
import signal
import sys
from datetime import datetime
from typing import List, Set
from pathlib import Path

import scraper
import notifier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class Config:
    """配置管理类"""

    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载配置文件，优先使用环境变量"""
        default_config = {
            "feishu_webhook": "",
            "check_interval": 300,
            "max_items": 10,
            "timeout": 10
        }

        # 优先从环境变量读取（GitHub Actions使用）
        if os.getenv('FEISHU_WEBHOOK'):
            default_config['feishu_webhook'] = os.getenv('FEISHU_WEBHOOK')
            logger.info("从环境变量读取到飞书Webhook")

        # 尝试从配置文件读取
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 如果环境变量没有设置，则使用配置文件
                    if not default_config['feishu_webhook']:
                        default_config.update(loaded_config)
                        logger.info(f"配置文件加载成功: {self.config_file}")
                    else:
                        # 环境变量优先级更高
                        logger.info("使用环境变量的Webhook配置")
            except Exception as e:
                logger.error(f"配置文件加载失败: {e}")

        return default_config

    def get(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)


class HistoryManager:
    """历史记录管理类"""

    def __init__(self, history_file: str = 'history.json'):
        self.history_file = history_file
        self.urls: Set[str] = self._load_history()

    def _load_history(self) -> Set[str]:
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    urls = set(data.get('urls', []))
                    logger.info(f"历史记录加载成功，共 {len(urls)} 条")
                    return urls
            except Exception as e:
                logger.error(f"历史记录加载失败: {e}")

        logger.info("未找到历史记录，将创建新文件")
        return set()

    def save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'urls': list(self.urls),
                    'last_update': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"历史记录保存成功，共 {len(self.urls)} 条")
        except Exception as e:
            logger.error(f"历史记录保存失败: {e}")

    def add_url(self, url: str):
        """添加URL到历史记录"""
        self.urls.add(url)

    def is_new(self, url: str) -> bool:
        """检查URL是否为新URL"""
        return url not in self.urls


class Monitor:
    """监控主类"""

    def __init__(self, config: Config):
        self.config = config
        self.history = HistoryManager()
        self.scraper = scraper.KMUSTScraper(timeout=config.get('timeout', 10))
        self.notifier = None
        self.running = True

        # 初始化飞书通知器
        webhook = config.get('feishu_webhook', '')
        if webhook:
            self.notifier = notifier.FeishuNotifier(webhook)
        else:
            logger.warning("未配置飞书Webhook，请在 config.json 中配置 feishu_webhook")

    def check_and_notify(self):
        """检查并通知"""
        logger.info("=" * 50)
        logger.info("开始检查昆工研招网...")

        try:
            # 获取最新通告
            announcements = self.scraper.get_latest_announcements(
                max_items=self.config.get('max_items', 10)
            )

            if not announcements:
                logger.info("未获取到任何通告")
                return

            # 筛选新通告
            new_announcements = []
            for ann in announcements:
                url = ann.get('url', '')
                if url and self.history.is_new(url):
                    new_announcements.append(ann)
                    self.history.add_url(url)
                    logger.info(f"发现新通告: {ann.get('title', '')}")
                else:
                    logger.debug(f"已知通告: {ann.get('title', '')}")

            # 发送通知
            if new_announcements:
                logger.info(f"发现 {len(new_announcements)} 条新通告，准备发送通知...")

                if self.notifier:
                    success_count = self.notifier.send_new_announcement_notification(new_announcements)
                    if success_count > 0:
                        logger.info(f"通知发送成功")
                    else:
                        logger.error(f"通知发送失败")
                else:
                    logger.warning("未配置通知器，仅记录新通告")

                # 保存历史记录
                self.history.save_history()
            else:
                logger.info("没有新通告")

        except Exception as e:
            logger.error(f"检查过程中发生错误: {e}")

    def run(self):
        """运行监控"""
        logger.info("=" * 60)
        logger.info("昆工研招网监控助手启动")
        logger.info(f"检查间隔: {self.config.get('check_interval', 300)} 秒")
        logger.info(f"每次检查数量: {self.config.get('max_items', 10)}")
        logger.info("=" * 60)

        # 设置信号处理
        def signal_handler(sig, frame):
            logger.info("收到停止信号，正在退出...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 首次运行
        self.check_and_notify()

        # 定时检查
        interval = self.config.get('check_interval', 300)
        while self.running:
            time.sleep(interval)
            if self.running:
                self.check_and_notify()


def main():
    """主函数"""
    # 判断是否在GitHub Actions环境中
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'

    if not is_github_actions:
        # 本地运行：创建配置文件（如果不存在）
        if not os.path.exists('config.json'):
            default_config = {
                "feishu_webhook": "YOUR_FEISHU_WEBHOOK_URL_HERE",
                "check_interval": 300,
                "max_items": 10,
                "timeout": 10
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            logger.info("已创建配置文件 config.json，请编辑并配置飞书Webhook")

    # 加载配置
    config = Config()

    # 检查Webhook配置
    webhook = config.get('feishu_webhook', '')
    if not webhook or webhook == "YOUR_FEISHU_WEBHOOK_URL_HERE":
        if is_github_actions:
            logger.error("=" * 60)
            logger.error("错误: 请在GitHub Secrets中配置FEISHU_WEBHOOK！")
            logger.error("设置方法：仓库 -> Settings -> Secrets and variables -> Actions -> New repository secret")
            logger.error("名称: FEISHU_WEBHOOK")
            logger.error("值: 你的飞书Webhook地址")
            logger.error("=" * 60)
            sys.exit(1)
        else:
            logger.error("=" * 60)
            logger.error("错误: 请先配置飞书Webhook地址！")
            logger.error("请编辑 config.json 文件，设置 feishu_webhook 为您的飞书机器人Webhook地址")
            logger.error("获取方法：飞书群 -> 设置 -> 群机器人 -> 添加机器人 -> 复制Webhook地址")
            logger.error("=" * 60)
            sys.exit(1)

    # 运行监控
    monitor = Monitor(config)
    monitor.run()


if __name__ == "__main__":
    main()
