"""卡片檢測模組：提供通用的卡片檢測功能"""

import cv2
from typing import List, Tuple
from ultralytics import YOLO

class CardDetector:
    """卡片檢測器類"""
    
    def __init__(self):
        """初始化檢測器"""
        # 載入 YOLOv8n 預訓練模型
        self.model = YOLO(model='yolov8n.pt', task='detect')
    
    def detect(self, image, conf_threshold: float = 0.0) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """檢測圖片中的卡片
        
        Args:
            image: 輸入圖片
            conf_threshold: 置信度閾值，預設為 0
            
        Returns:
            列表，每個元素為 ((x1, y1, x2, y2), confidence) 的元組
        """
        # 使用 YOLOv8 進行物件檢測
        results = self.model(image)
        
        detections = []
        # 遍歷檢測結果
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 檢查置信度
                if box.conf[0] > conf_threshold:
                    # 獲取邊界框座標
                    x1, y1, x2, y2 = [int(x) for x in box.xyxy[0]]
                    detections.append(((x1, y1, x2, y2), float(box.conf[0])))
        
        return detections
