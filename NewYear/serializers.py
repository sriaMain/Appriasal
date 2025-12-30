from rest_framework import serializers
from .models import (
    User,
    SurveyQuestion,
    SurveyResponse
)


class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "confirm_password"
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        return User.objects.create_user(**validated_data)


class SurveySerializer(serializers.Serializer):
    answers = serializers.JSONField()


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


class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = [
            "id",
            "answers",
            "status",
            "created_at",
        ]


class ListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "is_active"
        ]
