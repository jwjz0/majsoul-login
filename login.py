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
    一封邮件发送所有截图（luxury HTML 模板）
    screenshots: [(file_path, display_name, status), ...]
    status: 'success' | 'timeout' | 'error'
    """
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz)
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%H:%M")

    success_count = sum(1 for _, _, s in screenshots if s == "success")
    pending_count = len(screenshots) - success_count

    # 构建账号卡片 HTML
    cards_html = ""
    for idx, (path, name, status) in enumerate(screenshots):
        if status == "success":
            tag_color = "#c9a84c"
            tag_bg = "#c9a84c"
            tag_text = "#1a1a1a"
            desc = "Signed in successfully"
            line_color = "#c9a84c"
        else:
            tag_color = "rgba(255,255,255,0.55)"
            tag_bg = "rgba(255,255,255,0.12)"
            tag_text = tag_color
            desc = "Canvas did not load"
            line_color = "rgba(255,255,255,0.2)"

        status_label = "Success" if status == "success" else "Timeout"
        cid = f"screenshot-{idx}"

        cards_html += f"""\
                    <tr>
                      <td style="padding:0 48px 28px;background:#1a1a1a;">
                        <table width="100%" cellpadding="0" cellspacing="0" style="background:rgba(255,255,255,0.03);">
                          <tr>
                            <td width="56%" style="padding:16px 0 16px 16px;vertical-align:top;">
                              <div style="position:relative;overflow:hidden;">
                                <img src="cid:{cid}" alt="Screenshot" style="display:block;width:100%;height:auto;border:1px solid rgba(255,255,255,0.08);">
                                <span style="position:absolute;top:10px;left:10px;padding:4px 10px;background:{tag_bg};font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:8px;color:{tag_text};letter-spacing:0.15em;text-transform:uppercase;font-weight:600;">{status_label}</span>
                              </div>
                            </td>
                            <td style="padding:16px 22px 16px 18px;vertical-align:top;">
                              <div style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:14px;color:#ffffff;font-weight:500;margin-bottom:8px;">{name}</div>
                              <div style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:12px;color:rgba(255,255,255,0.45);margin-bottom:10px;">{desc}</div>
                              <div>
                                <span style="display:inline-block;width:16px;height:1px;background:{line_color};vertical-align:middle;margin-right:6px;"></span>
                                <span style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:10px;color:rgba(255,255,255,0.25);letter-spacing:0.05em;">Screenshot attached</span>
                              </div>
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>"""

    html = f"""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;1,400&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
    </head>
    <body style="margin:0;padding:0;background:#eae7e2;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#eae7e2;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;">
        <tr>
          <td style="padding:48px 48px 0;background:#1a1a1a;">
            <div style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:10px;letter-spacing:0.35em;color:#c9a84c;text-transform:uppercase;">
              Daily Check-in
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding:12px 48px 40px;background:#1a1a1a;">
            <div style="font-family:'Playfair Display',Georgia,serif;font-size:36px;font-weight:400;color:#ffffff;line-height:1.15;">
              Mahjong<br><span style="font-style:italic;">Soul</span>
            </div>
            <div style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:12px;color:rgba(255,255,255,0.45);letter-spacing:0.06em;margin-top:14px;">
              {date_str} &nbsp; at &nbsp; {time_str} CST
            </div>
            <div style="margin-top:24px;">
              <span style="display:inline-block;width:36px;height:1px;background:#c9a84c;"></span>
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 48px 32px;background:#1a1a1a;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="33%">
                  <div style="font-family:'Playfair Display',Georgia,serif;font-size:36px;font-weight:400;color:#ffffff;line-height:1;">{len(screenshots)}</div>
                  <div style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:9px;letter-spacing:0.2em;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-top:6px;">Accounts</div>
                </td>
                <td width="33%">
                  <div style="font-family:'Playfair Display',Georgia,serif;font-size:36px;font-weight:400;color:#c9a84c;line-height:1;">{success_count}</div>
                  <div style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:9px;letter-spacing:0.2em;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-top:6px;">Success</div>
                </td>
                <td width="33%">
                  <div style="font-family:'Playfair Display',Georgia,serif;font-size:36px;font-weight:400;color:#ffffff;line-height:1;">{pending_count}</div>
                  <div style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:9px;letter-spacing:0.2em;color:rgba(255,255,255,0.4);text-transform:uppercase;margin-top:6px;">Pending</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:14px 48px;background:#1a1a1a;">
            <div style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:9px;letter-spacing:0.2em;color:rgba(255,255,255,0.35);text-transform:uppercase;">
              Results
            </div>
          </td>
        </tr>
        {cards_html}
        <tr>
          <td style="padding:40px 48px 48px;background:#1a1a1a;">
            <div style="border-top:1px solid rgba(255,255,255,0.1);margin-bottom:24px;"></div>
            <div style="font-family:'DM Sans',Helvetica,Arial,sans-serif;font-size:11px;color:rgba(255,255,255,0.3);letter-spacing:0.04em;">
              Automated by GitHub Actions<br>
              <span style="color:rgba(255,255,255,0.15);">This is an automated message. Please do not reply.</span>
            </div>
          </td>
        </tr>
      </table>
    </td></tr>
    </table>
    </body>
    </html>"""

    msg = MIMEMultipart("related")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = f"Mahjong Soul - Daily Check-in - {date_str}"

    # HTML 正文
    msg.attach(MIMEText(html, "html", "utf-8"))

    # 截图内联嵌入（cid 引用）
    for idx, (path, name, status) in enumerate(screenshots):
        try:
            with open(path, "rb") as f:
                img = MIMEImage(f.read())
                cid = f"screenshot-{idx}"
                img.add_header("Content-ID", f"<{cid}>")
                img.add_header("Content-Disposition", "inline", filename=f"{name}_{status}.png")
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
    options.add_argument("--window-size=1280,800")
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
    sleep(30)  # 等游戏加载和奖励弹窗
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
