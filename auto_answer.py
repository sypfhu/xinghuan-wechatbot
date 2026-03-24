# auto_answer.py - 微信通话自动接听（图像识别+键鼠模拟 + 热开关支持）
import pyautogui
import cv2
import numpy as np
import time
import pygetwindow as gw
import os
import re

# ====================== 配置项（根据实际情况调整）======================
# 1. 接听按钮截图路径（必须替换为自己截取的按钮截图）
BTN_IMG_PATH = "wechat_answer_btn.png"
# 2. 识别精度（0-1，越低越容易匹配，误触率越高）
MATCH_THRESHOLD = 0.8
# ====================================================================

def is_auto_answer_enabled():
    """
    实时读取 config.py 中的 ENABLE_AUTO_ANSWER 配置项
    返回 True (开启) 或 False (关闭)
    """
    try:
        # 获取 config.py 的绝对路径 (假设与 auto_answer.py 同级)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, 'config.py')
        
        if not os.path.exists(config_path):
            # 如果找不到配置文件，默认关闭以保安全
            return False
            
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 使用正则查找 ENABLE_AUTO_ANSWER = True/False
        # 匹配模式：ENABLE_AUTO_ANSWER = True 或 ENABLE_AUTO_ANSWER = False (忽略空格)
        match = re.search(r"ENABLE_AUTO_ANSWER\s*=\s*(True|False)", content)
        
        if match:
            return match.group(1) == 'True'
        else:
            # 如果配置项不存在，默认关闭
            return False
            
    except Exception as e:
        print(f"[警告] 读取自动接听配置失败: {e}，默认关闭自动接听。")
        return False

def find_wechat_window():
    """找到并激活微信窗口"""
    try:
        # 匹配微信窗口标题（中文微信用"微信"，英文用"WeChat"）
        wechat_windows = gw.getWindowsWithTitle("微信")
        if not wechat_windows:
            wechat_windows = gw.getWindowsWithTitle("WeChat")
        if wechat_windows:
            wechat_win = wechat_windows[0]
            if not wechat_win.isActive:
                wechat_win.activate()  # 激活微信窗口
            time.sleep(0.5)  # 等待窗口激活
            return True
        return False
    except Exception as e:
        print(f"找不到微信窗口：{e}")
        return False

def click_answer_btn():
    """识别并点击接听按钮"""
    # 1. 确保微信在前台
    if not find_wechat_window():
        return False
    
    # 2. 读取按钮截图和屏幕截图
    try:
        btn_img = cv2.imread(BTN_IMG_PATH, 0)
        if btn_img is None:
            print(f"未找到接听按钮截图，请检查路径：{BTN_IMG_PATH}")
            return False
    except Exception as e:
        print(f"读取按钮截图失败：{e}")
        return False
    
    # 3. 截取当前屏幕
    screen_img = pyautogui.screenshot()
    screen_img_gray = cv2.cvtColor(np.array(screen_img), cv2.COLOR_RGB2GRAY)
    
    # 4. 模板匹配（查找按钮位置）
    res = cv2.matchTemplate(screen_img_gray, btn_img, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= MATCH_THRESHOLD)
    
    # 5. 点击按钮中心位置
    for pt in zip(*loc[::-1]):
        btn_h, btn_w = btn_img.shape
        center_x = pt[0] + btn_w // 2
        center_y = pt[1] + btn_h // 2
        # 模拟人工移动鼠标（避免被风控）
        pyautogui.moveTo(center_x, center_y, duration=0.3)
        pyautogui.click()
        print(f"[自动接听] 已模拟点击接听按钮，坐标：({center_x}, {center_y})")
        return True
    
    # 如果没有找到按钮，不打印过多日志以免刷屏，仅在调试时开启
    # print("未检测到接听按钮...") 
    return False

def monitor_call_and_answer():
    """
    循环监听通话，检测到按钮即点击
    【新增功能】支持热开关：每轮循环前检查 config.py 中的 ENABLE_AUTO_ANSWER 状态
    """
    print("自动接听监听线程已启动...")
    print("提示：请在网页编辑器底部切换开关，无需重启 Bot 即可生效。")
    
    last_status = None  # 用于记录上一次的状态，以便在状态变化时打印日志
    
    try:
        while True:
            # 1. 实时获取最新开关状态
            current_status = is_auto_answer_enabled()
            
            # 2. 如果状态发生变化，打印提示信息
            if last_status is not None and current_status != last_status:
                if current_status:
                    print("\n✅ [系统通知] 自动接听功能已【开启】，开始监测通话...")
                else:
                    print("\n⏸️ [系统通知] 自动接听功能已【关闭】，暂停自动接听监测。")
            
            last_status = current_status
            
            # 3. 只有在开关开启时才执行点击逻辑
            if current_status:
                click_answer_btn()
            else:
                # 如果关闭，可以稍微延长一点休眠时间以减少资源占用，或者保持原样
                pass
            
            # 4. 心跳检测间隔 (秒)
            # 建议 2-5 秒，太短占用CPU，太长可能漏接
            time.sleep(3) 
            
    except KeyboardInterrupt:
        print("自动接听监听已停止")
    except Exception as e:
        print(f"自动接听监听发生严重错误: {e}")