from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
import datetime
from django.contrib import messages
import requests
from django.http import JsonResponse
from django.conf import settings
import json
from django.urls import reverse

from cart.models import CartItem
from store.models import Product
from .models import Order, Payment, OrderProduct
from .forms import OrderForm
from orders.payments.paypal import get_access_token
from orders.services.email_service import (
    send_payment_confirmation_email,
    send_order_confirmation_email,
)

# Create your views here.


@login_required(login_url="login")
def place_order(request, total=0, quantity=0):
    current_user = request.user
    order_total = 0
    grand_total = 0
    tax = 0
    context = {}

    cart_items = CartItem.objects.filter(user=current_user, is_active=True)
    if cart_items.exists():
        for cart_item in cart_items:
            total += cart_item.product.price * cart_item.quantity
            quantity += cart_item.quantity
        tax = (2 * total) / 100
        order_total = total
        grand_total = total + tax

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing info inside orders table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data["first_name"]
            data.last_name = form.cleaned_data["last_name"]
            data.phone_number = form.cleaned_data["phone_number"]
            data.email = form.cleaned_data["email"]
            data.address_line_1 = form.cleaned_data["address_line_1"]
            data.address_line_2 = form.cleaned_data["address_line_2"]
            data.country = form.cleaned_data["country"]
            data.state = form.cleaned_data["state"]
            data.city = form.cleaned_data["city"]
            data.order_note = form.cleaned_data["order_note"]
            data.order_total = order_total
            data.grand_total = grand_total
            data.tax = tax
            data.ip = request.META.get("REMOTE_ADDR")
            data.save()

            # Generate Order Number
            date_time = datetime.datetime.now()
            order_number = (
                f"{date_time.strftime("%Y%m%d%H%M%S")}{current_user.id}{data.id}"
            )
            data.order_number = order_number
            data.save()
            order = Order.objects.get(
                user=current_user, is_ordered=False, order_number=order_number
            )
            context = {
                "order": order,
                "cart_items": cart_items,
                "order_total": order_total,
                "tax": tax,
                "grand_total": grand_total,
            }
        messages.success(request, "Order Placed Successfully")
        return render(request, "orders/payment.html", context)
    else:
        return redirect("checkout")


def payment(request):
    return render(request, "orders/payment.html")


def create_order(request):
    access_token = get_access_token()

    data = json.loads(request.body)
    order_id = data["order_id"]
    order_number = data["order_number"]

    order = Order.objects.get(
        id=order_id, order_number=order_number, is_ordered=False, user=request.user
    )
    order_amount = order.grand_total

    response = requests.post(
        f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [
                {"amount": {"currency_code": "USD", "value": str(order_amount)}}
            ],
        },
    )

    print("CREATE ORDER STATUS:", response.status_code)
    print("CREATE ORDER RESPONSE:", response.text)

    return JsonResponse(response.json())


def capture_order(request, order_id):

    access_token = get_access_token()

    response = requests.post(
        f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        json={},
    )

    print("CAPTURE STATUS:", response.status_code)
    print("CAPTURE RESPONSE:", response.text)

    return JsonResponse(response.json())


def payment_complete(request):
    current_user = request.user

    body = json.loads(request.body)

    order_number = body["order_number"]
    order_id = body["order_id"]
    payment_id = body["payment_id"]
    payment_method = body["payment_method"]
    status = body["status"]

    order = Order.objects.get(
        id=order_id, user=current_user, order_number=order_number, is_ordered=False
    )

    payment = Payment.objects.create(
        user=current_user,
        payment_id=payment_id,
        payment_method=payment_method,
        amount_paid=order.grand_total,
        status=status,
    )

    if payment.status == "COMPLETED":
        order.payment = payment
        order.is_ordered = True
        order.status = "Accepted"
        order.save()

    # Move the Cart Items to Order Product Table
    cart_items = CartItem.objects.filter(user=current_user)
    for item in cart_items:
        order_product = OrderProduct.objects.create(
            order=order,
            payment=payment,
            user=current_user,
            product=item.product,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=True,
        )
        order_product.variations.set(item.variations.all())

        # Reduce the quantity of sold product
        # item.product.stock -= item.quantity
        # item.product.save(update_fields=["stock"])

        # Another approach for scalable projects
        from django.db.models import F

        Product.objects.filter(id=item.product_id).update(
            stock=F("stock") - item.quantity
        )

    # Clear Cart
    cart_items.delete()

    # Send Order Recieved email to user
    send_payment_confirmation_email(order)
    send_order_confirmation_email(order)

    # Send order number and transaction id back to json response

    return JsonResponse(
        {
            "redirect_url": reverse(
                "order_complete", kwargs={"order_number": order.order_number}
            )
        }
    )


def order_complete(request, order_number):
    if not order_number:
        return redirect("home")

    order = get_object_or_404(
        Order.objects.select_related("payment"),
        order_number=order_number,
        is_ordered=True,
        user=request.user,
    )

    ordered_products = OrderProduct.objects.filter(order=order).select_related(
        "payment"
    )

    context = {
        "order": order,
        "ordered_products": ordered_products,
    }
    return render(request, "orders/thankyou.html", context)
