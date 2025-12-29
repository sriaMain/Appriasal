from django.contrib import admin
from .models import (
    User,
    GiftCard,
    SurveyResponse,
    SurveyQuestion,
    EmployeeProfile,
    AppraisalRecord,
    Department,
)

admin.site.register(User)
admin.site.register(GiftCard)
admin.site.register(SurveyResponse)
admin.site.register(SurveyQuestion)
admin.site.register(EmployeeProfile)
admin.site.register(AppraisalRecord)
admin.site.register(Department)


