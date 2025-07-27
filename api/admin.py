from django.contrib import admin, messages
from .models import Repository, Branch, RepositoryConfiguration
from api.tasks import start_flowchart_process, stop_flowchart_process

from flowchart_ai.celery import app as celery_app

@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'full_name', 'private', 'html_url', 'created_at', 'updated_at')
    search_fields = ('name', 'full_name')
    list_filter = ('private', 'created_at')

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('repository', 'name')
    search_fields = ('repository__name', 'name')
    list_filter = ('repository__name',)

@admin.register(RepositoryConfiguration)
class RepositoryConfigurationAdmin(admin.ModelAdmin):
    list_display = ('repository', 'main_branch', 'status', 'pr_url')
    search_fields = ('repository__name', 'main_branch__name')
    autocomplete_fields = ['repository', 'main_branch']
    actions = ['start_flowchart_generation', 'stop_flowchart_generation']

    @admin.action(description='Start Flowchart Generation')
    def start_flowchart_generation(self, request, queryset):
        for config in queryset:
            if config.main_branch:
                task = start_flowchart_process.delay(config.pk)
                config.status = 'CLONING' # Initial status
                config.process_id = task.id
                config.save()
                self.message_user(request, f"Started flowchart generation for {config.repository.name}. Task ID: {task.id}", messages.SUCCESS)
            else:
                self.message_user(request, f"Cannot start for {config.repository.name}: Main branch not configured.", messages.ERROR)

    @admin.action(description='Stop Flowchart Generation')
    def stop_flowchart_generation(self, request, queryset):
        for config in queryset:
            if config.process_id:
                # Revoke the Celery task
                celery_app.control.revoke(config.process_id, terminate=True)
                config.status = 'STOPPED'
                config.save()
                self.message_user(request, f"Stopped flowchart generation for {config.repository.name}. Task ID: {config.process_id}", messages.WARNING)
            else:
                self.message_user(request, f"No active process found for {config.repository.name}.", messages.INFO)