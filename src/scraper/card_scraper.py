"""
HOCG 卡片爬蟲實現
"""

import os
import time
import logging
import shutil
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Set
from urllib.parse import urljoin

class HOCGScraper:
    """HOCG卡片爬蟲管理器"""
    
    BASE_URL = 'https://hololive-official-cardgame.com'
    API_URL = f'{BASE_URL}/cardlist/cardsearch_ex'
    
    def __init__(self, temp_dir: str = 'temp/downloads', final_dir: str = 'data/reference_cards'):
        """
        初始化爬蟲管理器
        :param temp_dir: 臨時下載目錄
        :param final_dir: 最終圖片保存目錄
        """
        self.temp_dir = temp_dir
        self.final_dir = final_dir
        self.logger = logging.getLogger(__name__)
        self.processed_urls: Set[str] = set()
        
        # 確保目錄存在
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(final_dir, exist_ok=True)
        
        # 設置 session 和 headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.session.cookies.update({
            'cardlist_view': 'img',
            'cardlist_search_sort': 'new'
        })
    
    def _download_image(self, img_url: str, card_set: str, card_number: str) -> None:
        """下載單張卡片圖片"""
        try:
            # 建立卡片集目錄
            set_dir = os.path.join(self.temp_dir, card_set)
            os.makedirs(set_dir, exist_ok=True)
            
            # 下載圖片
            response = self.session.get(urljoin(self.BASE_URL, img_url))
            response.raise_for_status()
            
            # 保存圖片
            filename = f"{card_number}.png"
            filepath = os.path.join(set_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
                
            self.logger.info(f"已下載: {card_set}/{filename}")
            
        except Exception as e:
            self.logger.error(f"下載圖片時發生錯誤 {img_url}: {str(e)}")
    
    def _get_page_cards(self, page: int) -> list:
        """獲取指定頁面的卡片列表"""
        params = {
            'keyword': '',
            'attribute[0]': 'all',
            'expansion_name': '',
            'card_kind[0]': 'all',
            'rare[0]': 'all',
            'bloom_level[0]': 'all',
            'parallel[0]': 'all',
            'view': 'img',
            'page': page
        }
        
        try:
            response = self.session.get(self.API_URL, params=params)
            response.raise_for_status()
            
            if not response.text.strip():
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.find_all('img')
            
        except Exception as e:
            self.logger.error(f"獲取第 {page} 頁卡片時發生錯誤: {str(e)}")
            return []
    
    def _move_files_to_final_dir(self) -> None:
        """將檔案從臨時目錄移動到最終目錄"""
        try:
            # 遍歷所有卡片集目錄
            for card_set in os.listdir(self.temp_dir):
                src_dir = os.path.join(self.temp_dir, card_set)
                dst_dir = os.path.join(self.final_dir, card_set)
                
                if os.path.isdir(src_dir):
                    # 確保目標目錄存在
                    os.makedirs(dst_dir, exist_ok=True)
                    
                    # 移動所有圖片
                    for filename in os.listdir(src_dir):
                        src_path = os.path.join(src_dir, filename)
                        dst_path = os.path.join(dst_dir, filename)
                        if os.path.isfile(src_path):
                            shutil.move(src_path, dst_path)
            
            # 清理臨時目錄
            shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            
        except Exception as e:
            self.logger.error(f"移動檔案時發生錯誤: {str(e)}")
            raise
    
    def download_all_cards(self) -> None:
        """下載所有卡片"""
        try:
            page = 1
            total_cards = 0
            
            while True:
                self.logger.info(f"正在處理第 {page} 頁...")
                cards = self._get_page_cards(page)
                
                if not cards:
                    break
                
                for img in cards:
                    img_src = img.get('src')
                    if img_src and img_src not in self.processed_urls:
                        self.processed_urls.add(img_src)
                        
                        # 從圖片路徑中提取卡片信息
                        # 例如：/wp-content/images/cardlist/hSD04/hSD04-001_OC.png
                        card_info = img_src.split('/')[-2:]  # ['hSD04', 'hSD04-001_OC.png']
                        card_set = card_info[0]
                        card_number = card_info[1].split('.')[0]  # 移除副檔名
                        
                        self._download_image(img_src, card_set, card_number)
                        total_cards += 1
                
                page += 1
            
            self.logger.info(f"所有卡片下載完成，共 {total_cards} 張")
            
            # 移動檔案到最終目錄
            self._move_files_to_final_dir()
            self.logger.info(f"所有卡片已移動到 {self.final_dir}")
            
        except Exception as e:
            self.logger.error(f"下載過程中發生錯誤: {str(e)}")
            raise
        finally:
            self.session.close()
