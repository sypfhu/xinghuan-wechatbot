import subprocess
import sys

# 依赖列表（根据项目实际需要补充，比如wxautox4_wechatbot、requests等）
REQUIREMENTS = [
    "wxautox4_wechatbot",
    "requests",
    "pytz",
    "datetime",
    "opencv-python",
    "beautifulsoup4",
    # 其他项目需要的包...
]

def install_dependencies():
    print("正在检查并安装依赖环境...")
    # 使用pip批量安装依赖（国内镜像加速）
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "-U",
        *REQUIREMENTS,
        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"
    ])
    print("依赖安装完成！")

if __name__ == "__main__":
    # 先安装依赖，再启动主程序
    try:
        install_dependencies()
        # 启动你的主程序（替换为实际的入口文件，比如bot.py）
        subprocess.check_call([sys.executable, "bot.py"])
    except Exception as e:
        print(f"启动失败：{e}")
        input("按回车键退出...")