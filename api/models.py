from django.db import models

class Repository(models.Model):
    name = models.CharField(max_length=255, unique=True)
    full_name = models.CharField(max_length=255)
    private = models.BooleanField()
    html_url = models.URLField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self):
        return self.name

class Branch(models.Model):
    repository = models.ForeignKey(Repository, related_name='branches', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('repository', 'name')

    def __str__(self):
        return self.name

class RepositoryConfiguration(models.Model):
    repository = models.OneToOneField(Repository, on_delete=models.CASCADE, primary_key=True)
    main_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CLONING', 'Cloning Repository'),
        ('PROCESSING', 'Processing Files'),
        ('GENERATING_MD', 'Generating README.md'),
        ('PUSHING', 'Pushing to GitHub'),
        ('PR_CREATED', 'Pull Request Created'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('STOPPED', 'Stopped'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    process_id = models.CharField(max_length=255, blank=True, null=True, help_text="Celery task ID for the flowchart generation process")
    pr_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL of the generated Pull Request")

    def __str__(self):
        return f"Configuration for {self.repository.name}"