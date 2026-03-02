# -*- coding: utf-8 -*-
"""
昆明理工大学研究生招生网站爬虫模块
用于获取最新的招生通告
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KMUSTScraper:
    """昆工研招网爬虫类"""

    def __init__(self, timeout: int = 10):
        """
        初始化爬虫

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        # 昆明理工大学研究生招生主站点
        self.base_url = "https://www.kmust.edu.cn"
        # 研究生招生信息页面
        self.list_url = "https://www.kmust.edu.cn/zsjy/ssyjszs.htm"
        # 也尝试研究生院网站
        self.alt_base_url = "https://yjs.kmust.edu.cn"
        self.alt_list_url = "https://yjs.kmust.edu.cn/zs2/sszs/17.htm"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def fetch_page(self, url: str) -> Optional[str]:
        """
        获取网页内容

        Args:
            url: 网页URL

        Returns:
            网页HTML内容，失败返回None
        """
        try:
            logger.info(f"正在获取网页: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            logger.info(f"网页获取成功，状态码: {response.status_code}")
            return response.text
        except requests.exceptions.Timeout:
            logger.error(f"请求超时: {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
        return None

    def parse_announcements(self, html: str, max_items: int = 10) -> List[Dict]:
        """
        解析通告列表

        Args:
            html: 网页HTML内容
            max_items: 最大获取数量

        Returns:
            通告列表，每项包含 title, url, date
        """
        if not html:
            return []

        announcements = []
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 尝试多种常见的列表容器
            # 方法1: 查找新闻列表容器
            news_list = soup.find('div', class_='news_list')
            if not news_list:
                news_list = soup.find('ul', class_='news_list')
            if not news_list:
                news_list = soup.find('div', class_='list')
            if not news_list:
                news_list = soup.find('ul', class_='list')

            # 方法2: 查找所有链接容器
            if not news_list:
                # 查找包含招生通告的通用容器
                news_list = soup.find('div', class_='container')
                if not news_list:
                    news_list = soup.find('div', class_='main')
                    if not news_list:
                        news_list = soup

            # 查找所有文章链接
            if news_list:
                items = news_list.find_all('li', limit=max_items * 2)
            else:
                items = soup.find_all('li', limit=max_items * 2)

            for item in items[:max_items]:
                try:
                    # 查找链接
                    link = item.find('a')
                    if not link:
                        continue

                    # 获取标题
                    title = link.get('title', '')
                    if not title:
                        # 尝试获取文本内容
                        title = link.get_text(strip=True)

                    if not title:
                        continue

                    # 获取链接URL
                    href = link.get('href', '')
                    if href:
                        # 转换为绝对URL
                        full_url = urljoin(self.base_url, href)
                    else:
                        continue

                    # 获取日期（尝试多种方式）
                    date = ""
                    date_elem = item.find('span', class_='date')
                    if not date_elem:
                        date_elem = item.find('time')
                    if not date_elem:
                        # 尝试查找带有日期模式的文本
                        import re
                        text = item.get_text()
                        date_match = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)', text)
                        if date_match:
                            date = date_match.group(1)

                    if date_elem:
                        date = date_elem.get_text(strip=True)

                    announcements.append({
                        'title': title,
                        'url': full_url,
                        'date': date
                    })

                except Exception as e:
                    logger.warning(f"解析单条通告失败: {e}")
                    continue

            logger.info(f"成功解析 {len(announcements)} 条通告")

        except Exception as e:
            logger.error(f"解析网页失败: {e}")

        return announcements

    def get_latest_announcements(self, max_items: int = 10) -> List[Dict]:
        """
        获取最新通告

        Args:
            max_items: 最大获取数量

        Returns:
            通告列表
        """
        # 首先尝试主站点
        html = self.fetch_page(self.list_url)
        announcements = []

        if html:
            announcements = self.parse_announcements(html, max_items)

        # 如果主站点没有获取到，尝试备用站点
        if not announcements:
            logger.info("主站点未获取到通告，尝试备用站点...")
            html = self.fetch_page(self.alt_list_url)
            if html:
                self.base_url = self.alt_base_url
                announcements = self.parse_announcements(html, max_items)

        if not announcements:
            logger.warning("所有站点均未获取到通告")

        return announcements


def test_scraper():
    """测试爬虫"""
    scraper = KMUSTScraper()
    announcements = scraper.get_latest_announcements(5)

    print("=" * 60)
    print("昆工研招网最新通告测试")
    print("=" * 60)

    if announcements:
        for i, ann in enumerate(announcements, 1):
            print(f"\n【{i}】{ann['title']}")
            print(f"    日期: {ann['date']}")
            print(f"    链接: {ann['url']}")
    else:
        print("\n未能获取到任何通告")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_scraper()
