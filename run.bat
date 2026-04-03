@echo off
echo ========================================
echo  K-LIMS - KOLAS 통합 시험 관리 플랫폼
echo ========================================
echo.

cd /d %~dp0backend

echo [1/2] Python 패키지 설치 중...
pip install -r requirements.txt -q

echo.
echo [2/2] 서버 시작 중... (http://localhost:8000)
echo.
echo  - API 문서: http://localhost:8000/docs
echo  - 프론트엔드: frontend/index.html 파일을 브라우저에서 열어주세요
echo.
echo Ctrl+C 로 서버를 종료합니다.
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
