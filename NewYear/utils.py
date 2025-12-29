from django.core.exceptions import ValidationError
from .models import User, Department

L1_DEPARTMENT_MAP = {
    "NxSys": "Vignesh",
    "SAP": "Sharath",
}

L2_DEPARTMENT_MAP = {
    "NxSys": "Ravi",
    "SAP": "Sai",
}


def auto_assign_managers(user):
    dept = user.department

    if user.role == "EMPLOYEE":
        if user.l1_manager:
            return

        l1 = User.objects.filter(
            department=dept,
            role="L1_MANAGER",
            is_active=True
        ).first()

        if not l1:
            l1_username = L1_DEPARTMENT_MAP.get(dept)
            if l1_username:
                l1 = User.objects.filter(
                    username=l1_username,
                    role="L1_MANAGER",
                    is_active=True
                ).first()

        if not l1:
            raise ValidationError(
                f"No L1 Manager assigned or found for department: {dept}"
            )

        user.l1_manager = l1
        user.save(update_fields=["l1_manager"])

    if user.role == "L2_MANAGER":
        department_obj, _ = Department.objects.get_or_create(name=dept)
        user.l2_departments.add(department_obj)

    if user.role == "L1_MANAGER":
        pass

    return
