"""圖片分析模式：處理單張圖片的卡片識別"""

import cv2
import os
from typing import List, Tuple
from .utils import CardMatcher

class ImageAnalyzer(CardMatcher):
    """圖片分析器類"""
    
    def analyze_image(self, image_path: str) -> List[Tuple[str, float]]:
        """分析單張圖片
        
        Args:
            image_path: 圖片路徑
            
        Returns:
            列表，包含 (卡片ID, 匹配分數) 的元組，按分數降序排序
        """
        if not self.reference_cards:
            return []
            
        image = cv2.imread(image_path)
        if image is None:
            return []
            
        return self.find_matches(image)
    
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
                
            # 讀取原始圖片
            query_img = cv2.imread(image_path)
            
            # 準備參考圖片列表
            ref_images = []
            for card_id, score in matches[:3]:
                card_info = self.get_card_info(card_id)
                if card_info:
                    print(f"卡片: {card_id}")
                    print(f"系列: {card_info['card_set']}")
                    print(f"編號: {card_info['card_name']}")
                    print(f"匹配分數: {score:.2f}%\n")
                    ref_images.append((card_info['img'], card_id, score))
            
            # 創建並顯示結果圖像
            result_img = self.create_display_image(query_img, ref_images)
            cv2.imshow('Matching Result', result_img)
            print("\n按任意鍵關閉結果視窗...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
        except ValueError:
            print("請輸入有效的數字！")
        except Exception as e:
            print(f"錯誤: {str(e)}")
