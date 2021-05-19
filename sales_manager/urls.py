from django.urls import path
from sales_manager import views

urlpatterns = [
    path('', views.main_page),
    path('book_detail/<int:book_id>/', views.book_detail, name="book-detail")
]