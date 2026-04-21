from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import UserProfile, Field, FieldUpdate


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'colored_role', 'user_email', 'field_count']
    list_filter   = ['role']
    search_fields = ['user__username', 'user__email', 'user__first_name']
    readonly_fields = ['user']

    def colored_role(self, obj):
        color = '#2D6A2D' if obj.role == 'admin' else '#D4A017'
        label = 'Admin' if obj.role == 'admin' else 'Field Agent'
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:0.78rem;font-weight:600;">{}</span>',
            color, label
        )
    colored_role.short_description = 'Role'

    def user_email(self, obj):
        return obj.user.email or '—'
    user_email.short_description = 'Email'

    def field_count(self, obj):
        count = obj.user.assigned_fields.count()
        return format_html(
            '<span style="font-weight:600;color:#2D6A2D;">{}</span> field{}',
            count, 's' if count != 1 else ''
        )
    field_count.short_description = 'Assigned Fields'


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display  = ['name', 'crop_badge', 'stage_badge', 'status_badge', 'assigned_agent', 'planting_date', 'days_active']
    list_filter   = ['current_stage', 'crop_type', 'planting_date']
    search_fields = ['name', 'location', 'assigned_agent__username']
    readonly_fields  = ['created_at', 'updated_at', 'days_since_planting', 'computed_status']
    ordering      = ['-created_at']
    date_hierarchy = 'planting_date'

    fieldsets = (
        ('Field Information', {
            'fields': ('name', 'crop_type', 'location', 'size_acres')
        }),
        ('Growth Tracking', {
            'fields': ('planting_date', 'current_stage', 'days_since_planting', 'computed_status')
        }),
        ('Assignment', {
            'fields': ('assigned_agent', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def crop_badge(self, obj):
        colors = {
            'maize': '#F59E0B', 'wheat': '#D97706', 'rice': '#10B981',
            'sorghum': '#8B5CF6', 'beans': '#EF4444', 'sunflower': '#F59E0B',
            'cotton': '#6B7280', 'other': '#9CA3AF',
        }
        color = colors.get(obj.crop_type, '#9CA3AF')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 9px;border-radius:12px;font-size:0.75rem;font-weight:600;text-transform:capitalize;">{}</span>',
            color, obj.crop_type
        )
    crop_badge.short_description = 'Crop'

    def stage_badge(self, obj):
        colors = {
            'planted':   ('#DBEAFE', '#1D4ED8'),
            'growing':   ('#D1FAE5', '#065F46'),
            'ready':     ('#FEF3C7', '#92400E'),
            'harvested': ('#E5E7EB', '#374151'),
        }
        bg, fg = colors.get(obj.current_stage, ('#F3F4F6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 9px;border-radius:12px;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;">{}</span>',
            bg, fg, obj.get_current_stage_display()
        )
    stage_badge.short_description = 'Stage'

    def status_badge(self, obj):
        status = obj.computed_status
        configs = {
            'active':    ('#D1FAE5', '#065F46', '✓ Active'),
            'at_risk':   ('#FEF3C7', '#92400E', '⚠ At Risk'),
            'completed': ('#E5E7EB', '#374151', '✔ Completed'),
        }
        bg, fg, label = configs.get(status, ('#F3F4F6', '#374151', status))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:700;">{}</span>',
            bg, fg, label
        )
    status_badge.short_description = 'Status'

    def days_active(self, obj):
        days = obj.days_since_planting
        color = '#DC2626' if days > 90 else '#D4A017' if days > 60 else '#2D6A2D'
        return format_html(
            '<span style="color:{};font-weight:600;">{} days</span>',
            color, days
        )
    days_active.short_description = 'Days'


@admin.register(FieldUpdate)
class FieldUpdateAdmin(admin.ModelAdmin):
    list_display   = ['field', 'stage_badge', 'updated_by', 'notes_preview', 'created_at']
    list_filter    = ['stage', 'created_at']
    search_fields  = ['field__name', 'updated_by__username', 'notes']
    readonly_fields = ['created_at']
    ordering       = ['-created_at']
    date_hierarchy = 'created_at'

    def stage_badge(self, obj):
        colors = {
            'planted':   ('#DBEAFE', '#1D4ED8'),
            'growing':   ('#D1FAE5', '#065F46'),
            'ready':     ('#FEF3C7', '#92400E'),
            'harvested': ('#E5E7EB', '#374151'),
        }
        bg, fg = colors.get(obj.stage, ('#F3F4F6', '#374151'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 9px;border-radius:12px;font-size:0.75rem;font-weight:700;">{}</span>',
            bg, fg, obj.get_stage_display()
        )
    stage_badge.short_description = 'Stage'

    def notes_preview(self, obj):
        if obj.notes:
            return obj.notes[:60] + ('...' if len(obj.notes) > 60 else '')
        return format_html('<span style="color:#9CA3AF;">No notes</span>')
    notes_preview.short_description = 'Notes'