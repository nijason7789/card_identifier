"""相機分析模式：即時分析相機畫面中的卡片"""

import cv2
import time
import numpy as np
from typing import List, Tuple, Dict
from threading import Thread, Lock
from queue import Queue
from .utils import CardMatcher
from .cv_detector import CVCardDetector

class CameraAnalyzer(CardMatcher):
    """相機分析器類"""
    
    def __init__(self):
        super().__init__()
        # 初始化 OpenCV 檢測器
        self.detector = CVCardDetector(
            min_area=20000,        # 最小面積
            max_area=200000,       # 最大面積
            min_aspect_ratio=0.5,  # 最小寬高比
            max_aspect_ratio=0.9   # 最大寬高比
        )
        self.display_height = 480  # 顯示高度
        self.ref_width = 200      # 參考卡片寬度
        self.current_matches = []  # 當前的匹配結果
        self.matches_lock = Lock() # 用於保護匹配結果的鎖
        self.processing_queue = Queue(maxsize=1)  # 處理隊列
        self.is_running = False
    
    def matching_worker(self):
        """卡片比對工作線程"""
        while self.is_running:
            try:
                # 非阻塞式獲取最新的檢測結果
                detections_with_images = self.processing_queue.get_nowait()
                new_matches = []
                
                # 處理每個檢測結果
                for card_image, detection in detections_with_images:
                    card_matches = self.find_matches(card_image)
                    if card_matches:
                        new_matches.append((card_matches[0], detection))
                
                # 更新匹配結果
                with self.matches_lock:
                    self.current_matches = new_matches
                
                self.processing_queue.task_done()
            except:
                # 如果隊列為空，短暫休眠
                time.sleep(0.01)
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """處理單一影像幀
        
        Args:
            frame: 原始影像幀
            
        Returns:
            處理後的影像幀
        """
        # 調整主畫面大小
        h, w = frame.shape[:2]
        scale = self.display_height / h
        main_width = int(w * scale)
        frame = cv2.resize(frame, (main_width, self.display_height))
        
        # 檢測卡片
        detections = self.detector.detect(frame)
        print(f"[CameraAnalyzer] 檢測到 {len(detections)} 個卡片")
        
        # 準備檢測結果和對應的圖像
        detections_with_images = []
        for i, (bbox, conf) in enumerate(detections):
            x1, y1, x2, y2 = bbox
            # 提取卡片區域
            try:
                card_image = frame[y1:y2, x1:x2]
                if card_image.size == 0:
                    print(f"[CameraAnalyzer] 警告：卡片 {i} 區域為空")
                    continue
                detections_with_images.append((card_image, (i, bbox, conf)))
                print(f"[CameraAnalyzer] 成功提取卡片 {i} 圖像，大小：{card_image.shape}")
            except Exception as e:
                print(f"[CameraAnalyzer] 錯誤：提取卡片 {i} 圖像失敗：{str(e)}")
        
        # 如果處理隊列未滿，添加新的檢測結果
        try:
            if detections_with_images:
                self.processing_queue.put_nowait(detections_with_images)
                print(f"[CameraAnalyzer] 將 {len(detections_with_images)} 個卡片加入處理隊列")
        except:
            print("[CameraAnalyzer] 處理隊列已滿，跳過當前幀")
        
        # 在原圖上標註檢測結果
        current_matches = []
        with self.matches_lock:
            current_matches = self.current_matches.copy()
        print(f"[CameraAnalyzer] 當前有 {len(current_matches)} 個匹配結果")
        
        # 創建除錯圖像
        debug_frame = self.detector.draw_debug(frame, detections)
        
        # 繪製匹配結果
        for (card_id, score), (i, (x1, y1, x2, y2), conf) in current_matches:
            # 在框上方顯示匹配信息
            text = f'Match: {score:.1f}%'
            cv2.putText(debug_frame, text, (x1, y1-10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            print(f"[CameraAnalyzer] 卡片 {i} 匹配結果：ID={card_id}, 分數={score:.1f}%")
        
        # 如果有匹配結果，在右側顯示參考卡片
        if current_matches:
            # 最多顯示5張參考卡片
            current_matches = current_matches[:5]
            
            # 計算總寬度
            total_width = main_width + len(current_matches) * self.ref_width
            display = np.zeros((self.display_height, total_width, 3), dtype=np.uint8)
            
            # 放置主畫面
            display[:, :main_width] = debug_frame
            
            # 放置參考卡片
            x_offset = main_width
            for (card_id, score), _ in current_matches:
                card_info = self.get_card_info(card_id)
                if card_info and 'img' in card_info:
                    # 調整參考卡片大小
                    ref_img = card_info['img']
                    h, w = ref_img.shape[:2]
                    scale = self.ref_width / w
                    ref_height = int(h * scale)
                    ref_img = cv2.resize(ref_img, (self.ref_width, ref_height))
                    
                    # 添加匹配分數
                    score_text = f"{score:.1f}%"
                    cv2.putText(ref_img, score_text, 
                              (5, ref_height - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                              (0, 255, 0), 2)
                    
                    # 垂直居中放置
                    y_offset = (self.display_height - ref_height) // 2
                    display[y_offset:y_offset+ref_height, x_offset:x_offset+self.ref_width] = ref_img
                    x_offset += self.ref_width
            
            return display
        
        return debug_frame
    
    def run_camera(self, camera_id: int = 0) -> None:
        """運行相機分析模式
        
        Args:
            camera_id: 相機設備ID，預設為0（通常是內建相機）
        """
        print(f"已載入 {len(self.reference_cards)} 張參考卡片")
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"無法開啟相機 {camera_id}")
            return
            
        print("\n按 'q' 鍵退出")
        print("按 's' 鍵儲存當前畫面")
        
        # 啟動比對工作線程
        self.is_running = True
        matching_thread = Thread(target=self.matching_worker, daemon=True)
        matching_thread.start()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("無法讀取相機畫面")
                    break
                
                # 處理當前幀
                display = self.process_frame(frame)
                
                # 顯示結果
                cv2.imshow('Card Detection', display)
                
                # 檢查按鍵
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("退出相機模式")
                    break
                elif key == ord('s'):
                    # 儲存當前畫面
                    cv2.imwrite('camera_capture.jpg', frame)
                    print("已儲存當前畫面")
        finally:
            # 清理資源
            self.is_running = False
            matching_thread.join(timeout=1.0)
            cap.release()
            cv2.destroyAllWindows()
