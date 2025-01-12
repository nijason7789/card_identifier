"""卡片識別系統主程序"""

from .image_analyzer import ImageAnalyzer
from .camera_analyzer import CameraAnalyzer

def main():
    """主函數：提供使用者介面"""
    while True:
        print("\n=== 卡片識別系統 ===")
        print("1. 分析圖片")
        print("2. 使用攝影機")
        print("3. 退出")
        choice = input("\n請選擇功能 (1-3): ")
        
        if choice == '1':
            analyzer = ImageAnalyzer()
            analyzer.run_analysis()
        elif choice == '2':
            analyzer = CameraAnalyzer()
            print("\n開啟攝影機中... (按 'q' 退出)")
            analyzer.run_camera()
        elif choice == '3':
            print("\n感謝使用！")
            break
        else:
            print("\n無效的選擇，請重試。")

if __name__ == "__main__":
    main()
