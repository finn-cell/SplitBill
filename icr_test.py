import subprocess
import re
from datetime import datetime, timedelta
import pytz

def get_time_offset_from_remote(remote_ip: str) -> float:
    """
    使用 w32tm 從遠端電腦抓取時間差（單位：秒）
    """
    try:
        cmd = ['w32tm', '/stripchart', f'/computer:{remote_ip}', '/samples:1', '/dataonly']
        output = subprocess.check_output(cmd, universal_newlines=True)
        match = re.search(r'([+-]?\d+\.\d+)s', output)
        if match:
            return float(match.group(1))  # 秒
        else:
            raise ValueError("無法從 w32tm 結果中解析時間差")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"w32tm 執行失敗: {e.output}")

def get_uk_time_with_remote_offset(remote_ip: str) -> str:
    # Step 1: 抓遠端時間差
    offset_seconds = get_time_offset_from_remote(remote_ip)
    
    # Step 2: 用 UTC 時間校正
    corrected_utc = datetime.utcnow() + timedelta(seconds=offset_seconds)

    # Step 3: 轉 UK 時區
    uk_timezone = pytz.timezone("Europe/London")
    uk_time = corrected_utc.replace(tzinfo=pytz.utc).astimezone(uk_timezone)

    return uk_time.strftime("%Y-%m-%d %H:%M:%S")

# ==== Example ====
remote_ip = "172.23.113.31"
try:
    uk_time = get_uk_time_with_remote_offset(remote_ip)
    print("UK Time:", uk_time, "END")
except Exception as e:
    print("Error:", e)
