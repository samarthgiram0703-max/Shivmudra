from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'scheduled_date', 'location', 'advanced_rs', 'pending_rs', 'total_rs', 'status')
    list_filter = ('status', 'scheduled_date', 'user')
    search_fields = ('name', 'location', 'user__username')
    readonly_fields = ('total_rs', 'created_at')
    ordering = ('-scheduled_date',)

