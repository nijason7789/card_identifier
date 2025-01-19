"""OpenCV 卡片檢測器：使用傳統電腦視覺方法進行矩形檢測"""

import cv2
import numpy as np
from typing import List, Tuple

class CVCardDetector:
    """使用 OpenCV 的卡片檢測器"""
    
    def __init__(self, min_area: float = 2000, max_area: float = 200000,
                 min_aspect_ratio: float = 0.5, max_aspect_ratio: float = 0.9):
        """初始化檢測器
        
        Args:
            min_area: 最小矩形面積，用於過濾小物體
            max_area: 最大矩形面積，用於過濾大物體
            min_aspect_ratio: 最小寬高比（寬/高）
            max_aspect_ratio: 最大寬高比（寬/高）
        """
        self.min_area = min_area
        self.max_area = max_area
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """預處理圖像
        
        Args:
            image: 輸入圖像
            
        Returns:
            處理後的二值圖像
        """
        # 轉換為灰度圖
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 高斯模糊，減少噪聲
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        
        # 自適應二值化
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 形態學操作：閉運算，連接斷開的邊緣
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return morph
    
    def find_rectangles(self, binary: np.ndarray) -> List[np.ndarray]:
        """在二值圖像中查找矩形
        
        Args:
            binary: 二值圖像
            
        Returns:
            矩形輪廓列表
        """
        # 查找輪廓
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        print(f"[CVCardDetector] 找到 {len(contours)} 個輪廓")
        
        rectangles = []
        for i, cnt in enumerate(contours):
            # 計算面積
            area = cv2.contourArea(cnt)
            print(f"[CVCardDetector] 輪廓 {i} 面積: {area}")
            
            if area < self.min_area or area > self.max_area:
                print(f"[CVCardDetector] 輪廓 {i} 面積不符合要求 ({self.min_area} < area < {self.max_area})")
                continue
            
            # 獲取最小外接矩形
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            
            # 計算寬高比
            width = np.linalg.norm(box[0] - box[1])
            height = np.linalg.norm(box[1] - box[2])
            aspect_ratio = min(width, height) / max(width, height)
            print(f"[CVCardDetector] 輪廓 {i} 寬高比: {aspect_ratio:.3f}")
            
            # 根據寬高比過濾
            if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                print(f"[CVCardDetector] 輪廓 {i} 寬高比不符合要求 ({self.min_aspect_ratio} < ratio < {self.max_aspect_ratio})")
                continue
            
            print(f"[CVCardDetector] 輪廓 {i} 符合要求，加入矩形列表")
            rectangles.append(box)
        
        return rectangles
    
    def convert_to_xyxy(self, box: np.ndarray) -> Tuple[int, int, int, int]:
        """將旋轉矩形轉換為軸對齊的邊界框
        
        Args:
            box: 旋轉矩形的四個頂點
            
        Returns:
            (x1, y1, x2, y2) 格式的邊界框
        """
        x_coords = box[:, 0]
        y_coords = box[:, 1]
        return (int(np.min(x_coords)), int(np.min(y_coords)),
                int(np.max(x_coords)), int(np.max(y_coords)))
    
    def detect(self, image: np.ndarray, conf_threshold: float = 0.0) -> List[Tuple[Tuple[int, int, int, int], float]]:
        """檢測圖片中的卡片
        
        Args:
            image: 輸入圖片
            conf_threshold: 置信度閾值（為了與 YOLO 檢測器接口一致，但在這裡不使用）
            
        Returns:
            列表，每個元素為 ((x1, y1, x2, y2), confidence) 的元組
            注意：由於是傳統方法，confidence 統一設為 1.0
        """
        # 預處理圖像
        binary = self.preprocess_image(image)
        
        # 查找矩形
        rectangles = self.find_rectangles(binary)
        print(f"[CVCardDetector] 找到 {len(rectangles)} 個可能的矩形")
        
        # 轉換格式
        detections = []
        for box in rectangles:
            bbox = self.convert_to_xyxy(box)
            # 使用固定的置信度 1.0
            detections.append((bbox, 1.0))
            print(f"[CVCardDetector] 檢測到矩形：{bbox}")
        
        return detections
    
    def draw_debug(self, image: np.ndarray, detections: List[Tuple[Tuple[int, int, int, int], float]]) -> np.ndarray:
        """在圖像上繪製除錯信息
        
        Args:
            image: 原始圖像
            detections: 檢測結果列表
            
        Returns:
            帶有標註的圖像
        """
        debug_image = image.copy()
        
        # 繪製檢測結果
        for i, (bbox, conf) in enumerate(detections):
            x1, y1, x2, y2 = bbox
            
            # 畫矩形框
            cv2.rectangle(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 添加標籤
            label = f'Card {i+1}'
            cv2.putText(debug_image, label, (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return debug_image
