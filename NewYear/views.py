from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from .models import SurveyQuestion, SurveyResponse

from .models import (
    User,
    SurveyQuestion,
    SurveyResponse,
    GiftCard,
    EmployeeProfile,
    AppraisalRecord,
    Department,
)

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    SurveySerializer,
    SurveyQuestionSerializer,
)

from .utils import auto_assign_managers
from .emails import send_gift_card_email


class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"error": "Refresh token is required"}, status=400)

        try:
            token = RefreshToken(refresh_token)
            return Response({"access": str(token.access_token)})
        except TokenError:
            return Response({"error": "Invalid or expired refresh token"}, status=401)


class DepartmentListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        departments = Department.objects.all().order_by("name").values_list("name", flat=True)
        return Response({"departments": list(departments)})

    def post(self, request):
        if not request.user.is_authenticated or request.user.role != "ADMIN":
            return Response({"error": "Only admins can add departments"}, status=403)

        name = request.data.get("name")
        if not name:
            return Response({"error": "Department name is required"}, status=400)

        department, created = Department.objects.get_or_create(name=name)
        if not created:
            return Response({"error": "Department already exists"}, status=400)

        return Response({"message": "Department added successfully", "name": department.name}, status=201)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "User registered successfully"}, status=201)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        identifier = request.data.get("identifier")
        password = request.data.get("password")

        user = User.objects.filter(
            Q(username=identifier) | Q(email=identifier)
        ).first()

        if not user or not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=401)

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"message": "Logged out successfully"})


class SurveyQuestionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = SurveyQuestion.objects.filter(is_active=True).order_by("order")
        return Response([
            {
                "id": q.id,
                "text": q.text,
                "type": q.question_type,
                "rating_min": q.rating_min,
                "rating_max": q.rating_max
            }
            for q in questions
        ])

    # def post(self, request):
    #     if request.user.role != "L2_MANAGER" and request.user.role != "ADMIN":
    #         return Response({"error": "Only admin and L2 managers can add questions"}, status=403)

    #     serializer = SurveyQuestionSerializer(data=request.data, many=True)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response({"message": "Questions added"}, status=201)
    
def post(self, request):
    if request.user.role not in ["L2_MANAGER", "ADMIN"]:
        return Response(
            {"error": "Only admin and L2 managers can add questions"},
            status=403
        )

    data = request.data

    if isinstance(data, dict):
        serializer = SurveyQuestionSerializer(data=data)
    else:
        serializer = SurveyQuestionSerializer(data=data, many=True)

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response({"message": "Question(s) added successfully"}, status=201)


class SurveyQuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, question_id):
        try:
            return SurveyQuestion.objects.get(id=question_id)
        except SurveyQuestion.DoesNotExist:
            return None

    def put(self, request, question_id):
        if request.user.role not in ["L2_MANAGER", "ADMIN"]:
            return Response(
                {"error": "Only admin and L2 managers can update questions"},
                status=403
            )

        try:
            question = SurveyQuestion.objects.get(id=question_id)
        except SurveyQuestion.DoesNotExist:
            return Response(
                {"error": "Question not found"},
                status=404
            )

        serializer = SurveyQuestionSerializer(
            question,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Question updated successfully",
                "data": serializer.data
            },
            status=200
        )



    def delete(self, request, question_id):
        if request.user.role not in ["L2_MANAGER", "ADMIN"]:
            return Response({"error": "Forbidden"}, status=403)

        question = self.get_object(question_id)
        if not question:
            return Response({"error": "Question not found"}, status=404)

        question.is_active = False
        question.save(update_fields=["is_active"])

        return Response({"message": "Question deleted successfully"})


class SurveySubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        already_submitted = SurveyResponse.objects.filter(
            user=request.user
        ).exists()

        if already_submitted:
            return Response(
                {"error": "You have already submitted the survey"},
                status=400
            )

        auto_assign_managers(request.user)

        serializer = SurveySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if request.user.role == "L1_MANAGER":
            status_value = "PENDING_L2"
        else:
            status_value = "PENDING_L1"

        survey = SurveyResponse.objects.create(
            user=request.user,
            answers=serializer.validated_data["answers"],
            status=status_value
        )

        return Response(
            {
                "survey_id": survey.id,
                "status": status_value
            },
            status=201
        )

def format_answers(answers):
    questions = SurveyQuestion.objects.filter(id__in=answers.keys())
    question_map = {str(q.id): q.text for q in questions}

    return [
        {
            "question_id": int(q_id),
            "question": question_map.get(str(q_id)),
            "answer": ans
        }
        for q_id, ans in answers.items()
    ]

class EmployeeSurveyStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        surveys = SurveyResponse.objects.filter(user=request.user)

        return Response([
            {
                "survey_id": s.id,
                "responses": build_question_answers(s.answers),
                "l1_feedback": s.l1_feedback,
                "l2_feedback": s.l2_feedback,
                "status": s.status
            }
            for s in surveys
        ])


def build_question_answers(answers):
    if not answers:
        return []

    question_ids = [int(qid) for qid in answers.keys()]
    questions = SurveyQuestion.objects.filter(id__in=question_ids)

    question_map = {str(q.id): q.text for q in questions}

    return [
        {
            "question_id": int(qid),
            "question": question_map.get(str(qid)),
            "answer": answer
        }
        for qid, answer in answers.items()
    ]


class L1SurveyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ["L1_MANAGER", "ADMIN"] and not request.user.is_superuser:
            return Response({"error": "Forbidden"}, status=403)

        surveys = SurveyResponse.objects.filter(
            status="PENDING_L1"
        ) if request.user.role == "ADMIN" else SurveyResponse.objects.filter(
            status="PENDING_L1",
            user__l1_manager=request.user
        )

        return Response([
    {
        "survey_id": s.id,
        "employee": s.user.full_name,
        "department": s.user.department,
        "responses": format_answers(s.answers),
        "l1_feedback": s.l1_feedback,
        "status": s.status
    }
    for s in surveys
])



class L1ApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, survey_id):
        survey = SurveyResponse.objects.get(id=survey_id, status="PENDING_L1")

        survey.l1_feedback = request.data.get("feedback")
        survey.status = "PENDING_L2"
        survey.save()

        return Response({"message": "Forwarded to L2"})

class L1PendingReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "L1_MANAGER":
            return Response({"error": "Forbidden"}, status=403)

        surveys = SurveyResponse.objects.filter(
            status="PENDING_L1",
            user__l1_manager=request.user
        )

        return Response([
            {
                "survey_id": s.id,
                "employee": s.user.full_name,
                "department": s.user.department,
                "responses": build_question_answers(s.answers),
                "status": s.status
            }
            for s in surveys
        ])



class L1CompletedReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "L1_MANAGER":
            return Response({"error": "Forbidden"}, status=403)

        surveys = SurveyResponse.objects.filter(
            user__l1_manager=request.user,
            status__in=["PENDING_L2", "APPROVED", "REJECTED"]
        )

        return Response([
            {
                "survey_id": s.id,
                "employee": s.user.full_name,
                "department": s.user.department,
                "l1_feedback": s.l1_feedback,
                "status": s.status
            }
            for s in surveys
        ])


class L2PendingReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ["L2_MANAGER", "ADMIN"]:
            return Response({"error": "Forbidden"}, status=403)

        surveys = SurveyResponse.objects.filter(status="PENDING_L2")

        return Response([
            {
                "survey_id": s.id,
                "employee": s.user.full_name,
                "department": s.user.department,
                "responses": build_question_answers(s.answers),
                "l1_review": {
                    "feedback": s.l1_feedback
                },
                "l2_review": {
                    "feedback": s.l2_feedback
                },
                "status": s.status
            }
            for s in surveys
        ])



class L2CompletedReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ["L2_MANAGER", "ADMIN"]:
            return Response({"error": "Forbidden"}, status=403)

        surveys = SurveyResponse.objects.filter(
            status__in=["APPROVED", "REJECTED"]
        )

        return Response([
            {
                "survey_id": s.id,
                "employee": s.user.full_name,
                "department": s.user.department,
                "responses": build_question_answers(s.answers),
                "l1_review": {
                    "feedback": s.l1_feedback
                },
                "l2_review": {
                    "feedback": s.l2_feedback
                },
                "status": s.status
            }
            for s in surveys
        ])




@transaction.atomic
def assign_gift_card(user):
    gift_card = GiftCard.objects.select_for_update().filter(is_used=False).first()
    if not gift_card:
        raise ValidationError("No gift cards available")

    gift_card.is_used = True
    gift_card.assigned_to = user
    gift_card.assigned_at = timezone.now()
    gift_card.save()
    return gift_card


class L2SurveyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ["L2_MANAGER", "ADMIN"]:
            return Response({"error": "Forbidden"}, status=403)

        surveys = SurveyResponse.objects.filter(status="PENDING_L2")

        return Response([
    {
        "survey_id": s.id,
        "employee": s.user.full_name,
        "department": s.user.department,
        "responses": format_answers(s.answers),
        "l1_feedback": s.l1_feedback,
        "l2_feedback": s.l2_feedback,
        "status": s.status
    }
    for s in surveys
])
    



class GiftCardBulkCreateView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        gift_cards = GiftCard.objects.all().order_by("-id")

        total = gift_cards.count()
        used = gift_cards.filter(is_used=True).count()
        remaining = total - used

        cards = [
            {
                "id": g.id,
                "is_used": g.is_used,
                "assigned_to": g.assigned_to.username if g.assigned_to else None,
                "assigned_at": g.assigned_at,
            }
            for g in gift_cards
        ]

        return Response({
            "stats": {
                "total": total,
                "used": used,
                "remaining": remaining
            },
            "gift_cards": cards
        })

    def post(self, request):
        codes = request.data.get("codes", [])

        if not isinstance(codes, list) or not codes:
            return Response({"error": "codes must be a non-empty list"}, status=400)

        GiftCard.objects.bulk_create(
            [GiftCard(code=c) for c in codes],
            ignore_conflicts=True
        )

        return Response({"message": "Gift cards processed"}, status=201)


class L2ApprovalView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, survey_id):
        try:
            survey = (
                SurveyResponse.objects
                .select_for_update()
                .get(id=survey_id)
            )
        except SurveyResponse.DoesNotExist:
            return Response(
                {"error": "Survey not found"},
                status=404
            )

        if survey.status != "PENDING_L2":
            return Response(
                {"error": "Survey already reviewed"},
                status=400
            )

        action = request.data.get("action")
        feedback = request.data.get("feedback")

        if action == "REJECT":
            survey.l2_feedback = feedback
            survey.status = "REJECTED"
            survey.save(update_fields=["l2_feedback", "status"])
            return Response({"message": "Survey rejected"})

        survey.l2_feedback = feedback
        survey.status = "APPROVED"
        survey.save(update_fields=["l2_feedback", "status"])

        gift = assign_gift_card(survey.user)
        send_gift_card_email(survey.user.email, gift.code)

        AppraisalRecord.objects.create(
            user=survey.user,
            answers=survey.answers,
            l1_feedback=survey.l1_feedback,
            l2_feedback=survey.l2_feedback,
            reward_given=True,
            reward_code=gift.code
        )

        return Response({"message": "Survey approved"})
    
class EmployeePDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        surveys = SurveyResponse.objects.filter(user=request.user)

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        y = 800

        p.setFont("Helvetica", 10)
        p.drawString(50, y, f"Employee: {request.user.full_name}")
        y -= 30

        for survey in surveys:
            p.drawString(50, y, f"Survey ID: {survey.id}")
            y -= 20

            for q_id, answer in survey.answers.items():
                p.drawString(70, y, f"Q{q_id}: {answer}")
                y -= 15

            if survey.l1_feedback:
                p.drawString(70, y, f"L1 Feedback: {survey.l1_feedback}")
                y -= 15

            if survey.l2_feedback:
                p.drawString(70, y, f"L2 Feedback: {survey.l2_feedback}")
                y -= 15

            p.drawString(70, y, f"Status: {survey.status}")
            y -= 30

            if y < 100:
                p.showPage()
                y = 800

        p.save()
        buffer.seek(0)

        return HttpResponse(
            buffer,
            content_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=employee_surveys.pdf"}
        )


class L1SurveyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, survey_id):
        if not (request.user.role in ["L1_MANAGER", "ADMIN"] or request.user.is_superuser):
            return Response({"error": "Not authorized"}, status=403)

        survey = SurveyResponse.objects.get(id=survey_id)

        return Response({
            "survey_id": survey.id,
            "employee": survey.user.full_name,
            "department": survey.user.department,
            "answers": survey.answers,
            "l1_feedback": survey.l1_feedback,
            "status": survey.status
        })


class L2SurveyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, survey_id):
        if not (request.user.role in ["L2_MANAGER", "ADMIN"] or request.user.is_superuser):
            return Response({"error": "Not authorized"}, status=403)

        survey = SurveyResponse.objects.get(id=survey_id)

        return Response({
            "survey_id": survey.id,
            "employee": survey.user.full_name,
            "department": survey.user.department,
            "answers": survey.answers,
            "l1_feedback": survey.l1_feedback,
            "l2_feedback": survey.l2_feedback,
            "status": survey.status
        })
