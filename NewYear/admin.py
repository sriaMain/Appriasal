from django.contrib import admin
from .models import (
    User,
    SurveyQuestion,
    SurveyResponse,
    GiftCard,
    EmployeeProfile,
    AppraisalRecord,
)

admin.site.register(User)
admin.site.register(SurveyQuestion)
admin.site.register(SurveyResponse)
admin.site.register(GiftCard)
admin.site.register(EmployeeProfile)
admin.site.register(AppraisalRecord)
