from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, role="EMPLOYEE"):
        if not username or not email:
            raise ValueError("Username and email are required")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            role=role
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        return self.create_user(
            username=username,
            email=email,
            password=password,
            role="ADMIN"
        )


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("EMPLOYEE", "Employee"),
        ("ADMIN", "Admin"),
    )

    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="EMPLOYEE")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    def __str__(self):
        return self.username


class SurveyQuestion(models.Model):
    QUESTION_TYPES = (
        ("TEXT", "Text"),
        ("RATING", "Rating"),
    )

    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    rating_min = models.IntegerField(null=True, blank=True)
    rating_max = models.IntegerField(null=True, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text


class SurveyResponse(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="survey"
    )
    answers = models.JSONField()
    status = models.CharField(max_length=20, default="APPROVED")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey - {self.user.username}"


class GiftCard(models.Model):
    code = models.CharField(max_length=100, unique=True)
    is_used = models.BooleanField(default=False)

    assigned_to = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.code


class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_surveys = models.PositiveIntegerField(default=0)
    total_rewards = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.username


class AppraisalRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answers = models.JSONField()
    reward_given = models.BooleanField(default=True)
    reward_code = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Appraisal - {self.user.username}"
