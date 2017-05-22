# _*_encoding:utf8_*_
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic.base import View
# from django.utils import timezone

import datetime
import random

from product.models import Product, Review
from .models import OrderItem, Order
from .forms import OrderForm, ReviewForm
# Create your views here.


# 立即购买
class ForeProductView(View):
    def get(self, request):
        # 获取商品、数量
        item_id = request.GET.get("pid", "")
        num = request.GET.get("num", "")
        item = Product.objects.get(id=int(item_id))
        user_id = request.user.id

        all_oi = OrderItem.objects.filter(user_id=user_id, order_id__isnull=True)
        found = False
        for oi in all_oi:
            if oi.product.id == item.id:
                oi.number += int(num)
                oi.save()
                found = True

        if not found:
            oi = OrderItem()
            oi.number = num
            oi.product_id = item_id
            oi.user_id = user_id
            oi.save()

        all_order_item = OrderItem.objects.filter(user_id=user_id, order_id__isnull=True)
        all_unit = 0
        for oi in all_order_item:
            unit = oi.product.promoteprice * oi.number
            all_unit += unit

        return render(request, "order_settlement.html", {
            "all_order_item": all_order_item,
            "all_unit": all_unit,
        })

    def post(self, request):
        pass


class AddCartView(View):
    def get(self, request):
        item_id = request.GET.get("pid", "")
        num = request.GET.get("num", "")
        # item = Product.objects.get(id=item_id)

        user = request.user
        found = False

        all_oi = OrderItem.objects.filter(user_id=user.id, order_id__isnull=True)
        for oi in all_oi:
            if oi.product.id == item_id:
                oi.number += int(num)
                oi.save()
                found = True
        if not found:
            oi = OrderItem()
            oi.user = user
            oi.number = num
            oi.product = Product.objects.get(id=item_id)
            oi.save()
        # 给js发送一个字符串表示成功加入购物车
        return HttpResponse("success", content_type='text')


class ForeCatView(View):
    def get(self, request):
        user = request.user
        ois = OrderItem.objects.filter(user_id=user.id, order_id__isnull=True)
        oi_count = ois.count()
        return render(request, "user_forecart.html", {
            "all_cat_item": ois,
            "all_cat_count": oi_count,
        })


# 创建订单
class CreateOrderView(View):
    def post(self, request):
        pass
        order_form = OrderForm(request.POST)
        user_id = request.user
        if order_form.is_valid():
            order_ask = order_form.save(commit=False)
            # time = datetime.datetime.now()
            order_ask.orderCode = int(datetime.datetime.now().strftime('%y%m%d%H%M%S')) * 10000 + random.randint(0, 9999)
            # order_ask.status = "waitPay"
            order_ask.user = user_id
            order_ask.save()
            all_oi = OrderItem.objects.filter(order_id__isnull=True, user_id=user_id)
            all_unit = 0
            for oi in all_oi:
                oi.order = order_ask
                oi.save()
                unit = oi.product.promoteprice * oi.number
                all_unit += unit
            return render(request, "order_payment.html", {
                "all_unit": all_unit,
                "order": order_ask,
            })
        else:
            return HttpResponse("妈的，出问题了，赶紧查查CreateOrderView", content_type='text')


# 点击确认支付，跳转到支付成功页面
class PayedView(View):
    def get(self, request):
        oid = request.GET.get("oid", "")
        order = Order.objects.get(id=oid)
        order.status = "waitDelivery"
        order.payDate = datetime.datetime.now()
        order.save()

        sum_unit = 0
        all_order_item = order.get_order_item()
        for oi in all_order_item:
            unit = oi.product.promoteprice * oi.number
            sum_unit += int(unit)
        return render(request, "order_paymentSuccess.html", {
            "order": order,
            "sum_unit": sum_unit,
        })


# 我的订单页
class MyOrderView(View):
    def get(self, request):
        user = request.user
        os = Order.objects.filter(user_id=user.id).exclude(status="delete")
        return render(request, "order_myOrder.html", {
            "orders": os,
        })


# 评价页面
class ReviewView(View):
    def get(self, request):
        order_item_id = request.GET.get("oid", "")
        oi = OrderItem.objects.get(id=order_item_id)
        return render(request, "order_review.html", {
            "order_item": oi,
        })

    def post(self, request):
        review_form = ReviewForm(request.POST)
        order_item_id = request.GET.get("oi", "")
        oi = OrderItem.objects.get(id=order_item_id)
        if review_form.is_valid():
            review_ask = review_form.save(commit=True)
            oi.status = "finish"
            oi.save()
            all_review = Review.objects.filter(product=review_ask.product)
            return render(request, "order_review.html", {
                "all_review": all_review,
                "show_only": True,
                "order_item": oi,
            })


class ConfirmPayView(View):
    def get(self, request):
        order_item_id = request.GET.get("oid", "")
        oi = OrderItem.objects.get(id=order_item_id)
        return render(request, "order_confirmPay.html", {
            "order_item": oi,
        })


class ForeCatBuyView(View):
    def get(self, request):
        oiids = request.GET.getlist("oiid", [])
        all_oi = []
        total = 0
        for oiid in oiids:
            oi = OrderItem.objects.get(id=int(oiid))
            all_oi.append(oi)
            total += oi.product.promoteprice * oi.number
        return render(request, "order_settlement.html", {
            "all_order_item": all_oi,
            "all_unit": total,
        })

