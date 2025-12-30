from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_gift_card_email(to_email, gift_code, employee_name):
    subject = "🎁 Congratulations! Your Appraisal Gift Card"

    text_content = f"""
Congratulations {employee_name}!

Your appraisal has been successfully completed.

Gift Card Code: {gift_code}

Thank you for your valuable contributions.

HR Team
"""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<title>Appraisal Congratulations</title>
</head>

<body style="margin:0;padding:0;background:#fafbff;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td align="center">

<table width="620" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:18px;overflow:hidden;margin-top:25px;box-shadow:0 10px 30px rgba(0,0,0,0.1);">

<tr>
<td style="background:#6a11cb;background-image: url('https://res.cloudinary.com/dulamyf3s/image/upload/v1767090609/images_thqj0a.jpg');padding:45px 25px;text-align:center;color:#fff; background-size: cover; background-position: center;">
<h1 style="margin:0;font-size:34px; color:#fff">🎉 CONGRATULATIONS!</h1>
<p style="margin-top:10px;font-size:18px; color:#fff;">
Your Appraisal is Successfully Completed
</p>
</td>
</tr>

<tr>
<td style="padding:35px 25px;text-align:center;">
<h2 style="color:#333;margin:0;">Well Done, <span style="color:#6a11cb;">{employee_name}</span>!</h2>

<p style="font-size:16px;color:#555;line-height:1.6;margin-top:10px;">
We truly appreciate your hard work, dedication, and consistent performance.
Your commitment has played a major role in our success, and we’re proud of you.
Keep achieving greater milestones and inspiring others!
</p>

<p style="font-size:16px;color:#444;margin-top:20px;">
💐 As a token of appreciation, here’s a special reward just for you
</p>

<div style="display:inline-block;margin-top:10px;background:#f5f3ff;border:2px dashed #6a11cb;border-radius:10px;padding:16px 30px;">
<span style="font-size:18px;color:#6a11cb;font-weight:bold;letter-spacing:2px;">{gift_code}</span>
</div>

<p style="font-size:14px;color:#777;margin-top:8px;">
Use this code to redeem your reward 🎁
</p>

</td>
</tr>

<tr>
<td style="background:#f4f4ff;text-align:center;padding:18px;color:#666;font-size:13px;">
Celebrating your growth, success & achievements. Keep shining! ✨
</td>
</tr>

</table>

</td>
</tr>
</table>
</body>
</html>
"""

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
