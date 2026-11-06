import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from .models import Monkey_Message


def authorized(request):
    return (
        request.headers.get("X-API-Key")
        == settings.MESSAGE_API_KEY
    )


@csrf_exempt
def create_message(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    if not authorized(request):
        return JsonResponse(
            {"error": "Unauthorized"},
            status=401,
        )

    try:
        data = json.loads(request.body)
        text = data.get("text", "").strip()

        if not text:
            return JsonResponse(
                {"error": "Message cannot be empty"},
                status=400,
            )

        if len(text) > 1000:
            return JsonResponse(
                {"error": "Message must be 1000 characters or fewer"},
                status=400,
            )

        message = Monkey_Message.objects.create(text=text)

        return JsonResponse(
            {
                "id": message.id,
                "text": message.text,
                "created_at": message.created_at.isoformat(),
            },
            status=201,
        )

    except (json.JSONDecodeError, AttributeError):
        return JsonResponse(
            {"error": "Invalid JSON"},
            status=400,
        )


def latest_message(request):
    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    if not authorized(request):
        return JsonResponse(
            {"error": "Unauthorized"},
            status=401,
        )

    message = Monkey_Message.objects.order_by("-id").first()

    if message is None:
        return JsonResponse(
            {"id": None, "text": None},
        )

    return JsonResponse(
        {
            "id": message.id,
            "text": message.text,
            "created_at": message.created_at.isoformat(),
        }
    )

def message_history(request):
    if request.method != "GET":
        return JsonResponse(
            {"error": "Method not allowed"},
            status=405,
        )

    if not authorized(request):
        return JsonResponse(
            {"error": "Unauthorized"},
            status=401,
        )

    messages = Monkey_Message.objects.order_by("-id")[:50]

    return JsonResponse({
        "messages": [
            {
                "id": message.id,
                "text": message.text,
                "created_at": message.created_at.isoformat(),
            }
            for message in messages
        ]
    })

def index_ui(request):
    return render(request, "monkey_messages/index.html")