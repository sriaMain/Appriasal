from rest_framework import serializers
from .models import User, SurveyResponse, SurveyQuestion, Department


class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "full_name",
            "department",
            "designation",
            "password",
            "confirm_password",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_department(self, value):
        if not Department.objects.filter(name=value).exists():
            raise serializers.ValidationError("Invalid department selected.")
        return value



    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("confirm_password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        if user.role == "EMPLOYEE":
            l1 = User.objects.filter(
                role="L1_MANAGER",
                department=user.department,
                is_active=True
            ).first()
            
            l2 = User.objects.filter(
                role="L2_MANAGER",
                department=user.department,
                is_active=True
            ).first()

            if l1:
                user.l1_manager = l1
            if l2:
                user.l2_manager = l2
            
            if l1 or l2:
                user.save()

        return user



class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)


class SurveySerializer(serializers.Serializer):
    answers = serializers.JSONField()


class GiftCardBulkSerializer(serializers.Serializer):
    codes = serializers.ListField(child=serializers.CharField())


class EmployeeSurveySerializer(serializers.ModelSerializer):
    survey_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = SurveyResponse
        fields = [
            "survey_id",
            "answers",
            "l1_feedback",
            "l2_feedback",
            "status",
        ]


class SurveyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyQuestion
        fields = [
            "id",
            "text",
            "question_type",
            "rating_min",
            "rating_max",
            "order",
            "is_active",
        ]
