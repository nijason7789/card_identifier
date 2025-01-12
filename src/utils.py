"""
共用工具模組，包含基礎的圖像處理和特徵匹配功能
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
import os

@dataclass
class MatchResult:
    """匹配結果數據類"""
    card_name: str
    score: float
    visualization: np.ndarray

class CardMatcher:
    """卡片匹配器基類"""
    
    SCORE_THRESHOLD = 0.25  # 分數閾值
    MATCH_DISPLAY_COUNT = 3  # 顯示的匹配結果數量
    
    def __init__(self, reference_dir: str = 'data/reference_cards'):
        """初始化卡片匹配器"""
        self.reference_dir = reference_dir
        self.reference_cards: Dict[str, Dict] = {}
        self.orb = cv2.ORB_create()
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self._load_reference_cards()
    
    def _load_reference_cards(self) -> None:
        """載入參考卡片圖片並提取特徵"""
        if not os.path.exists(self.reference_dir):
            raise FileNotFoundError(f"參考卡片目錄不存在: {self.reference_dir}")
            
        for filename in os.listdir(self.reference_dir):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            image_path = os.path.join(self.reference_dir, filename)
            image = cv2.imread(image_path)
            if image is None:
                print(f"無法讀取圖片: {image_path}")
                continue
                
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            keypoints, descriptors = self.orb.detectAndCompute(gray, None)
            
            if descriptors is not None:
                card_name = os.path.splitext(filename)[0]
                self.reference_cards[card_name] = {
                    'image': image,
                    'keypoints': keypoints,
                    'descriptors': descriptors
                }
        
        print(f"已載入 {len(self.reference_cards)} 張參考卡片")
    
    def _calculate_similarity(self, image: np.ndarray, reference: Dict) -> Tuple[float, np.ndarray]:
        """計算兩張圖片的相似度"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = self.orb.detectAndCompute(gray, None)
        
        if descriptors is None:
            return 0.0, image
            
        matches = self.bf.match(descriptors, reference['descriptors'])
        matches = sorted(matches, key=lambda x: x.distance)
        
        good_matches = [m for m in matches if m.distance < 45]
        similarity_score = len(good_matches) / len(matches) if matches else 0
        
        result_img = cv2.drawMatches(
            image, keypoints,
            reference['image'], reference['keypoints'],
            good_matches[:10], None,
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS
        )
        
        return similarity_score, result_img
    
    def _create_visualization(self, matches: List[MatchResult], input_image: np.ndarray) -> np.ndarray:
        """創建匹配結果的視覺化圖像"""
        if not matches:
            return input_image
            
        ref_images = []
        for match in matches[:3]:
            card_name = match.card_name
            if card_name in self.reference_cards:
                img = self.reference_cards[card_name]['image'].copy()
                
                if match.score < self.SCORE_THRESHOLD:
                    h, w = img.shape[:2]
                    center_x = w // 2
                    center_y = h // 2
                    
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    text = "undefined"
                    font_scale = 1.5
                    thickness = 3
                    
                    (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)
                    text_x = center_x - text_width // 2
                    text_y = center_y + text_height // 2
                    
                    overlay = img.copy()
                    cv2.rectangle(overlay, 
                                (text_x - 10, text_y - text_height - 10),
                                (text_x + text_width + 10, text_y + 10),
                                (0, 0, 0), -1)
                    cv2.addWeighted(overlay, 0.5, img, 0.5, 0, img)
                    cv2.putText(img, text, (text_x, text_y), font, font_scale, (0, 0, 255), thickness)
                
                ref_images.append(img)
        
        if not ref_images:
            return input_image
            
        camera_height, camera_width = input_image.shape[:2]
        main_height, main_width = ref_images[0].shape[:2]
        
        camera_display = cv2.resize(input_image, (int(camera_width * main_height / camera_height), main_height))
        side_width = main_width // 2
        
        total_width = camera_display.shape[1] + main_width + side_width
        result = np.zeros((main_height, total_width, 3), dtype=np.uint8)
        
        result[:, :camera_display.shape[1]] = camera_display
        
        x_offset = camera_display.shape[1]
        result[:, x_offset:x_offset + main_width] = ref_images[0]
        
        if len(ref_images) > 1:
            small_width = side_width // 2
            small_height = main_height // 2
            
            y_offset = (main_height - small_height) // 2
            x_start = x_offset + main_width
            
            for i, img in enumerate(ref_images[1:3]):
                small_img = cv2.resize(img, (small_width, small_height))
                x_pos = x_start + (small_width * i)
                result[y_offset:y_offset + small_height, x_pos:x_pos + small_width] = small_img
        
        return result
    
    def _find_matches(self, image: np.ndarray) -> List[MatchResult]:
        """找出圖片與所有參考卡片的匹配結果"""
        matches = []
        for card_name, card_data in self.reference_cards.items():
            score, _ = self._calculate_similarity(image, card_data)
            matches.append(MatchResult(card_name, score, None))
        
        matches.sort(key=lambda x: x.score, reverse=True)
        matches = matches[:self.MATCH_DISPLAY_COUNT]
        
        visualization = self._create_visualization(matches, image)
        for match in matches:
            match.visualization = visualization
            
        return matches
