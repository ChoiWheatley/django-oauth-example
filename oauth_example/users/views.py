import json
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
import requests


@require_http_methods(["GET"])
def get_kakao_auth_url(req):
    """
    client가 카카오 auth 서버로 리다이렉트를 해준다.
    """
    auth_url = settings.KAKAO_AUTH_URL
    client_id = settings.KAKAO_CLIENT_ID
    redirect_uri = settings.KAKAO_REDIRECT_URL
    kakao_auth_url = (
        f"{auth_url}?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
    )
    return redirect(kakao_auth_url)


@require_http_methods(["GET"])
def kakao_redirect(req):
    """
    카카오 로그인시 redirect uri로 GET 요청을 하며, 이때 query param으로 `code`가 포함됩니다.
    [kakao developers](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#request-code-response) 참고
    """
    error = req.GET.get("error")
    if error:
        raise PermissionDenied(req.GET.get("error_description"))

    code = req.GET.get("code")  # 카카오 인증서버가 준 인가코드
    token_response = requests.post(  # 카카오 인가서버가 준 액세스, 리프레시 토큰
        settings.KAKAO_TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
        data={
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": settings.KAKAO_REDIRECT_URL,
            "code": code,
            "client_secret": settings.KAKAO_CLIENT_SECRET,
        },
        timeout=10,
    )

    if token_response.status_code != status.HTTP_200_OK:
        return HttpResponse(
            f"카카오 토큰 받기 실패 💀 {token_response.content}",
            status=500,
        )

    # 응답으로부터 액세스 토큰 가져오기
    access_token = token_response.json()["access_token"]

    # 액세스 토큰으로 사용자 정보 가져오기 [참고](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api#req-user-info)
    profile_response = requests.get(
        settings.KAKAO_PROFILE_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        timeout=10,
    )

    if profile_response.status_code != status.HTTP_200_OK:
        return HttpResponse(
            "카카오 프로필 받기 실패 💀",
            status=500,
        )

    user_profile = profile_response.json()

    print(json.dumps(user_profile))

    response = HttpResponse(user_profile, status=status.HTTP_200_OK)

    return response
