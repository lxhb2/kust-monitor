# -*- coding: utf-8 -*-
"""
飞书通知模块
用于发送群机器人消息
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeishuNotifier:
    """飞书群机器人通知类"""

    def __init__(self, webhook_url: str):
        """
        初始化通知器

        Args:
            webhook_url: 飞书机器人Webhook地址
        """
        self.webhook_url = webhook_url
        self.session = requests.Session()

    def send_text(self, content: str) -> bool:
        """
        发送文本消息

        Args:
            content: 消息内容

        Returns:
            是否发送成功
        """
        payload = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        return self._send(payload)

    def send_rich_text(self, title: str, announcements: List[Dict]) -> bool:
        """
        发送富文本消息

        Args:
            title: 消息标题
            announcements: 通告列表

        Returns:
            是否发送成功
        """
        # 构建富文本内容
        content = []

        # 添加标题
        content.append([
            {"tag": "text", "text": f"🔔 {title}\n\n"}
        ])

        # 添加通告列表
        for i, ann in enumerate(announcements, 1):
            title_text = ann.get('title', '未知标题')
            url = ann.get('url', '')
            date = ann.get('date', '未知日期')

            # 每条通告的结构
            item = [
                {"tag": "text", "text": f"{i}. "},
                {"tag": "a", "text": title_text, "href": url},
                {"tag": "text", "text": f"\n   📅 {date}\n\n"}
            ]
            content.append(item)

        # 添加监控时间
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        content.append([
            {"tag": "text", "text": f"---\n🦾 监控时间: {current_time}"}
        ])

        payload = {
            "msg_type": "rich_text",
            "content": {
                "title": title,
                "elements": content
            }
        }

        return self._send(payload)

    def send_post(self, title: str, announcements: List[Dict]) -> bool:
        """
        发送帖子消息（飞书富文本）

        Args:
            title: 消息标题
            announcements: 通告列表

        Returns:
            是否发送成功
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 构建消息内容
        content = []

        # 标题部分
        content.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"## 🔔 {title}"
            }
        })

        # 分隔线
        content.append({
            "tag": "hr"
        })

        # 通告列表
        for i, ann in enumerate(announcements, 1):
            title_text = ann.get('title', '未知标题')
            url = ann.get('url', '')
            date = ann.get('date', '未知日期')

            content.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{i}. {title_text}**\n📅 发布时间: {date}\n[查看详情]({url})"
                }
            })

        # 底部信息
        content.append({
            "tag": "hr"
        })
        content.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"🦾 *昆明理工大学研招监控 • {current_time}*"
            }
        })

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"🔔 {title}"
                    },
                    "template": "blue"
                },
                "elements": content
            }
        }

        return self._send(payload)

    def _send(self, payload: Dict) -> bool:
        """
        发送消息到飞书

        Args:
            payload: 消息载荷

        Returns:
            是否发送成功
        """
        try:
            logger.info(f"正在发送飞书消息...")
            response = self.session.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            result = response.json()

            if result.get("code") is None or result.get("code") == 0:
                logger.info("消息发送成功")
                return True
            else:
                logger.error(f"消息发送失败: {result.get('msg', '未知错误')}")
                return False

        except requests.exceptions.Timeout:
            logger.error("消息发送超时")
        except requests.exceptions.RequestException as e:
            logger.error(f"消息发送失败: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"响应解析失败: {e}")

        return False

    def send_new_announcement_notification(self, announcements: List[Dict]) -> int:
        """
        发送新通告通知

        Args:
            announcements: 通告列表，每项包含 title, url, date

        Returns:
            发送成功的数量
        """
        if not announcements:
            logger.info("没有新通告需要通知")
            return 0

        title = "昆工研招网新通告"

        # 尝试发送卡片消息（更美观）
        if self.send_post(title, announcements):
            return 1

        # 如果卡片消息失败，尝试富文本
        if self.send_rich_text(title, announcements):
            return 1

        # 最后尝试纯文本
        return self._send_text_notification(announcements)

    def _send_text_notification(self, announcements: List[Dict]) -> int:
        """
        发送纯文本通知（备选方案）

        Args:
            announcements: 通告列表

        Returns:
            发送成功的数量
        """
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        text = f"🔔 昆工研招网新通告\n\n"

        for i, ann in enumerate(announcements, 1):
            title = ann.get('title', '未知标题')
            url = ann.get('url', '')
            date = ann.get('date', '未知日期')
            text += f"{i}. {title}\n   📅 {date}\n   🔗 {url}\n\n"

        text += f"---\n🦾 监控时间: {current_time}"

        if self.send_text(text):
            return 1

        return 0


def test_notifier():
    """测试通知功能"""
    # 这里使用一个假的Webhook URL进行测试
    notifier = FeishuNotifier("https://open.feishu.cn/open-apis/bot/v2/hook/TEST")

    print("=" * 60)
    print("飞书通知测试")
    print("=" * 60)

    # 测试消息
    test_announcements = [
        {
            'title': '2026年硕士研究生招生复试通知',
            'url': 'https://www.kmust.edu.cn/info/1234.html',
            'date': '2026-03-01'
        },
        {
            'title': '关于公布2026年研究生初试成绩的通知',
            'url': 'https://www.kmust.edu.cn/info/1235.html',
            'date': '2026-02-28'
        }
    ]

    print("\n发送测试消息...")
    result = notifier.send_new_announcement_notification(test_announcements)
    print(f"发送结果: {'成功' if result > 0 else '失败'}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_notifier()
