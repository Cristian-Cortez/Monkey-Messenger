import json

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.core.files.base import ContentFile

import os
import base64
from io import BytesIO
from PIL import Image

from .models import Monkey_Message

#-----------------------------------------------------------------------------
# verifying matching secret API key
#-----------------------------------------------------------------------------
def authorized(request):
    return (
        request.headers.get("X-API-Key")
        == settings.MESSAGE_API_KEY
    )

#-----------------------------------------------------------------------------
# helper to process uploaded image:
# 1. Compress & downscale file for web/disk storage (Max 320x240 JPEG)
# 2. Convert to 64x64 RGB565 Base64 string for ESP32 avatar
# 3. thank you gemini for this
#-----------------------------------------------------------------------------
def process_image(image_file, max_size=(320, 240), avatar_size=(64, 64), quality=70):
    image_file.seek(0)
    
    with Image.open(image_file) as img:
        # Convert RGBA / Palette mode images to standard RGB for JPEG output
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        else:
            img = img.convert("RGB")

        # Generate 64x64 RGB565 Base64 for ESP32 ---
        avatar = img.resize(avatar_size, Image.Resampling.LANCZOS).convert('RGB')
        raw_bytes = bytearray()

        # avatar.getdata() iterates flat in C-level memory (under 5ms for 64x64)
        for r, g, b in avatar.getdata():
            rgb565 = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            raw_bytes.append((rgb565 >> 8) & 0xFF)
            raw_bytes.append(rgb565 & 0xFF)
                
        image_base64 = base64.b64encode(raw_bytes).decode('utf-8')

        # --- 2. Compress & Downscale JPEG for Server Storage ---
        compressed_img = img.copy()
        compressed_img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        buffer = BytesIO()
        compressed_img.save(buffer, format="JPEG", quality=quality, optimize=True)
        
        # Ensure file extension ends with .jpg
        orig_name = image_file.name if hasattr(image_file, 'name') else "image.jpg"
        base_name = os.path.splitext(orig_name)[0]
        filename = f"{base_name}.jpg"

        compressed_file = ContentFile(buffer.getvalue(), name=filename)

    return compressed_file, image_base64

#-----------------------------------------------------------------------------
# POST to create a monkey message
#-----------------------------------------------------------------------------
@csrf_exempt
def create_message(request):

    # enure only POST
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # check key
    if not authorized(request):
        return JsonResponse({"error": "Unauthorized"}, status=401)

    text = ""
    image_file = None
    compressed_file = None
    image_base64 = None

    # handle file uploads (multipart/form-data)
    if request.content_type and "multipart/form-data" in request.content_type:
        text = request.POST.get("text", "").strip()
        image_file = request.FILES.get("image")
    else:
        # standard JSON with no image
        try:
            data = json.loads(request.body)
            text = data.get("text", "").strip()
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    # must have text or image
    if not text and not image_file:
        return JsonResponse({"error": "Message text or image is required"}, status=400)

    if len(text) > 1000:
        return JsonResponse({"error": "Message must be 1000 characters or fewer"}, status=400)

    # Process image if provided
    if image_file:
        try:
            compressed_file, image_base64 = process_image(image_file)
        except Exception as e:
            return JsonResponse({"error": f"Invalid image file: {str(e)}"}, status=400)

    # Create message record
    message = Monkey_Message.objects.create(
        text=text,
        image=compressed_file,
        image_base64=image_base64
    )

    image_url = request.build_absolute_uri(message.image.url) if message.image else None

    return JsonResponse({
        "id": message.id,
        "text": message.text,
        "image_url": image_url,
        "has_image": bool(message.image_base64),
        "created_at": message.created_at.isoformat(),
    }, status=201)

#-----------------------------------------------------------------------------
# GET to recieve latest message in the db
#-----------------------------------------------------------------------------
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

    # query db to get highest id (maybe not needed anymore?)
    message = Monkey_Message.objects.order_by("-id").first()

    # if db is empty return None
    if message is None:
        return JsonResponse({
            "id": None, 
            "text": None,
            "image_base64": None,
            "image_url": None,
        })

    image_url = request.build_absolute_uri(message.image.url) if message.image else None

    return JsonResponse(
        {
            "id": message.id,
            "text": message.text,
            "image_base64": message.image_base64,  # Used directly by ESP32
            "image_url": image_url,                # Optional for web client
            "created_at": message.created_at.isoformat(),
        }
    )

#-----------------------------------------------------------------------------
# GET to recieve latest 50 messages in the db
#-----------------------------------------------------------------------------
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

    # query limits by 50 and orders latest to top
    messages = Monkey_Message.objects.order_by("-id")[:50]

    return JsonResponse({
        "messages": [
            {
                "id": message.id,
                "text": message.text,
                "created_at": message.created_at.isoformat(),
                "image_url": request.build_absolute_uri(message.image.url) if message.image else None,
                "created_at": message.created_at.isoformat(),
            }
            for message in messages
        ]
    })

#-----------------------------------------------------------------------------
# base view to render index page
#-----------------------------------------------------------------------------
def index_ui(request):
    return render(request, "monkey_messages/index.html")