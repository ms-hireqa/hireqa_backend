# app/email_service.py
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.email_username = os.getenv("EMAIL_USERNAME")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL")
        self.frontend_url = os.getenv("FRONTEND_URL")

    def generate_verification_token(self):
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)

    def create_verification_email_html(self, first_name, verification_link):
        """Create HTML email template for verification"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email - HireQA</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2c3e50; margin-bottom: 10px;">Welcome to HireQA!</h1>
                    <p style="color: #7f8c8d; font-size: 16px;">Your Gateway to Career Success</p>
                </div>
                
                <div style="background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #2c3e50; margin-bottom: 20px;">Hello {first_name}!</h2>
                    
                    <p style="margin-bottom: 20px; font-size: 16px;">
                        Thank you for signing up with HireQA! We're excited to have you join our community.
                    </p>
                    
                    <p style="margin-bottom: 20px; font-size: 16px;">
                        To complete your registration and start exploring job opportunities, please verify your email address by clicking the button below:
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}" 
                           style="background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 16px;">
                            Verify My Email
                        </a>
                    </div>
                    
                    <p style="margin-bottom: 20px; font-size: 14px; color: #7f8c8d;">
                        If the button above doesn't work, you can also copy and paste the following link into your browser:
                    </p>
                    
                    <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-size: 14px;">
                        {verification_link}
                    </p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="font-size: 14px; color: #7f8c8d; margin-bottom: 10px;">
                            <strong>Important:</strong> This verification link will expire in 24 hours for security reasons.
                        </p>
                        
                        <p style="font-size: 14px; color: #7f8c8d;">
                            If you didn't create an account with HireQA, please ignore this email.
                        </p>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 14px;">
                    <p>Best regards,<br>The HireQA Team</p>
                    <p style="margin-top: 20px;">
                        © 2025 HireQA. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def send_verification_email(self, recipient_email, first_name, verification_token):
        """Send verification email to user using Zoho SMTP with SSL"""
        try:
            # Create verification link
            verification_link = f"{self.frontend_url}/verify-email?token={verification_token}"
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = "Verify Your Email - Welcome to HireQA!"
            msg['From'] = self.from_email
            msg['To'] = recipient_email
            
            # Create HTML content
            html_content = self.create_verification_email_html(first_name, verification_link)
            html_part = MIMEText(html_content, 'html')
            
            # Create plain text version
            text_content = f"""
            Hello {first_name}!
            
            Welcome to HireQA! Thank you for signing up.
            
            Please verify your email address by clicking the link below:
            {verification_link}
            
            This link will expire in 24 hours.
            
            If you didn't create an account with HireQA, please ignore this email.
            
            Best regards,
            The HireQA Team
            """
            text_part = MIMEText(text_content, 'plain')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email using SSL (port 465) - Updated for Zoho
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)  # Enable debug for testing
                server.login(self.email_username, self.email_password)
                server.send_message(msg)
            
            return {"success": True, "message": "Verification email sent successfully"}
            
        except Exception as e:
            return {"success": False, "message": f"Failed to send email: {str(e)}"}

# Create global instance
email_service = EmailService()