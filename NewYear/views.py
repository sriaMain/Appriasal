from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.http import HttpResponse

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO

from .models import (
    User,
    SurveyQuestion,
    SurveyResponse,
    GiftCard,
    EmployeeProfile,
    AppraisalRecord,
)

from .serializers import (
    RegisterSerializer,
    SurveySerializer,
    SurveyQuestionSerializer,
    ListSerializer,
)

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


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "User registered successfully",
                "data": RegisterSerializer(user).data
            },
            status=201
        )

    def get(self, request):
        users = User.objects.all()
        serializer = ListSerializer(users, many=True)
        return Response({"users": serializer.data})


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
                "role": user.role
            }
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"message": "Logged out successfully"})


class SurveyQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questions = SurveyQuestion.objects.filter(is_active=True).order_by("order")
        serializer = SurveyQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin can add survey questions"}, status=403)

        data = request.data
        serializer = (
            SurveyQuestionSerializer(data=data, many=True)
            if isinstance(data, list)
            else SurveyQuestionSerializer(data=data)
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Survey question(s) added successfully"}, status=201)

    def put(self, request, question_id=None):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin can update survey questions"}, status=403)

        if not question_id:
            return Response({"error": "question_id is required"}, status=400)

        try:
            question = SurveyQuestion.objects.get(id=question_id)
        except SurveyQuestion.DoesNotExist:
            return Response({"error": "Question not found"}, status=404)

        serializer = SurveyQuestionSerializer(question, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "Survey question updated successfully", "data": serializer.data})

    def delete(self, request, question_id=None):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin can delete survey questions"}, status=403)

        if not question_id:
            return Response({"error": "question_id is required"}, status=400)

        try:
            question = SurveyQuestion.objects.get(id=question_id)
        except SurveyQuestion.DoesNotExist:
            return Response({"error": "Question not found"}, status=404)

        question.is_active = False
        question.save(update_fields=["is_active"])

        return Response({"message": "Survey question deleted successfully"})


class SurveySubmitView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        if request.user.role != "EMPLOYEE":
            return Response(
                {"error": "Only employees are allowed to submit the survey"},
                status=403
            )

        if SurveyResponse.objects.filter(user=request.user).exists():
            return Response(
                {"error": "You have already submitted the survey"},
                status=400
            )

        serializer = SurveySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        survey = SurveyResponse.objects.create(
            user=request.user,
            answers=serializer.validated_data["answers"],
            status="APPROVED"
        )

        gift_card = GiftCard.objects.select_for_update().filter(is_used=False).first()
        if not gift_card:
            raise ValidationError("No gift cards available")

        gift_card.is_used = True
        gift_card.assigned_to = request.user
        gift_card.assigned_at = timezone.now()
        gift_card.save()

       
        send_gift_card_email(
            request.user.email,
            gift_card.code,
            request.user.username
        )

        AppraisalRecord.objects.create(
            user=request.user,
            answers=survey.answers,
            reward_given=True,
            reward_code=gift_card.code
        )

        profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)
        profile.total_surveys += 1
        profile.total_rewards += 1
        profile.save()

        return Response(
            {
                "message": "Survey submitted successfully. Gift card sent.",
                "survey_id": survey.id
            },
            status=201
        )


class EmployeeSurveyStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        surveys = SurveyResponse.objects.filter(user=request.user)
        return Response([
            {
                "survey_id": s.id,
                "answers": s.answers,
                "status": s.status,
                "submitted_at": s.created_at
            }
            for s in surveys
        ])


class GiftCardBulkCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can add gift cards"},
                status=status.HTTP_403_FORBIDDEN
            )

        codes = request.data
        if not isinstance(codes, list) or not codes:
            return Response(
                {"error": "Request body must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        GiftCard.objects.bulk_create(
            [GiftCard(code=c) for c in codes],
            ignore_conflicts=True
        )

        return Response(
            {"message": "Gift cards added successfully"},
            status=status.HTTP_201_CREATED
        )

    
    def get(self, request):
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can view gift cards"},
                status=status.HTTP_403_FORBIDDEN
            )

        gift_cards = GiftCard.objects.all().order_by("-id")
        total = gift_cards.count()
        used = gift_cards.filter(is_used=True).count()

        return Response({
            "stats": {
                "total": total,
                "used": used,
                "remaining": total - used
            },
            "gift_cards": [
                {
                    "id": g.id,
                    "code": g.code,
                    "is_used": g.is_used,
                    "assigned_to": g.assigned_to.username if g.assigned_to else None,
                    "assigned_at": g.assigned_at
                }
                for g in gift_cards
            ]
        }, status=status.HTTP_200_OK)

    def put(self, request, giftcard_id=None):
        if request.user.role != "ADMIN":
            return Response({"error": "Only admin can update gift cards"}, status=403)

        if not giftcard_id:
            return Response({"error": "giftcard_id is required"}, status=400)

        new_code = request.data.get("code")
        if not new_code:
            return Response({"error": "New code is required"}, status=400)

        try:
            gift_card = GiftCard.objects.get(id=giftcard_id)
        except GiftCard.DoesNotExist:
            return Response({"error": "Gift card not found"}, status=404)

        if gift_card.is_used:
            return Response({"error": "Used gift cards cannot be updated"}, status=400)

        gift_card.code = new_code
        gift_card.save(update_fields=["code"])

        return Response({"message": "Gift card updated successfully"}, status=200)


    def delete(self, request, giftcard_id=None):
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can delete gift cards"},
                status=status.HTTP_403_FORBIDDEN
            )

        ids = request.data.get("ids")

        if not isinstance(ids, list) or not ids:
            return Response(
                {"error": "ids must be a non-empty list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        gift_cards = GiftCard.objects.filter(id__in=ids)

        if gift_cards.count() != len(ids):
            return Response(
                {"error": "One or more gift cards not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        if gift_cards.filter(is_used=True).exists():
            return Response(
                {"error": "Used gift cards cannot be deleted"},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count = gift_cards.count()
        gift_cards.delete()

        return Response(
            {
                "message": f"{deleted_count} gift cards deleted successfully"
            },
            status=status.HTTP_200_OK
        )

class EmployeePDFView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        surveys = SurveyResponse.objects.filter(user=request.user)

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        y = 800

        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, f"Employee: {request.user.username}")
        y -= 30

        for survey in surveys:
            pdf.drawString(50, y, f"Survey ID: {survey.id}")
            y -= 20

            for q_id, ans in survey.answers.items():
                pdf.drawString(70, y, f"Q{q_id}: {ans}")
                y -= 15

            pdf.drawString(70, y, f"Status: {survey.status}")
            y -= 30

            if y < 100:
                pdf.showPage()
                y = 800

        pdf.save()
        buffer.seek(0)

        return HttpResponse(
            buffer,
            content_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=employee_surveys.pdf"}
        )


class AdminSurveyResponsesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "ADMIN":
            return Response(
                {"error": "Only admin can view survey responses"},
                status=status.HTTP_403_FORBIDDEN
            )

        surveys = SurveyResponse.objects.select_related("user").order_by("-created_at")

        data = [
            {
                "survey_id": s.id,
                "employee": {
                    "username": s.user.username,
                    "email": s.user.email,
                },
                "answers": s.answers,
                "status": s.status,
                "submitted_at": s.created_at,
            }
            for s in surveys
        ]

        return Response(data, status=status.HTTP_200_OK)