from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def send_payment_confirmation_email(order):
    render_string = "orders/emails/payment_confirmation_email.html"
    mail_subject = f"Payment Confirmation - {order.payment.payment_id}"
    message = render_to_string(
        render_string,
        {"user": order.user, "order": order, "payment": order.payment},
    )
    to_email = order.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.content_subtype = "html"
    send_email.send(fail_silently=False)


def send_order_confirmation_email(order):
    render_string = "orders/emails/order_confirmation_email.html"
    mail_subject = f"Order Confirmation #{order.order_number}"
    message = render_to_string(
        render_string,
        {"user": order.user, "order": order, "payment": order.payment},
    )
    to_email = order.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.content_subtype = "html"
    send_email.send(fail_silently=False)
