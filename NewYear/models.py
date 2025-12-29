from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ("EMPLOYEE", "Employee"),
        ("L1_MANAGER", "L1 Manager"),
        ("L2_MANAGER", "L2 Manager"),
        ("ADMIN", "Admin"),
    )

    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)

    full_name = models.CharField(max_length=100)
    designation = models.CharField(max_length=50)
    department = models.CharField(max_length=50)

    l1_manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="l1_team"
    )

    l2_departments = models.ManyToManyField(
        Department,
        blank=True,
        related_name="l2_managers"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="EMPLOYEE"
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


class SurveyQuestion(models.Model):
    QUESTION_TYPES = (
        ("TEXT", "Long Answer"),
        ("RATING", "Rating"),
    )

    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    rating_min = models.IntegerField(null=True, blank=True)
    rating_max = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.text


class SurveyResponse(models.Model):
    STATUS_CHOICES = (
        ("PENDING_L1", "Pending L1"),
        ("PENDING_L2", "Pending L2"),
        ("REJECTED", "Rejected"),
        ("APPROVED", "Approved"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answers = models.JSONField()
    l1_feedback = models.TextField(null=True, blank=True)
    l2_feedback = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
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
    total_surveys = models.IntegerField(default=0)
    total_rewards = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username


class AppraisalRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answers = models.JSONField()
    l1_feedback = models.TextField(null=True, blank=True)
    l2_feedback = models.TextField()
    reward_given = models.BooleanField(default=False)
    reward_code = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

