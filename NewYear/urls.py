from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    SurveyQuestionView,
    SurveySubmitView,
    EmployeeSurveyStatusView,
    GiftCardBulkCreateView,
    EmployeePDFView,
    AdminSurveyResponsesView,
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("refresh/", RefreshTokenView.as_view()),

    path("survey/questions/", SurveyQuestionView.as_view()),
    path("survey/questions/<int:question_id>/", SurveyQuestionView.as_view()),

    path("survey/submit/", SurveySubmitView.as_view()),
    path("employee/surveys/", EmployeeSurveyStatusView.as_view()),
    path("employee/pdf/", EmployeePDFView.as_view()),

    path("giftcards/", GiftCardBulkCreateView.as_view()),
    path("giftcards/<int:giftcard_id>/", GiftCardBulkCreateView.as_view()),
    
    path("admin/surveys/", AdminSurveyResponsesView.as_view()),

]
