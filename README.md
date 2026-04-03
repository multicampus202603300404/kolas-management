# K-LIMS — KOLAS 통합 시험 관리 플랫폼

> **K-LIMS** (KOLAS Laboratory Information Management System) — KOLAS 인증 시험소를 위한 통합 웹 기반 LIMS

시험 의뢰 접수부터 성적서 발행, 수수료 정산, 전자결재까지 전 과정을 전자화하고 **ISO/IEC 17025** 표준 준수를 보장합니다.

---

## 주요 기능

| 모듈 | 설명 |
|------|------|
| **대시보드** | 전체 진행 현황, 미결재 건수, 교정 만료 장비 알림 |
| **고객 관리** | 고객사 정보 등록·조회·수정 (soft delete) |
| **의뢰 관리** | 의뢰 번호 자동 생성 (`KOLAS-YYYY-NNN`), 시료 바코드 발급 |
| **시험 기록** | 측정값·불확도·환경 조건 입력, 기준치 합격/불합격 자동 판정 |
| **전자결재** | 3단계 결재(계약 → 검토 → 승인), 디지털 서명 (SHA-256) |
| **장비 관리** | 교정 만료일 검증 — 만료 장비 시험 기록 생성 차단 |
| **정산 관리** | 청구·수납·세금계산서 발행 현황 추적 |
| **감사 추적** | 모든 수정에 대한 Audit Trail (수정 전·후·사유·담당자) |

---

## 기술 스택

```
Backend   FastAPI 0.115 · SQLAlchemy 2.0 · Pydantic 2.9 · SQLite · Uvicorn
Frontend  Vanilla HTML5 / CSS3 / JavaScript (의존성 없음)
Deploy    Vercel (서버리스) / 로컬 개발 환경
```

---

## 시작하기

### 사전 요건
- Python 3.10 이상

### 설치 및 실행

```bash
# 저장소 복제
git clone https://github.com/multicampus202603300404/kolas-management.git
cd kolas-management

# 의존성 설치
pip install -r backend/requirements.txt

# 서버 실행
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Windows에서는 프로젝트 루트의 `run.bat`를 실행해도 됩니다.

브라우저에서 `frontend/index.html`을 열거나, `http://localhost:8000`으로 접속하세요.

**API 문서:** `http://localhost:8000/docs` (Swagger UI 자동 생성)

---

## 프로젝트 구조

```
kolas-management/
├── backend/
│   ├── main.py          # FastAPI 엔드포인트 (37개)
│   ├── models.py        # SQLAlchemy ORM 모델 (10개 테이블)
│   ├── schemas.py       # Pydantic 요청/응답 스키마
│   └── requirements.txt
├── frontend/
│   └── index.html       # 싱글 페이지 애플리케이션
├── api/
│   └── index.py         # Vercel 서버리스 진입점
├── vercel.json          # Vercel 배포 설정
└── run.bat              # Windows 빠른 실행 스크립트
```

---

## 데이터베이스 스키마

```
CUSTOMER ──< TEST_ORDER ──< ORDER_ITEM ──< TEST_RECORD >── EQUIPMENT
                  │                │            │
                  └── BILLING      └── TEST_REPORT
                                        TEST_RECORD >── APPROVAL_LOG
                                        TEST_RECORD >── AUDIT_LOG
                                        STAFF ─────>    TEST_RECORD
                                        STAFF ─────>    APPROVAL_LOG
```

> 상세 ERD는 [ERD.md](./ERD.md)를 참조하세요.

---

## 시험 처리 흐름

```
고객 의뢰
   ↓
[접수 담당] 시료 확인 → 결재 1: 계약 승인
   ↓
[시험원] 시험 수행, Raw Data 입력
   ↓
[검토자] 시험 기록서 검토 → 결재 2: 데이터 검토
   ↓
[승인자] 최종 승인 → 결재 3: 성적서 발행 (자동)
   ↓
정산 처리 → 세금계산서 발행
```

---

## KOLAS 17025 준수 사항

| 요건 | 구현 방법 |
|------|----------|
| 감사 추적 (Audit Trail) | `AUDIT_LOG` 테이블 — 모든 수정에 사유 필수 |
| 데이터 무결성 | 최종 승인 후 `is_locked = True` (읽기 전용) |
| 디지털 서명 | SHA-256 `signature_hash` |
| 이력 추적성 | Soft Delete + `version_no` — 물리 삭제 없음 |
| 교정 관리 | 장비 `calibration_date` 검증, 만료 시 기록 차단 |
| 성적서 관리 | 자동 발행 + 버전 관리 + 무효화 프로세스 |

---

## Vercel 배포

```bash
# Vercel CLI 설치 후
vercel --prod
```

`vercel.json`에서 라우팅을 설정합니다:
- `/api/*` → FastAPI (서버리스 함수)
- `/*` → `frontend/index.html` (SPA)

---

## 초기 샘플 데이터

서버 최초 실행 시 다음 데이터가 자동으로 생성됩니다:

| 항목 | 내용 |
|------|------|
| 직원 | 김관리(관리자), 이시험(시험원), 박검토(검토자), 최승인(승인자), 정접수(접수담당) |
| 고객 | (주)한국전자, 삼성전기(주) |
| 장비 | Keysight DMM-5000, Vaisala DL-200, Agilent E4980A |
| 샘플 의뢰 | KOLAS-2026-001 (PCB 기판 절연저항 시험) |

---

## 문서

- [PRD.md](./PRD.md) — 제품 요구사항 명세서
- [ERD.md](./ERD.md) — 데이터베이스 설계 및 ERD
- [API.md](./API.md) — API 엔드포인트 전체 목록

---

## 라이선스

본 프로젝트는 교육 목적으로 제작되었습니다.
