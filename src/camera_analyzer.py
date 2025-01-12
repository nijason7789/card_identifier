"""攝像頭分析模式：即時卡片識別"""

import cv2
import time
from typing import List
import numpy as np
from .utils import CardMatcher, MatchResult

class CameraAnalyzer(CardMatcher):
    """攝像頭分析器類"""
    
    DETECTION_INTERVAL = 1.0  # 檢測間隔（秒）
    
    def _draw_results(self, frame: np.ndarray, matches: List[MatchResult], 
                     time_until_next: float) -> np.ndarray:
        """在圖片上繪製識別結果"""
        display_frame = frame.copy()
        
        if not matches:
            return display_frame
            
        best_match = matches[0]
        card_name = best_match.card_name if best_match.score >= self.SCORE_THRESHOLD else 'undefined'
        cv2.putText(display_frame, f"Card: {card_name}", 
                  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        y_position = 70
        for i, match in enumerate(matches):
            score_color = (0, 255, 0) if match.score >= self.SCORE_THRESHOLD else (0, 0, 255)
            score_text = f"#{i+1} {match.card_name}: {match.score:.2f}"
            if match.score < self.SCORE_THRESHOLD:
                score_text += " (undefined)"
            
            cv2.putText(display_frame, score_text, (10, y_position),
                      cv2.FONT_HERSHEY_SIMPLEX, 1, score_color, 2)
            y_position += 40
        
        cv2.putText(display_frame, f"Next detection in: {time_until_next:.1f}s",
                  (10, y_position), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return display_frame
    
    def run_camera(self) -> None:
        """運行攝像頭分析模式"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("無法開啟攝像頭")
            return
            
        last_detection_time = time.time()
        current_matches: List[MatchResult] = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                current_time = time.time()
                
                if current_time - last_detection_time >= self.DETECTION_INTERVAL:
                    current_matches = self._find_matches(frame)
                    last_detection_time = current_time
                
                time_until_next = self.DETECTION_INTERVAL - (current_time - last_detection_time)
                display_frame = self._draw_results(frame, current_matches, time_until_next)
                
                cv2.imshow('Camera', display_frame)
                if current_matches:
                    cv2.imshow('Matching Result', current_matches[0].visualization)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()
