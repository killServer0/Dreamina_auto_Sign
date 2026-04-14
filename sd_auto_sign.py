# /// script
# dependencies = [
#   "requests",
#   "playwright",
# ]
# ///
import asyncio
import re
import random
import string
import os
import requests
import socket
import winsound
import datetime
from playwright.async_api import async_playwright
import requests.packages.urllib3.util.connection as urllib3_cn
def allowed_gai_family():
    return socket.AF_INET
urllib3_cn.allowed_gai_family = allowed_gai_family

# 改成你自己的地址
DOMAIN = "@你的地址"
WORKER_BASE_URL = "https://你设置的自定义域" 
TARGET_URL = "https://dreamina.capcut.com/ai-tool/home/"
session = requests.Session()
session.trust_env = False
adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=5)
session.mount("https://", adapter)
session.mount("http://", adapter)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE_PATH = os.path.join(BASE_DIR, "save.txt")

def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def get_random_birthday():
    year = str(random.randint(1985, 2003))
    month_map = {
        "January": 31, "March": 31, "April": 30, "May": 31, "June": 30,
        "July": 31, "August": 31, "September": 30, "October": 31, "November": 30, "December": 31
    }
    month_name = random.choice(list(month_map.keys()))
    day = str(random.randint(1, month_map[month_name]))
    return {"year": year, "month": month_name, "day": day}

async def save_account(email, pwd):
    reg_date = datetime.datetime.now().strftime("%Y-%m-%d")
    with open(SAVE_FILE_PATH, "a+", encoding="utf-8") as f:
        f.write(f"{email}----{pwd}----{reg_date}\n")
        
def get_existing_emails():
    emails = set()
    if not os.path.exists(SAVE_FILE_PATH):
        return emails
    with open(SAVE_FILE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"^\s*(\S+@\S+)", line)
            if match:
                emails.add(match.group(1).strip())
    return emails

async def fetch_verify_code(email):
    await asyncio.sleep(2) 
    print(f"开始轮询{email}。")
    for i in range(80):
        try:
            resp = session.get(
                f"{WORKER_BASE_URL}/get-code", 
                params={"email": email}, 
                timeout=1.5
            )
            if resp.status_code == 200:
                data = resp.json()
                code = data.get("code")
                if code and code.upper() not in ["GEOPOD", "CAPCUT", "SHA256"]:
                    print(f"获取验证码:{code.upper()}")
                    return code.upper()
        except Exception as e:
            pass
        await asyncio.sleep(1)
    print("轮询超时，未获取验证码。")
    return None

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(30000)
        existing_emails = get_existing_emails()
        while True:
            random_prefix = ''.join(random.choices(string.digits, k=6))
            email_address = f"{random_prefix}{DOMAIN}"
            if email_address not in existing_emails:
                break
        random_password = generate_random_password(10)
        birthday = get_random_birthday()
        print(f"准备注册:{email_address} | 密码:{random_password}")

        await page.goto(TARGET_URL)
        await page.click("text=/Sign in|登入/i")
        await page.wait_for_selector("text=/Continue with email|使用電子郵件繼續/i")
        await page.click("text=email")
        await page.wait_for_selector("text=/Sign up|註冊/i")
        await page.click("text=/Sign up|註冊/i")
        await page.get_by_placeholder(re.compile(r"email|電子郵件", re.I)).fill(email_address)
        await page.get_by_placeholder(re.compile(r"password|密碼", re.I)).fill(random_password)
        continue_btn = page.locator("button").filter(has_text=re.compile(r"Continue|Next|繼續", re.I))
        for i in range(8):
            await continue_btn.click(force=True)
            try:
                await page.wait_for_selector("input:visible", timeout=3000)
                break
            except:
                print(f"等待验证码界面，重试{i+1}。")
                await asyncio.sleep(1)
        verify_code = await fetch_verify_code(email_address)
        
        if verify_code:
            first_input = page.locator("input:visible").first
            await first_input.click()
            await page.keyboard.type(verify_code, delay=120)
        else:
            try:
                winsound.MessageBeep()
            except ImportError:
                print("\a")
            verify_code = input("自动获取失败，手动输入:").strip()
            first_input = page.locator("input:visible").first
            await first_input.click()
            await page.keyboard.type(verify_code, delay=120)

        try:
            await page.wait_for_selector("text=/When’s your birthday?/i", timeout=15000)
            await page.get_by_placeholder("Year").fill(birthday["year"])
            month_box = page.get_by_role("combobox").filter(has_text=re.compile(r"Month", re.I)).first
            await month_box.click()
            await asyncio.sleep(0.5)
            await page.get_by_role("option", name=birthday["month"]).click()
            day_box = page.get_by_role("combobox").filter(has_text=re.compile(r"Day", re.I)).first
            await day_box.click()
            await asyncio.sleep(0.5)
            await page.get_by_role("option", name=birthday["day"], exact=True).click()
            next_btn = page.get_by_role("button", name=re.compile(r"Next|Continue|下一步", re.I)).last
            await next_btn.click()
            await save_account(email_address, random_password)
            print(f"{email_address}注册成功。")  
        except Exception as e:
            print(f"步骤失败:{e}")

        print("\n流程结束，窗口保持。")
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n脚本关闭。")
        
