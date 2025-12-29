from django.urls import path
from .views import (
    RegisterView,
    RefreshTokenView,
    LoginView,
    LogoutView,
    SurveySubmitView,
    EmployeeSurveyStatusView,
    EmployeePDFView,
    L1SurveyDetailView,
    L2SurveyDetailView,
    L1SurveyListView,
    L2SurveyListView,
    L1ApprovalView,
    L2ApprovalView,
    GiftCardBulkCreateView,
    SurveyQuestionListView,
    DepartmentListView,
    L1PendingReviewsView,
    L1CompletedReviewsView, 
    L2PendingReviewsView,
    L2CompletedReviewsView,
    SurveyQuestionDetailView
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("refresh/", RefreshTokenView.as_view()),


    path("survey/submit/", SurveySubmitView.as_view()),
    path("employee/surveys/", EmployeeSurveyStatusView.as_view()),
    path("employee/pdf/", EmployeePDFView.as_view()),
    path("departments/", DepartmentListView.as_view()),

    path("l1/survey/<int:survey_id>/view/", L1SurveyDetailView.as_view()),
    path("l1/survey/<int:survey_id>/action/", L1ApprovalView.as_view()),
    path("l1/reviews/pending/", L1PendingReviewsView.as_view()),
    path("l1/reviews/completed/", L1CompletedReviewsView.as_view()),
    path("l2/reviews/pending/", L2PendingReviewsView.as_view()),
    path("l2/reviews/completed/", L2CompletedReviewsView.as_view()),

    path("l2/survey/<int:survey_id>/view/", L2SurveyDetailView.as_view()),
    path("l2/survey/<int:survey_id>/action/", L2ApprovalView.as_view()),
    path("survey/questions/", SurveyQuestionListView.as_view()),
    path("survey/questions/<int:question_id>/", SurveyQuestionDetailView.as_view()),

    path("l1/surveys/", L1SurveyListView.as_view()),
    path("l2/surveys/", L2SurveyListView.as_view()),
    path("giftcards/", GiftCardBulkCreateView.as_view()),
]
