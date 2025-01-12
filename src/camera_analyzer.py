"""
攝像頭分析模式：即時分析攝像頭影像
"""

import cv2
import time
from typing import List, Tuple
import numpy as np
from .utils import CardMatcher

class CameraAnalyzer(CardMatcher):
    """攝像頭分析器類"""
    
    DETECTION_INTERVAL = 1.0  # 檢測間隔（秒）
    display_height = 400
    
    def _draw_results(self, frame: np.ndarray, matches: List[Tuple[str, float]], 
                     time_until_next: float) -> np.ndarray:
        """在圖片上繪製識別結果
        
        Args:
            frame: 原始影像幀
            matches: 匹配結果列表
            time_until_next: 距離下次檢測的時間
            
        Returns:
            處理後的影像幀
        """
        if not matches:
            return self.resize_image(frame)
            
        # 準備參考圖片列表
        ref_images = []
        for card_id, score in matches[:3]:
            card_info = self.get_card_info(card_id)
            if card_info:
                ref_images.append((card_info['img'], card_id, score))
        
        # 創建顯示圖像
        result_img = self.create_display_image(frame, ref_images)
        
        # 添加倒數計時
        cv2.putText(result_img,
                    f"Next detection in: {time_until_next:.1f}s",
                    (10, self.display_height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2)
        
        return result_img
    
    def resize_image(self, frame: np.ndarray) -> np.ndarray:
        """調整圖片大小
        
        Args:
            frame: 原始影像幀
            
        Returns:
            調整後的影像幀
        """
        h, w = frame.shape[:2]
        scale = self.display_height / h
        return cv2.resize(frame, (int(w * scale), self.display_height))
    
    def create_display_image(self, frame: np.ndarray, ref_images: List[Tuple[np.ndarray, str, float]]) -> np.ndarray:
        """創建顯示圖像
        
        Args:
            frame: 原始影像幀
            ref_images: 參考圖片列表
            
        Returns:
            顯示圖像
        """
        # 調整原始圖片大小
        frame = self.resize_image(frame)
        
        # 調整參考圖片大小
        ref_displays = []
        for ref_img, card_id, score in ref_images:
            ref_display = self.resize_image(ref_img)
            
            # 在參考圖片上添加文字
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
        all_displays = [frame] + ref_displays
        return cv2.hconcat(all_displays)
    
    def run_camera(self, camera_id: int = 0) -> None:
        """運行攝像頭分析模式
        
        Args:
            camera_id: 攝像頭設備ID
        """
        print(f"已載入 {len(self.reference_cards)} 張參考卡片")
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"無法開啟攝像頭 {camera_id}")
            return
            
        print("按 'q' 鍵退出")
        
        last_detection_time = 0
        matches: List[Tuple[str, float]] = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("無法讀取攝像頭影像")
                break
                
            current_time = time.time()
            time_since_last = current_time - last_detection_time
            
            # 定期進行檢測
            if time_since_last >= self.DETECTION_INTERVAL:
                matches = self.find_matches(frame)
                last_detection_time = current_time
            
            # 繪製結果
            time_until_next = max(0, self.DETECTION_INTERVAL - time_since_last)
            display_frame = self._draw_results(frame, matches, time_until_next)
            
            cv2.imshow('Card Detection', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
