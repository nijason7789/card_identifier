"""圖片分析模式：處理單張圖片的卡片識別"""

import cv2
import os
from typing import List
from .utils import CardMatcher, MatchResult

class ImageAnalyzer(CardMatcher):
    """圖片分析器類"""
    
    def analyze_image(self, image_path: str) -> List[MatchResult]:
        """分析單張圖片"""
        if not self.reference_cards:
            return [MatchResult("No reference cards loaded", 0.0, None)]
        image = cv2.imread(image_path)
        if image is None:
            return [MatchResult("Cannot read image", 0.0, None)]
        return self._find_matches(image)
    
    def run_analysis(self, card_picture_dir: str = 'data/card_picture') -> None:
        """運行圖片分析模式"""
        os.makedirs(card_picture_dir, exist_ok=True)
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
            if 1 <= file_num <= len(image_files):
                image_path = os.path.join(card_picture_dir, image_files[file_num-1])
                matches = self.analyze_image(image_path)
                print("\n預測結果:")
                for i, match in enumerate(matches, 1):
                    status = "(undefined)" if match.score < self.SCORE_THRESHOLD else ""
                    print(f"{i}. {match.card_name}: {match.score:.1%} 相似度 {status}")
                if matches:
                    cv2.imshow('Matching Result', matches[0].visualization)
                    print("\n按任意鍵關閉結果視窗...")
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
            else:
                print("無效的圖片編號！")
        except ValueError:
            print("請輸入有效的數字！")
        except Exception as e:
            print(f"錯誤: {str(e)}")
