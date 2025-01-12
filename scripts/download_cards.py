"""
下載 HOCG 卡片的執行腳本
"""

import os
import sys
import logging

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.scraper import HOCGScraper

def setup_logging():
    """配置日誌"""
    # 確保 logs 目錄存在
    os.makedirs('temp/logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('temp/logs/download_cards.log')
        ]
    )

def main():
    """主函數"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("開始下載卡片...")
        scraper = HOCGScraper(
            temp_dir='temp/downloads',
            final_dir='data/reference_cards'
        )
        scraper.download_all_cards()
        logger.info("卡片下載完成！")
        
    except Exception as e:
        logger.error(f"下載過程中發生錯誤: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
