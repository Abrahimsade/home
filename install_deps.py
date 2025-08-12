import os
import subprocess
import sys

def install_package(package):
    try:
        __import__(package)
        print(f"DEBUG: {package} is already installed.")
    except ImportError:
        print(f"DEBUG: Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"DEBUG: {package} installed successfully.")

if __name__ == "__main__":
    install_package("pyTelegramBotAPI")
    print("DEBUG: All dependencies installed.")