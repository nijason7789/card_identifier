"""圖片分析模式：處理單張圖片的卡片識別"""

import cv2
import os
import csv
from collections import Counter
from typing import List, Tuple
from .utils import CardMatcher
from .detector import CardDetector

class ImageAnalyzer(CardMatcher):
    """圖片分析器類"""
    
    def __init__(self):
        super().__init__()
        # 初始化卡片檢測器
        self.detector = CardDetector()
    
    def detect_cards(self, image) -> List[cv2.Mat]:
        """在圖片中偵測並分割出個別卡片
        
        Args:
            image: 輸入圖片
            
        Returns:
            列表，包含所有偵測到的卡片圖像
        """
        # 使用檢測器進行檢測
        cards, _ = self.detector.detect(image)
        return cards
    
    def analyze_image(self, image_path: str) -> List[Tuple[str, float]]:
        """分析單張圖片中的所有卡片
        
        Args:
            image_path: 圖片路徑
            
        Returns:
            列表，包含所有識別到的卡片的 (卡片ID, 匹配分數) 元組
        """
        if not self.reference_cards:
            return []
            
        image = cv2.imread(image_path)
        if image is None:
            return []
            
        # 偵測圖片中的所有卡片
        card_images = self.detect_cards(image)
        
        # 分析每張卡片
        all_matches = []
        for card_image in card_images:
            matches = self.find_matches(card_image)
            if matches:  # 只添加有成功匹配的結果
                all_matches.append(matches[0])  # 取最佳匹配
                
        return all_matches
    
    def export_to_csv(self, matches: List[Tuple[str, float]], output_path: str) -> None:
        """將卡片識別結果輸出為 CSV 檔案
        
        Args:
            matches: 卡片匹配結果列表
            output_path: CSV 檔案輸出路徑
        """
        # 統計每種卡片的數量
        card_counts = Counter(card_id for card_id, _ in matches)
        
        # 寫入 CSV 檔案
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['卡片ID', '張數'])
            for card_id, count in card_counts.items():
                writer.writerow([card_id, count])
    
    def run_analysis(self, card_picture_dir: str = 'data/card_picture') -> None:
        """運行圖片分析模式
        
        Args:
            card_picture_dir: 待分析的卡片圖片目錄
        """
        if not os.path.exists(card_picture_dir):
            print(f"圖片目錄不存在: {card_picture_dir}")
            return
            
        # 列出所有圖片
        image_files = [f for f in os.listdir(card_picture_dir)
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print("找不到任何圖片檔案！")
            return
            
        print("\n可用的圖片：")
        for i, filename in enumerate(image_files, 1):
            print(f"{i}. {filename}")
            
        try:
            file_num = int(input("\n請選擇圖片編號: "))
            if not 1 <= file_num <= len(image_files):
                print("無效的圖片編號！")
                return
                
            filename = image_files[file_num-1]
            image_path = os.path.join(card_picture_dir, filename)
            print(f"\n分析圖片: {filename}")
            
            matches = self.analyze_image(image_path)
            
            if not matches:
                print("未找到匹配的卡片")
                return
            
            # 輸出 CSV 檔案
            output_path = os.path.join(os.path.dirname(image_path), 'card_results.csv')
            self.export_to_csv(matches, output_path)
            print(f"\n分析結果已輸出至: {output_path}")
            
            # 顯示識別結果
            print("\n識別結果：")
            card_counts = Counter(card_id for card_id, _ in matches)
            for card_id, count in card_counts.items():
                card_info = self.get_card_info(card_id)
                if card_info:
                    print(f"卡片: {card_id}")
                    print(f"系列: {card_info['card_set']}")
                    print(f"編號: {card_info['card_name']}")
                    print(f"數量: {count} 張\n")
            
            # 讀取原始圖片
            query_img = cv2.imread(image_path)
            cv2.imshow('Original Image', query_img)
            print("\n按任意鍵關閉結果視窗...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
        except ValueError:
            print("請輸入有效的數字！")
        except Exception as e:
            print(f"錯誤: {str(e)}")
