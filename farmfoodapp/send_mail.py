import smtplib

EMAIL_ADDRESS = "dalgroup13@gmail.com"
EMAIL_PASSWORD = 'macs@group13'


def send_email(email_subject, email_body, user_email):
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        subject = email_subject
        body = email_body

        msg = f'Subject: {subject}\n\n{body}'

        smtp.sendmail(EMAIL_ADDRESS, user_email, msg)
        return True
