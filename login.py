import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from time import sleep

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def send_screenshot_email(smtp_server, smtp_port, sender, password, recipient, image_path):
    """发送带截图的邮件"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"雀魂自动登录结果 - {now}"

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    body = MIMEText(f"雀魂每日自动登录完成，截图见附件。\n执行时间：{now}", "plain", "utf-8")
    msg.attach(body)

    with open(image_path, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-Disposition", "attachment", filename="result.png")
        msg.attach(img)

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"截图邮件已发送至 {recipient}")


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

for i in range(acccounts):
    email = account_args[i]
    passwd = account_args[i + acccounts]
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
        # Canvas 超时，截图发邮件后退出
        screenshot_path = f"timeout_{email.replace('@', '_at_')}.png"
        driver.save_screenshot(screenshot_path)
        try:
            send_screenshot_email(SMTP_SERVER, SMTP_PORT, SENDER_EMAIL,
                                  SENDER_PASS, RECIPIENT_EMAIL, screenshot_path)
        except Exception as e:
            print(f"发送失败: {e}")
        driver.quit()
        raise

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

    # 5. 截图 + 发邮件
    screenshot_path = f"result_{email.replace('@', '_at_')}.png"
    driver.save_screenshot(screenshot_path)
    print(f"截图已保存: {screenshot_path}")

    try:
        send_screenshot_email(SMTP_SERVER, SMTP_PORT, SENDER_EMAIL,
                              SENDER_PASS, RECIPIENT_EMAIL, screenshot_path)
    except Exception as e:
        print(f"邮件发送异常: {e}")

    driver.quit()
    print(f"Account {i+1} browser closed")

print("\n全部完成!")
