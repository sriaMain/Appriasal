from django.core.exceptions import ValidationError
from .models import User

L1_DEPARTMENT_MAP = {
    "NxSys": "Vignesh",
    "SAP": "Sharath",
}

L2_DEPARTMENT_MAP = {
    "NxSys": "Ravi",
    "SAP": "Sai",
}

# def auto_assign_managers(user):
#     if user.l1_manager and user.l2_manager:
#         return

#     if not user.department:
#         raise ValidationError("Department is not set for this employee")

#     dept = user.department.strip()

#     l1_username = L1_DEPARTMENT_MAP.get(dept)
#     l2_username = L2_DEPARTMENT_MAP.get(dept)

#     if not l1_username or not l2_username:
#         raise ValidationError(
#             f"No manager mapping found for department: {dept}"
#         )

#     try:
#         l1 = User.objects.get(username=l1_username, role="L1_MANAGER")
#         l2 = User.objects.get(username=l2_username, role="L2_MANAGER")
#     except User.DoesNotExist:
#         raise ValidationError(
#             f"L1 or L2 user not created for department: {dept}"
#         )

#     user.l1_manager = l1
#     user.l2_manager = l2
#     user.save(update_fields=["l1_manager", "l2_manager"])

from rest_framework.exceptions import ValidationError

def auto_assign_managers(user):
    dept = user.department 

    l1 = User.objects.filter(role="L1_MANAGER", department=dept).first()
    l2 = User.objects.filter(role="L2_MANAGER", department=dept).first()

    if not l1 or not l2:
        raise ValidationError(
            f"L1 or L2 user not created for department: {dept}"
        )

    user.l1_manager = l1
    user.l2_manager = l2
    user.save()
