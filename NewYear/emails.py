from django.core.mail import send_mail
from django.conf import settings


def send_gift_card_email(to_email, gift_code):
    send_mail(
        subject="🎁 Congratulations! Your Gift Card",
        message=f"""
Hello,

Congratulations! Your appraisal has been approved.

🎁 Gift Card Code: {gift_code}

Regards,
HR Team
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_email],
        fail_silently=False,
    )

