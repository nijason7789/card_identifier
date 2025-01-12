# HOCG Card Identifier

這是一個使用 ORB (Oriented FAST and Rotated BRIEF) 特徵匹配算法實現的卡牌辨識系統，可以即時識別 HOCG 卡牌並顯示最相似的三張卡片。

## 功能特點

- 支援圖片分析和攝像頭即時辨識兩種模式
- 顯示最相似的三張卡片及其相似度分數
- 當相似度低於閾值時顯示 "undefined"
- 視覺化匹配結果，包含特徵點連線
- 模組化設計，代碼結構清晰

## 環境需求

- Python 3.8+
- OpenCV
- NumPy

## 安裝步驟

1. 安裝所需套件：
```bash
pip install -r requirements.txt
```

2. 準備參考卡片：
   - 將參考卡片圖片放入 `data/reference_cards` 資料夾
   - 支援的圖片格式：PNG, JPG, JPEG

3. 準備待識別圖片（可選）：
   - 將要辨識的圖片放入 `data/card_picture` 資料夾

## 使用方式

1. 運行程式：
```bash
python -m src.main
```

2. 選擇辨識模式：
   - 1: 分析圖片 - 從 `data/card_picture` 選擇圖片進行辨識
   - 2: 使用攝影機 - 開啟攝像頭進行即時辨識
   - 3: 退出程式

3. 查看辨識結果：
   - 顯示前三個最相似的卡片名稱及相似度分數
   - 相似度低於 25% 的卡片會標記為 "undefined"
   - 視覺化結果會顯示：
     - 左側：輸入圖片/攝像頭畫面
     - 中間：最佳匹配卡片（原始大小）
     - 右側：第二和第三匹配卡片（縮小顯示）

## 專案結構

```
src/
├── __init__.py      # 套件初始化
├── main.py          # 主程式入口
├── utils.py         # 共用工具和基礎類
├── image_analyzer.py # 圖片分析模式
└── camera_analyzer.py# 攝像頭分析模式

data/
├── reference_cards/ # 參考卡片圖片
└── card_picture/   # 待分析的圖片
```

## 開發說明

- `CardMatcher`: 基礎類，實現特徵匹配核心功能
- `ImageAnalyzer`: 處理單張圖片的分析
- `CameraAnalyzer`: 處理攝像頭即時分析
- 特徵匹配使用 ORB 算法，具有旋轉不變性和尺度不變性
- 匹配分數閾值可在 `utils.py` 中調整
