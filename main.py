import os
import sys
from pathlib import Path
import chardet
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox
import logging
from datetime import datetime
import shutil
import tempfile
import time

# 確定專案目錄
if getattr(sys, 'frozen', False):
    # 如果程式被打包
    PROJECT_DIR = os.path.dirname(sys.executable)
else:
    # 如果程式以腳本運行
    PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# 建立必要的目錄
LOG_DIR = os.path.join(PROJECT_DIR, 'logs')
DESKTOP_DIR = os.path.join(Path.home(), "Desktop")
MODIFIED_DIR = os.path.join(DESKTOP_DIR, 'modified')

# 確保目錄存在
def ensure_dir(directory):
    # 如果目錄不存在則建立
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f'建立目錄: {directory}')

ensure_dir(LOG_DIR)
ensure_dir(MODIFIED_DIR)

# 設定日誌
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(LOG_DIR, f'app_log_{current_time}.txt')
logging.basicConfig(filename=log_file, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8')

# 檢測檔案編碼
def detect_encoding(file_path):
    try:
        import chardet
    except ImportError as e:
        logging.error(f"ImportError: {e}")
        return None

    # 讀取檔案的原始資料
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    logging.debug(f"檔案 {file_path} 的編碼檢測結果：{result['encoding']} (信心度：{result['confidence']})")
    return result['encoding']

# 讀取檔案
def read_file(file_path):
    detected_encoding = detect_encoding(file_path)
    try:
        with open(file_path, 'r', encoding=detected_encoding) as file:
            content = file.read()
        logging.debug(f'成功讀取 {len(content)} 個字元，使用 {detected_encoding} 編碼')
        return content
    except Exception as e:
        logging.error(f'讀取檔案 {file_path} 時發生錯誤：{e}')
        return None
    
# 將內容轉換為 Big5 編碼
def convert_to_big5(content):
    try:
        big5_content = content.encode('big5', errors='replace')
        logging.debug(f'轉換為 Big5 編碼，長度：{len(big5_content)} 字節')
        return big5_content
    except Exception as e:
        logging.error(f'轉換為 Big5 編碼時發生錯誤：{e}')
        return None

# 寫入 Big5 編碼檔案
def write_big5_file(file_path, content):
    try:
        with open(file_path, 'wb') as file:
            file.write(content)
        logging.debug(f'寫入 {len(content)} 字節到 {file_path}')
    except Exception as e:
        logging.error(f'寫入檔案 {file_path} 時發生錯誤：{e}')

# 驗證 Big5 編碼檔案
def verify_big5_file(file_path):
    try:
        with open(file_path, 'rb') as file:
            content = file.read().decode('big5')
        logging.debug(f"成功以 Big5 編碼讀取檔案 {file_path}")
        logging.debug(f"檔案內容預覽：\n{content[:100]}...")  # 只顯示前100個字元
    except UnicodeDecodeError:
        logging.error(f"無法以 Big5 編碼讀取檔案 {file_path}")
    except Exception as e:
        logging.error(f"讀取檔案 {file_path} 時發生錯誤：{e}")

def process_fled_file(parts):
    result = ['I']
    result.append(parts[1].ljust(10)[:10])
    result.append(parts[2].ljust(50)[:50])
    result.append(parts[3].ljust(15)[:15])
    result.append(parts[4].ljust(3)[:3])
    result.append(parts[5].rjust(8)[:8])
    result.append(parts[6].rjust(1)[:1])
    result.append(parts[7].rjust(8)[:8])
    result.append(parts[8].rjust(8)[:8] if len(parts) > 8 else ' ' * 8)
    result.append(' ' * 7)
    return '!'.join(result)

def process_immi_file(parts):
    result = ['I' if parts[0] == 'I' else 'U']
    result.append(parts[1].ljust(10)[:10])
    result.append(' ' * 50)
    result.append(parts[3].ljust(15)[:15])
    result.append(parts[4].ljust(3)[:3])
    result.append(parts[5].rjust(8)[:8])
    result.append(parts[6].rjust(1)[:1])
    result.append(parts[7].rjust(8)[:8])
    result.append(parts[8].rjust(1)[:1])
    result.append(' ' * 4)
    return '!'.join(result)

def process_punish_file(parts):
    result = ['U']
    result.append(parts[1].ljust(10)[:10])
    result.append(' ' * 50)
    result.append(parts[3].ljust(15)[:15])
    result.append(parts[4].ljust(3)[:3])
    result.append(parts[5].rjust(8)[:8])
    result.append(parts[6].rjust(1)[:1])
    result.append(parts[7].rjust(8)[:8])
    result.append(parts[8].rjust(8)[:8])
    result.append(' ' * 7)
    return '!'.join(result)

# 處理特殊檔案內容
def process_special_file(content, file_type):
    lines = content.splitlines()

    # 移除第一行和最後一行（根據特定條件）
    if len(lines) > 2:
        if lines[0].startswith('000002!') or lines[0].startswith('084852!'):
            lines = lines[1:]  # 移除第一行
        if lines[-1].startswith('@@'):
            lines = lines[:-1]  # 移除最後一行
    
    # 處理每行，填充或裁剪至所需的長度
    processed_lines = []
    for line in lines:
        # 處理每一行，忽略空行
        if not line.strip():
            continue

        parts = line.split('!')

        try:
             # 確保每一行都是固定長度
            if file_type == 'Fled':
                processed_line = process_fled_file(parts)
                required_length = 120
            elif file_type == 'Immi':
                processed_line = process_immi_file(parts)
                required_length = 110
            elif file_type == 'Punish':
                processed_line = process_punish_file(parts)
                required_length = 120
            else:
                logging.error(f'未知的檔案類型：{file_type}')
                return None
            
            if len(processed_lines) < required_length:
                processed_line = processed_line.ljust(required_length)
            else:
                processed_line = processed_line[:required_length]
        
            processed_lines.append(processed_line)
        except Exception as e:
            logging.error(f"處理行時發生錯誤： {line}")
            logging.error(f"錯誤詳情： {str(e)}")
            continue

    # 重新組合行並將 LF 換行符號改為 CRLF
    processed_content = '\r\n'.join(processed_lines)

    logging.debug(f'處理 {file_type} 檔案: 移除了首尾行，保留了列對齊，確保末尾有一個換行符號')
    return processed_content

# 處理檔案
def process_file(file_path):
    content = read_file(file_path)
    if content is None:
        return None

    logging.debug(f'原始內容預覽：\n{content[:100]}...')

    file_name = os.path.basename(file_path)
    file_type = None
    for prefix in ['Punish-', 'Fled-', 'Immi-']:
        if prefix in file_name:
            file_type = prefix.rstrip('-')
            break

    # 根據檔名判斷檔案類型並處理
    if file_type:
        if file_type == 'Immi':
            content = content.replace('|', '!')
            
        content = process_special_file(content, file_type)
        if content is None:
            logging.error(f'處理 {file_type} 檔案時發生錯誤')
            return None
        logging.debug(f'處理後的 {file_type} 檔案內容預覽： \n{content[:100]}...')
        logging.debug(f'處理後的 {file_type} 檔案最後幾行： \n{content[-100:]}')
    else:
        logging.warning(f'未知的檔案類型：{file_name}')

    big5_content = convert_to_big5(content)
    if big5_content is None:
        return None

    output_path = os.path.join(MODIFIED_DIR, file_name)
    write_big5_file(output_path, big5_content)

    logging.debug("驗證輸出檔案：")
    verify_big5_file(output_path)

    return output_path

# 選擇檔案
def select_files():
    logging.debug("進入 select_files 函數")
    root = tk.Tk()
    root.withdraw()
    files = filedialog.askopenfilenames(title="選擇檔案", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    logging.debug(f"選擇的檔案: {files}")
    return files

# 主程式
def main():
    logging.debug("進入 main 函數")
    ensure_dir(MODIFIED_DIR)  # 確保 modified 資料夾存在
    parser = argparse.ArgumentParser(description='將檔案轉換為 Big5 編碼。')
    parser.add_argument('files', nargs='*', help='要轉換的輸入檔案')
    args = parser.parse_args()

    logging.debug(f"命令列參數: {args}")

    if not args.files:
        logging.debug("沒有提供檔案，呼叫 select_files")
        args.files = select_files()

    if not args.files:
        logging.debug("沒有選擇任何檔案，程式結束")
        messagebox.showinfo("提示", "沒有選擇任何檔案，程式結束。")
        return

    success_count = 0
    fail_count = 0
    for file in args.files:
        if not os.path.exists(file):
            logging.error(f'錯誤：檔案 {file} 不存在')
            fail_count += 1
            continue

        output_file = process_file(file)
        if output_file:
            logging.info(f'成功將 {file} 轉換為 {output_file}')
            success_count += 1
        else:
            logging.error(f'轉換 {file} 失敗')
            fail_count += 1
        logging.debug('-' * 50)

    messagebox.showinfo("處理結果", f"處理完成！\n成功轉換: {success_count} 個檔案\n失敗: {fail_count} 個檔案\n\n轉換後的檔案位於：\n{MODIFIED_DIR}")

if __name__ == "__main__":
    try:
        logging.debug("程式開始執行")
        main()
    except Exception as e:
        logging.exception("程式執行時發生錯誤")
        messagebox.showerror("錯誤", f"程式執行時發生錯誤：\n{str(e)}")
    finally:
        logging.debug("程式結束執行")