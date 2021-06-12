from abc import ABC

from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.generics import ListAPIView, ListCreateAPIView, GenericAPIView, UpdateAPIView, \
    RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.views import APIView
# from django_filters import rest_framework as filters
from rest_framework import filters

from sales_manager.models import Book, Comment, UserRateBook
from django.views import View
from sales_manager.utils import get_book_with_comment


def main_page(request):
    query_set = get_book_with_comment()
    context = {"books": query_set}
    return render(request, "sales_manager/index.html", context=context)


def book_detail(request, book_id):
    query_set = get_book_with_comment()
    book = query_set.get(id=book_id)
    context = {"book": book}
    return render(request, "sales_manager/book_detail.html", context=context)


@login_required(login_url="/admin/")
def book_like(request, book_id, rate, redirect_url):
    UserRateBook.objects.update_or_create(
        user_id=request.user.id,
        book_id=book_id,
        defaults={'rate': rate}
    )
    book = Book.objects.get(id=book_id)
    book.avg_rate = book.rated_user.aggregate(rate=Avg("rate"))['rate']
    book.save(update_fields=['avg_rate'])
    if redirect_url == 'main_page':
        return redirect('main_page')
    elif redirect_url == 'book-detail':
        return redirect('book-detail', book_id=book_id)


class LoginView(View):
    def get(self, request):
        return render(request, 'sales_manager/login.html')

    def post(self, request):
        user = authenticate(username=request.POST['login'],
                            password=request.POST['pwd'])
        if user is not None:
            login(request, user)
            return redirect("main_page")
        return redirect("login")


def logout_view(request):
    logout(request)
    return redirect("main_page")


@login_required()
@require_http_methods(["POST"])
def add_comment(request, book_id):
    text = request.POST.get("text")
    Comment.objects.create(
        text=text,
        user=request.user,
        book_id=book_id
    )
    return redirect("book-detail", book_id=book_id)


@login_required()
def comment_like(request, comment_id):
    com = Comment.objects.get(id=comment_id)
    if request.user in com.like.all():
        com.like.remove(request.user)
    else:
        com.like.add(request.user)
    return redirect("book-detail", com.book_id)


def add_like_ajax(request):
    comment_id = request.POST.get('comment_id')
    query_com = Comment.objects.filter(id=comment_id)
    if query_com.exists():
        com = query_com.first()
        if request.user in com.like.all():
            com.like.remove(request.user)
        else:
            com.like.add(request.user)
        return HttpResponse(com.like.count())
    return HttpResponseNotFound()


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id", "title", "text", "date_publish", "author", "avg_rate"]


class RateBookSerializer(serializers.Serializer):
    rate = serializers.IntegerField()
    book_id = serializers.IntegerField()

    def validate_rate(self, instance):
        if instance > 5:
            raise serializers.ValidationError("rate must be less than 5")
        elif instance < 0:
            raise serializers.ValidationError("rate must be more than 0")
        return instance


# class BookListAPIView(ListAPIView):
#     serializer_class = BookSerializer
#     queryset = Book.objects.all()

# class BookListAPIView(APIView):
#
#     def get(self, request):
#         query_set = Book.objects.all()
#         serializer = BookSerializer(query_set, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)
#
#     def post(self, request):
#         serializer = BookSerializer(data=request.data)
#         if serializer.is_valid():
#             book = serializer.save()
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookListAPIView(ListCreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ("id", 'title')
    ordering = ["-id"]
    search_fields = ("title", 'text')


class BookDetail(GenericAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get(self, request, pk):
        serializer = self.serializer_class(self.get_object())
        return Response(serializer.data)


class BookUpdateAPI(RetrieveUpdateDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class AddRateBookAPI(APIView):
    serializer_class = RateBookSerializer

    # permission_classes = []

    def put(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = get_object_or_404(Book, id=serializer.data['book_id'])
        UserRateBook.objects.update_or_create(
            user_id=request.user.id,
            book_id=book.id,
            defaults={'rate': serializer.data['rate']}
        )
        book.avg_rate = book.rated_user.aggregate(rate=Avg("rate"))['rate']
        book.save(update_fields=['avg_rate'])
        return Response({}, status=status.HTTP_200_OK)
