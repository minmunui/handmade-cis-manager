import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.services.discord import discord_client
from src.utils.env import get_env

def send_test_mail(to_email:str):
    send_gmail(to_email, "CIS 테스트 메일입니다.", "메일이 성공적으로 전송되었습니다.")

async def send_invite_mail(to_email:str):
    invite_url = await discord_client.create_invite()
    invite_title = "[CIS] Discord Invitation"
    invite_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Welcome to CIS!</h2>
                <p>You have been invited to the PNU CIS Discord Server.</p>
                <p>Please click the button below to join:</p>
                <a href="{invite_url}" style="display: inline-block; padding: 10px 20px; color: #fff; background-color: #5865F2; text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Join Discord Server
                </a>
                <p style="margin-top: 20px;">
                    <strong>Verification Steps:</strong><br>
                    1. Join the server.<br>
                    2. The bot will send you a DM (or check the #verification channel).<br>
                    3. Enter your Student ID when prompted.
                </p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">
                    If the button doesn't work, copy this link: {invite_url}
                </p>
            </div>
        </body>
    </html>
    """
    send_gmail(to_email, subject=invite_title, content=invite_content, subtype="html")


def send_gmail(to_email:str, subject:str, content:str, subtype:str="plain"):
    """
    이메일을 전송합니다. 
    subtype은 html 혹은 plain이어야 합니다.
    """
    GOOGLE_EMAIL = get_env("GMAIL_USER")
    GOOGLE_APP_PASSWORD = get_env("GMAIL_PASSWORD")

    msg = MIMEMultipart()
    msg['From'] = GOOGLE_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(content, subtype))

    try:
        # 3. SMTP 서버 연결 (Gmail)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587  # TLS 포트

        # 서버 연결 및 TLS 보안 시작
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() 

        # 4. 로그인 및 전송
        server.login(GOOGLE_EMAIL, GOOGLE_APP_PASSWORD)
        server.send_message(msg)
        
        print(f"메일 전송 성공! ({to_email})")
        
    except Exception as e:
        print(f"메일 전송 실패: {e}")
        
    finally:
        # 연결 종료
        server.quit()

# --- 실행 테스트 ---
if __name__ == "__main__":
    send_gmail(
        to_email="recipient@example.com",  # 받는 사람 이메일
        subject="테스트 메일입니다",         # 제목
        content="파이썬으로 보낸 Gmail 테스트 메일 본문입니다."  # 내용
    )