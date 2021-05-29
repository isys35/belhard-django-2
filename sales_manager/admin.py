from django.contrib import admin
from sales_manager.models import Book, Comment


class CommentAdmin(admin.StackedInline):
    model = Comment
    readonly_fields = ("like",)


class BookInline(admin.ModelAdmin):
    inlines = (CommentAdmin, )
    readonly_fields = ("likes", )
    list_filter = ("date_publish", )
    list_editable = ("text", )
    list_display = ("title", "text", )

admin.site.register(Book, BookInline)

# admin.site.register(Book)
# admin.site.register(Comment)
