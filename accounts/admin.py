from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('created_at',)}),
    )
    readonly_fields = ('created_at',)
