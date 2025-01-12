# HOCG Card Identifier

這是一個使用 ORB (Oriented FAST and Rotated BRIEF) 特徵匹配算法實現的卡牌辨識系統，可以即時識別 HOCG 卡牌並顯示最相似的三張卡片。系統包含自動化爬蟲功能，可以從官方網站獲取最新的卡片圖片作為參考資料。

## 功能特點

- 支援圖片分析和攝像頭即時辨識兩種模式
- 顯示最相似的三張卡片及其相似度分數
- 統一的視覺化界面，清晰展示匹配結果
- 模組化設計，代碼結構清晰
- 高效的圖像處理和特徵匹配
- 自動化爬蟲更新參考卡片資料庫

## 環境需求

- Python 3.8+
- OpenCV
- NumPy
- BeautifulSoup4
- Requests

## 安裝步驟

1. 安裝所需套件：
```bash
pip install -r requirements.txt
```

2. 準備參考卡片：
   - 方法一：手動準備
     - 將參考卡片圖片放入 `data/reference_cards` 資料夾
     - 支援的圖片格式：PNG, JPG, JPEG
   - 方法二：自動爬取
     - 運行爬蟲程式自動下載最新卡片
     - 詳見下方爬蟲使用說明

3. 準備待識別圖片（可選）：
   - 將要辨識的圖片放入 `data/card_picture` 資料夾

## 使用方式

### 卡片識別

1. 運行程式：
```bash
python -m src.main
```

2. 選擇辨識模式：
   - 1: 分析圖片 - 從 `data/card_picture` 選擇圖片進行辨識
   - 2: 使用攝影機 - 開啟攝像頭進行即時辨識
   - 3: 退出程式

3. 查看辨識結果：
   - 顯示前三個最相似的卡片及其詳細資訊
   - 視覺化結果會顯示：
     - 左側：輸入圖片/攝像頭畫面
     - 右側：匹配到的參考卡片（按相似度排序）
   - 每張參考卡片上方顯示：
     - 卡片ID
     - 匹配分數

### 爬蟲使用

1. 運行爬蟲：
```python
from src.scraper import HOCGScraper

scraper = HOCGScraper()
scraper.run()  # 開始爬取卡片
```

2. 爬蟲功能：
   - 自動從官方網站下載最新卡片圖片
   - 支援斷點續傳
   - 自動分類整理到對應資料夾
   - 避免重複下載

## 專案結構

```
src/
├── __init__.py      # 套件初始化
├── main.py          # 主程式入口
├── utils.py         # 共用工具和基礎類
├── image_analyzer.py # 圖片分析模式
├── camera_analyzer.py# 攝像頭分析模式
└── scraper/         # 爬蟲模組
    ├── __init__.py
    └── card_scraper.py

data/
├── reference_cards/ # 參考卡片圖片
└── card_picture/   # 待分析的圖片
```

## 技術實現

### 核心類別

- `ImageProcessor`: 基礎圖像處理類，提供通用的圖像處理功能
  - 圖像縮放
  - 結果視覺化
  - 統一的顯示格式

- `CardMatcher`: 繼承自 `ImageProcessor`，實現特徵匹配核心功能
  - ORB 特徵提取
  - 特徵點匹配
  - 匹配分數計算

- `ImageAnalyzer`: 處理單張圖片的分析
  - 檔案選擇介面
  - 批次圖片處理
  - 結果展示

- `CameraAnalyzer`: 處理攝像頭即時分析
  - 即時影像擷取
  - 週期性檢測
  - 動態結果更新

- `HOCGScraper`: 卡片爬蟲類
  - 自動下載卡片圖片
  - 支援分頁爬取
  - 錯誤重試機制
  - 檔案管理功能

### 匹配參數

- 最小匹配點數：20（確保匹配的可靠性）
- 分數閾值：45（過濾低質量匹配）
- 檢測間隔：1秒（攝像頭模式）

## 開發說明

- 使用 ORB 算法進行特徵提取和匹配
- 採用模組化設計，便於維護和擴展
- 統一的圖像處理流程，確保顯示效果一致
- 參數可在 `utils.py` 中根據需求調整
- 爬蟲模組支援自定義下載設置和錯誤處理
