from django.shortcuts import render
from django.http import JsonResponse

def health_check(request):  # pyright: ignore[reportUnusedParameter]
    return JsonResponse({"status": "ok", "message": "Prompts app is alive"})
