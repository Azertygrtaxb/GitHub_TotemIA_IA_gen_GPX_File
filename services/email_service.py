import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, GMAIL_CREDENTIALS
import logging

class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        if not SENDER_EMAIL:
            raise ValueError("SENDER_EMAIL environment variable is not set")
        self.sender_email = SENDER_EMAIL
        if not GMAIL_CREDENTIALS:
            raise ValueError("GMAIL_CREDENTIALS environment variable is not set")
        self.credentials = GMAIL_CREDENTIALS

    def send_gpx_email(self, recipient_email, gpx_content, route_description, preferences):
        """Send GPX file via email with personalized content."""
        try:
            msg = MIMEMultipart()
            msg['Subject'] = "Votre Parcours Personnalisé - Sport Outdoor"
            msg['From'] = self.sender_email
            msg['To'] = recipient_email

            # Generate a simple discount code
            discount_code = "SPORT340"
            discount_percentage = "10"

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #40E0D0;">Votre parcours est prêt !</h1>

                    <p>Voici votre parcours personnalisé de {preferences['distance']}km en {preferences['activity_type']}.</p>

                    <div style="background-color: #f8f8f8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3>🎉 Bonne nouvelle !</h3>
                        <p>Pour vous remercier de votre intérêt, nous vous offrons un code de réduction de {discount_percentage}%</p>

                        <h3>Code promo : {discount_code}</h3>
                        <p>sur votre prochain achat en magasin !</p>
                    </div>

                    <div style="margin-top: 30px;">
                        <p>Notre équipe reste à votre disposition pour vous conseiller sur votre parcours.</p>
                        <p>À bientôt sur les sentiers !</p>
                    </div>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_content, 'html'))

            # Attach GPX file
            gpx_attachment = MIMEApplication(gpx_content, _subtype="gpx")
            gpx_attachment.add_header('Content-Disposition', 'attachment', 
                                    filename='parcours_bretagne.gpx')
            msg.attach(gpx_attachment)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.credentials)
                server.send_message(msg)

            logging.debug("Email sent successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise Exception(f"Failed to send email: {str(e)}")