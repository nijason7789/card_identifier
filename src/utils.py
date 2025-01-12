"""
工具類模組
"""

import os
import cv2
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional

class ImageProcessor:
    """基礎圖像處理類"""
    
    def __init__(self, display_height: int = 400):
        """初始化圖像處理器
        
        Args:
            display_height: 顯示圖片的統一高度
        """
        self.display_height = display_height
    
    def resize_image(self, image: np.ndarray) -> np.ndarray:
        """調整圖片大小到統一高度
        
        Args:
            image: 輸入圖片
            
        Returns:
            調整後的圖片
        """
        h, w = image.shape[:2]
        scale = self.display_height / h
        return cv2.resize(image, (int(w * scale), self.display_height))
    
    def create_display_image(self, 
                           query_img: np.ndarray,
                           ref_images: List[Tuple[np.ndarray, str, float]]) -> np.ndarray:
        """創建顯示圖像
        
        Args:
            query_img: 查詢圖片
            ref_images: 參考圖片列表，每個元素為 (圖片, 卡片ID, 分數) 的元組
            
        Returns:
            合併後的顯示圖像
        """
        # 調整查詢圖片大小
        query_display = self.resize_image(query_img)
        
        # 準備參考卡片顯示
        ref_displays = []
        for ref_img, card_id, score in ref_images[:3]:  # 只顯示前三個結果
            # 調整參考卡片大小
            ref_display = self.resize_image(ref_img)
            
            # 添加文字標註
            cv2.putText(ref_display,
                       f"{card_id}",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                       (0, 255, 0), 2)
            cv2.putText(ref_display,
                       f"Score: {score:.2f}%",
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1,
                       (0, 255, 0), 2)
            
            ref_displays.append(ref_display)
        
        # 水平拼接所有圖片
        all_displays = [query_display] + ref_displays
        return cv2.hconcat(all_displays)

class CardMatcher(ImageProcessor):
    """卡片匹配器類，用於識別和匹配卡片圖像"""
    
    def __init__(self, 
                 reference_dir: str = 'data/reference_cards',
                 min_match_count: int = 20,
                 score_threshold: int = 45):
        """初始化卡片匹配器
        
        Args:
            reference_dir: 參考卡片目錄路徑
            min_match_count: 最小匹配點數量
            score_threshold: 最小匹配分數閾值
        """
        super().__init__()
        self.reference_dir = reference_dir
        self.min_match_count = min_match_count
        self.score_threshold = score_threshold
        self.reference_cards: Dict[str, Dict] = {}
        
        # 初始化特徵檢測器和匹配器
        self.feature_detector = cv2.ORB_create()
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # 載入參考卡片
        self._load_reference_cards()
    
    def _extract_features(self, image: np.ndarray) -> Tuple[Optional[List], Optional[np.ndarray]]:
        """提取圖像特徵
        
        Args:
            image: 輸入圖像
            
        Returns:
            特徵點和描述符的元組
        """
        try:
            return self.feature_detector.detectAndCompute(image, None)
        except Exception as e:
            logging.error(f"特徵提取失敗: {str(e)}")
            return None, None
    
    def _calculate_match_score(self, matches: List, min_count: int) -> float:
        """計算匹配分數
        
        Args:
            matches: 匹配結果列表
            min_count: 最小匹配點數量
            
        Returns:
            匹配分數 (0-100)
        """
        if len(matches) < min_count:
            return 0.0
            
        # 計算前N個最佳匹配的平均距離
        avg_distance = sum(m.distance for m in matches[:min_count]) / min_count
        return max(0, 100 - avg_distance)
    
    def _load_single_card(self, card_path: str, card_set: str, card_name: str) -> None:
        """載入單張參考卡片"""
        try:
            img = cv2.imread(card_path)
            if img is None:
                logging.error(f"無法讀取卡片圖片: {card_path}")
                return
                
            # 提取特徵
            keypoints, descriptors = self._extract_features(img)
            if descriptors is None:
                logging.error(f"無法計算卡片特徵: {card_path}")
                return
                
            # 儲存卡片資訊
            card_id = f"{card_set}/{card_name}"
            self.reference_cards[card_id] = {
                'img': img,
                'keypoints': keypoints,
                'descriptors': descriptors,
                'card_set': card_set,
                'card_name': card_name
            }
            logging.info(f"已載入卡片: {card_id}")
            
        except Exception as e:
            logging.error(f"處理卡片時發生錯誤 {card_path}: {str(e)}")

    def _load_reference_cards(self) -> None:
        """載入所有參考卡片"""
        if not os.path.exists(self.reference_dir):
            logging.error(f"參考卡片目錄不存在: {self.reference_dir}")
            return
            
        for card_set in os.listdir(self.reference_dir):
            set_dir = os.path.join(self.reference_dir, card_set)
            if not os.path.isdir(set_dir):
                continue
                
            for card_file in os.listdir(set_dir):
                if not card_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue
                    
                card_path = os.path.join(set_dir, card_file)
                card_name = os.path.splitext(card_file)[0]
                self._load_single_card(card_path, card_set, card_name)
        
        logging.info(f"共載入 {len(self.reference_cards)} 張參考卡片")
    
    def find_matches(self, query_img: np.ndarray, min_match_count: Optional[int] = None) -> List[Tuple[str, float]]:
        """尋找匹配的卡片
        
        Args:
            query_img: 查詢圖片
            min_match_count: 最小匹配點數量，如果為None則使用初始化時設定的值
            
        Returns:
            列表，包含 (卡片ID, 匹配分數) 的元組，按分數降序排序
        """
        min_match_count = min_match_count or self.min_match_count
        
        # 提取查詢圖片特徵
        query_keypoints, query_descriptors = self._extract_features(query_img)
        if query_descriptors is None:
            return []
        
        matches_list = []
        
        # 與所有參考卡片比對
        for card_id, card_info in self.reference_cards.items():
            # 特徵匹配
            matches = self.matcher.match(query_descriptors, card_info['descriptors'])
            matches = sorted(matches, key=lambda x: x.distance)
            
            # 計算匹配分數
            score = self._calculate_match_score(matches, min_match_count)
            if score > self.score_threshold:
                matches_list.append((card_id, score))
        
        # 按分數降序排序
        return sorted(matches_list, key=lambda x: x[1], reverse=True)
    
    def get_card_info(self, card_id: str) -> Optional[Dict]:
        """獲取卡片資訊"""
        return self.reference_cards.get(card_id)
