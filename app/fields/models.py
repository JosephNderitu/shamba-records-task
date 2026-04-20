from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('agent', 'Field Agent'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='agent')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_agent(self):
        return self.role == 'agent'


class Field(models.Model):
    CROP_CHOICES = [
        ('maize', 'Maize'),
        ('wheat', 'Wheat'),
        ('rice', 'Rice'),
        ('sorghum', 'Sorghum'),
        ('beans', 'Beans'),
        ('sunflower', 'Sunflower'),
        ('cotton', 'Cotton'),
        ('other', 'Other'),
    ]

    STAGE_CHOICES = [
        ('planted', 'Planted'),
        ('growing', 'Growing'),
        ('ready', 'Ready'),
        ('harvested', 'Harvested'),
    ]

    name = models.CharField(max_length=100)
    crop_type = models.CharField(max_length=20, choices=CROP_CHOICES, default='maize')
    planting_date = models.DateField()
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='planted')
    location = models.CharField(max_length=200, blank=True)
    size_acres = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    assigned_agent = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_fields'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_fields'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} — {self.crop_type}"

    @property
    def days_since_planting(self):
        return (timezone.now().date() - self.planting_date).days

    @property
    def computed_status(self):
        """
        Status Logic:
        - Completed: stage is 'harvested'
        - At Risk: stage is 'planted' or 'growing' AND no update in last 7 days
                   OR days_since_planting > 90 and still not 'ready'/'harvested'
        - Active: everything else
        """
        if self.current_stage == 'harvested':
            return 'completed'

        last_update = self.updates.order_by('-created_at').first()
        days_since_update = None
        if last_update:
            days_since_update = (timezone.now() - last_update.created_at).days

        if days_since_update is None or days_since_update > 7:
            return 'at_risk'

        if self.days_since_planting > 90 and self.current_stage not in ['ready', 'harvested']:
            return 'at_risk'

        return 'active'

    @property
    def status_badge_color(self):
        colors = {
            'active': 'success',
            'at_risk': 'warning',
            'completed': 'secondary',
        }
        return colors.get(self.computed_status, 'secondary')

    class Meta:
        ordering = ['-created_at']


class FieldUpdate(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='updates')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    stage = models.CharField(max_length=20, choices=Field.STAGE_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.field.name} → {self.stage} by {self.updated_by}"

    class Meta:
        ordering = ['-created_at']