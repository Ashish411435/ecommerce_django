from django.urls import path, include
from . import views

urlpatterns = [
    path("place-order/", views.place_order, name="place_order"),
    path("payment/", views.payment, name="payment"),
    path(
        "demo/checkout/api/paypal/order/create/",
        views.create_order,
        name="paypal_create_order",
    ),
    path(
        "demo/checkout/api/paypal/order/<str:order_id>/capture/",
        views.capture_order,
        name="paypal_capture_order",
    ),
    path("payment-complete/", views.payment_complete, name="payment_complete"),
    path(
        "order-complete/<str:order_number>/",
        views.order_complete,
        name="order_complete",
    ),
]
