from django.contrib import admin
from .models import UserProfile, Field, FieldUpdate


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'crop_type', 'current_stage', 'assigned_agent', 'planting_date', 'computed_status']
    list_filter = ['current_stage', 'crop_type']
    search_fields = ['name', 'location']


@admin.register(FieldUpdate)
class FieldUpdateAdmin(admin.ModelAdmin):
    list_display = ['field', 'stage', 'updated_by', 'created_at']
    list_filter = ['stage']