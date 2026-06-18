import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timezone, timedelta
from time import sleep

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def send_screenshots_email(smtp_server, smtp_port, sender, password, recipient, screenshots):
    """
    一封邮件发送所有截图
    screenshots: [(file_path, display_name, status), ...]
    status: 'success' | 'timeout' | 'error'
    """
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M")

    # 生成邮件正文摘要
    lines = [f"雀魂每日自动登录完成，共 {len(screenshots)} 个账号。", f"执行时间：{now}", ""]
    for _, name, status in screenshots:
        icon = {"success": "✅", "timeout": "⏱️", "error": "❌"}.get(status, "❓")
        lines.append(f"  {icon} {name}")
    body_text = "\n".join(lines)

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = f"雀魂自动登录结果 - {now}"

    msg.attach(MIMEText(body_text, "plain", "utf-8"))

    for path, name, status in screenshots:
        try:
            with open(path, "rb") as f:
                img = MIMEImage(f.read())
                filename = f"{name}_{status}.png"
                img.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(img)
        except Exception as e:
            print(f"附件读取失败 ({name}): {e}")

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"汇总邮件已发送至 {recipient}，共 {len(screenshots)} 张截图")


# ========== 解析参数 ==========
# 格式: EMAIL1 EMAIL2 ... PASSWD1 PASSWD2 ... SMTP_SERVER SMTP_PORT SENDER_EMAIL SENDER_PASS RECIPIENT_EMAIL
raw_args = sys.argv[1:]

# 最后 5 个参数是邮件配置
SMTP_SERVER = raw_args[-5]
SMTP_PORT = int(raw_args[-4])
SENDER_EMAIL = raw_args[-3]
SENDER_PASS = raw_args[-2]
RECIPIENT_EMAIL = raw_args[-1]

# 前面是账号密码（前一半是邮箱，后一半是对应密码）
account_args = raw_args[:-5]
acccounts = int(len(account_args) / 2)
print(f"Config {acccounts} accounts")

# 收集所有截图，最后一起发
screenshots = []

for i in range(acccounts):
    email = account_args[i]
    passwd = account_args[i + acccounts]
    account_label = email.split("@")[0]  # 用邮箱前缀当短名
    print("----------------------------")

    # 1. 启动浏览器
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
    driver.get("https://game.maj-soul.net/1/")
    print(f"Account {i+1} loading game...")

    try:
        screen = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.TAG_NAME, "canvas"))
        )
    except:
        screenshot_path = f"timeout_{email.replace('@', '_at_')}.png"
        driver.save_screenshot(screenshot_path)
        screenshots.append((screenshot_path, account_label, "timeout"))
        driver.quit()
        continue  # 跳过这个号，继续处理下一个

    sleep(60)

    # 2. 输入邮箱
    ActionChains(driver)\
        .move_to_element_with_offset(screen, 350, -135)\
        .click()\
        .perform()
    sleep(1)
    ActionChains(driver)\
        .send_keys(email)\
        .perform()
    sleep(1)

    # 3. 输入密码
    ActionChains(driver)\
        .move_to_element_with_offset(screen, 350, -50)\
        .click()\
        .perform()
    sleep(1)
    ActionChains(driver)\
        .send_keys(passwd)\
        .perform()
    sleep(1)

    # 4. 登录
    ActionChains(driver)\
        .move_to_element_with_offset(screen, 350, 60)\
        .click()\
        .perform()
    print(f"Account {i+1} entering game...")
    sleep(20)  # 等游戏加载和奖励弹窗
    print(f"Account {i+1} login completed")

    # 5. 截图
    screenshot_path = f"result_{email.replace('@', '_at_')}.png"
    driver.save_screenshot(screenshot_path)
    screenshots.append((screenshot_path, account_label, "success"))
    print(f"截图已保存: {screenshot_path}")

    driver.quit()
    print(f"Account {i+1} browser closed")

# ========== 所有号处理完，汇总发一封邮件 ==========
if screenshots:
    try:
        send_screenshots_email(SMTP_SERVER, SMTP_PORT, SENDER_EMAIL,
                               SENDER_PASS, RECIPIENT_EMAIL, screenshots)
    except Exception as e:
        print(f"邮件发送异常: {e}")
else:
    print("没有截图需要发送")

print("\n全部完成!")
