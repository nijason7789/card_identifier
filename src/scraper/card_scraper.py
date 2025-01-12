"""
HOCG 卡片爬蟲實現
"""

import os
import logging
import shutil
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup
from typing import List, Set
from urllib.parse import urljoin

@dataclass
class CardInfo:
    """卡片信息數據類"""
    set_name: str
    card_number: str
    image_url: str

class HOCGScraper:
    """HOCG卡片爬蟲管理器"""
    
    BASE_URL = 'https://hololive-official-cardgame.com'
    API_URL = f'{BASE_URL}/cardlist/cardsearch_ex'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                     ' (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    COOKIES = {
        'cardlist_view': 'img',
        'cardlist_search_sort': 'new'
    }
    
    def __init__(self, temp_dir: str = 'temp/downloads', final_dir: str = 'data/reference_cards'):
        """初始化爬蟲管理器
        
        Args:
            temp_dir: 臨時下載目錄
            final_dir: 最終圖片保存目錄
        """
        self.temp_dir = temp_dir
        self.final_dir = final_dir
        self.logger = logging.getLogger(__name__)
        self.processed_urls: Set[str] = set()
        
        # 確保目錄存在
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(final_dir, exist_ok=True)
        
        # 初始化 session
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.session.cookies.update(self.COOKIES)
    
    def _extract_card_info(self, img_src: str) -> CardInfo:
        """從圖片URL提取卡片信息
        
        Args:
            img_src: 圖片URL
            
        Returns:
            CardInfo對象
        """
        parts = img_src.split('/')[-2:]  # ['hSD04', 'hSD04-001_OC.png']
        return CardInfo(
            set_name=parts[0],
            card_number=parts[1].split('.')[0],
            image_url=img_src
        )
    
    def _download_card(self, card: CardInfo) -> bool:
        """下載單張卡片
        
        Args:
            card: 卡片信息
            
        Returns:
            下載是否成功
        """
        try:
            # 建立卡片集目錄
            set_dir = os.path.join(self.temp_dir, card.set_name)
            os.makedirs(set_dir, exist_ok=True)
            
            # 下載圖片
            url = urljoin(self.BASE_URL, card.image_url)
            response = self.session.get(url)
            response.raise_for_status()
            
            # 保存圖片
            filename = f"{card.card_number}.png"
            filepath = os.path.join(set_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
                
            self.logger.info(f"已下載: {card.set_name}/{filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"下載卡片時發生錯誤 {card.image_url}: {str(e)}")
            return False
    
    def _get_page_cards(self, page: int) -> List[BeautifulSoup]:
        """獲取指定頁面的卡片列表
        
        Args:
            page: 頁碼
            
        Returns:
            卡片圖片元素列表
        """
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
    
    def _move_to_final_dir(self) -> None:
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
    
    def run(self) -> None:
        """執行爬蟲任務"""
        try:
            self.logger.info("開始下載卡片...")
            page = 1
            total_cards = 0
            success_count = 0
            
            while True:
                self.logger.info(f"正在處理第 {page} 頁...")
                cards = self._get_page_cards(page)
                
                if not cards:
                    break
                
                for img in cards:
                    img_src = img.get('src')
                    if not img_src or img_src in self.processed_urls:
                        continue
                        
                    self.processed_urls.add(img_src)
                    card_info = self._extract_card_info(img_src)
                    
                    if self._download_card(card_info):
                        success_count += 1
                    total_cards += 1
                
                page += 1
            
            self.logger.info(f"下載完成，共 {total_cards} 張卡片，成功 {success_count} 張")
            
            # 移動檔案到最終目錄
            self._move_to_final_dir()
            self.logger.info(f"所有卡片已移動到 {self.final_dir}")
            
        except Exception as e:
            self.logger.error(f"爬蟲過程中發生錯誤: {str(e)}")
            raise
        finally:
            self.session.close()
