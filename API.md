# K-LIMS API 문서

베이스 URL: `http://localhost:8000` (로컬) / `https://<domain>` (Vercel)

> Swagger UI: `http://localhost:8000/docs`

---

## 목차

- [대시보드](#대시보드)
- [고객 관리](#고객-관리)
- [직원 관리](#직원-관리)
- [시험 의뢰](#시험-의뢰)
- [의뢰 항목 (시료)](#의뢰-항목-시료)
- [장비 관리](#장비-관리)
- [시험 기록](#시험-기록)
- [전자결재](#전자결재)
- [정산 관리](#정산-관리)
- [감사 추적](#감사-추적)

---

## 대시보드

### `GET /api/dashboard/stats`

6개의 운영 현황 지표를 반환합니다.

**응답 예시**
```json
{
  "total_orders": 42,
  "in_progress": 8,
  "pending_approval": 3,
  "completed_today": 2,
  "equipment_due_calibration": 1,
  "total_customers": 15
}
```

---

### `GET /api/dashboard/recent-orders`

최근 의뢰 목록을 반환합니다.

**응답 예시**
```json
[
  {
    "id": 1,
    "order_no": "KOLAS-2026-001",
    "customer_name": "(주)한국전자",
    "status": "시험중",
    "order_date": "2026-04-01"
  }
]
```

---

## 고객 관리

### `GET /api/customers`

고객 목록 조회. `?search=` 쿼리 파라미터로 검색 가능.

### `POST /api/customers`

**요청 바디**
```json
{
  "name": "(주)한국전자",
  "business_no": "123-45-67890",
  "contact_name": "홍길동",
  "contact_email": "hong@example.com",
  "contact_phone": "010-1234-5678",
  "address": "서울시 강남구"
}
```

### `GET /api/customers/{customer_id}`

특정 고객 상세 조회.

### `PUT /api/customers/{customer_id}`

고객 정보 수정.

### `DELETE /api/customers/{customer_id}`

고객 소프트 삭제 (`is_deleted = true`).

---

## 직원 관리

### `GET /api/staff`

전체 직원 목록 조회.

### `POST /api/staff`

**요청 바디**
```json
{
  "name": "김시험",
  "employee_no": "EMP006",
  "role": "시험원",
  "email": "kim@lab.co.kr"
}
```

가능한 `role` 값: `관리자`, `시험원`, `검토자`, `승인자`, `접수담당`

---

## 시험 의뢰

### `GET /api/orders`

의뢰 목록 조회. `?status=` 로 상태 필터링 가능.

| status 값 | 설명 |
|-----------|------|
| `접수` | 접수 완료, 시험 전 |
| `시험중` | 시험 진행 중 |
| `검토중` | 결과 검토 중 |
| `완료` | 성적서 발행 완료 |
| `취소` | 취소 처리 |

### `POST /api/orders`

**요청 바디**
```json
{
  "customer_id": 1,
  "requested_due_date": "2026-04-30",
  "notes": "긴급 처리 요청"
}
```

`order_no`는 서버에서 자동 생성됩니다 (`KOLAS-2026-NNN`).

### `GET /api/orders/{order_id}`

의뢰 상세 + 시료 항목 포함 조회.

### `PUT /api/orders/{order_id}`

의뢰 정보 수정.

---

## 의뢰 항목 (시료)

### `POST /api/orders/{order_id}/items`

시료 추가. `sample_id_code` 자동 생성 (`S-XXXXXXXX`).

**요청 바디**
```json
{
  "sample_name": "PCB 기판",
  "test_standard": "KS C IEC 60664-1",
  "quantity": 3,
  "unit_price": 150000
}
```

### `GET /api/orders/{order_id}/items`

특정 의뢰의 시료 목록 조회.

---

## 장비 관리

### `GET /api/equipment`

전체 장비 목록 조회.

### `POST /api/equipment`

**요청 바디**
```json
{
  "model_name": "디지털 멀티미터 DMM-5000",
  "serial_no": "SN-20240101-001",
  "manufacturer": "Keysight",
  "calibration_date": "2026-12-31",
  "next_calibration_date": "2027-12-31",
  "location": "시험실 A",
  "status": "정상"
}
```

가능한 `status` 값: `정상`, `교정중`, `고장`

### `PUT /api/equipment/{equipment_id}`

장비 정보 수정.

### `DELETE /api/equipment/{equipment_id}`

장비 소프트 삭제.

---

## 시험 기록

### `GET /api/test-records`

최근 50개 시험 기록 조회.

### `POST /api/test-records`

시험 기록 생성. 교정 유효성 검사 포함 — 만료된 장비 사용 시 `HTTP 400` 반환.

**요청 바디**
```json
{
  "order_item_id": 1,
  "equipment_id": 1,
  "staff_id": 2,
  "raw_data": 1250.5,
  "uncertainty": 12.5,
  "unit": "MΩ",
  "env_cond": "23°C, 50% RH",
  "result": "합격",
  "calculation_note": "기준치 ≥ 1000 MΩ",
  "start_date": "2026-04-03T09:00:00",
  "end_date": "2026-04-03T11:00:00"
}
```

### `GET /api/test-records/{record_id}`

특정 시험 기록 상세 조회.

### `PUT /api/test-records/{record_id}`

시험 기록 수정. `is_locked = true`인 경우 `HTTP 400` 반환.  
수정 시 `reason` 필드 필수 (Audit Trail 기록).

**요청 바디**
```json
{
  "raw_data": 1280.0,
  "reason": "재측정 결과 반영"
}
```

---

## 전자결재

### `GET /api/approvals`

전체 결재 이력 조회.

### `GET /api/approvals/pending`

미결재 건수 조회.

**응답 예시**
```json
{ "pending_count": 3 }
```

### `POST /api/approvals`

결재 처리. 최종 승인 시 자동으로:
1. `TEST_RECORD.is_locked = True`
2. `TEST_ORDER.status = "완료"`
3. `TEST_REPORT` 자동 생성

**요청 바디**
```json
{
  "test_record_id": 1,
  "staff_id": 4,
  "step": "승인",
  "action": "승인",
  "comment": "이상 없음, 승인합니다."
}
```

| step 값 | 설명 |
|---------|------|
| `계약` | 접수 담당자의 계약 검토 승인 |
| `검토` | 검토자의 데이터 검토 |
| `승인` | 승인자의 최종 성적서 승인 |

| action 값 | 설명 |
|-----------|------|
| `승인` | 해당 단계 승인 |
| `반려` | 반려 (comment 필수) |
| `대기` | 결재 대기 상태 |

---

## 정산 관리

### `GET /api/billing`

전체 정산 목록 조회.

### `POST /api/billing`

정산 등록.

**요청 바디**
```json
{
  "test_order_id": 1,
  "total_amount": 450000,
  "paid_amount": 450000,
  "payment_method": "Transfer",
  "payment_date": "2026-04-03",
  "is_paid": true,
  "invoice_no": "INV-2026-001",
  "tax_invoice_issued": true
}
```

가능한 `payment_method` 값: `Cash`, `Card`, `Transfer`

### `PUT /api/billing/{billing_id}`

정산 정보 수정 (수납 처리 등).

---

## 감사 추적

### `GET /api/audit-logs`

감사 로그 조회. `?record_id=` 로 특정 시험 기록의 이력만 조회 가능.

**응답 예시**
```json
[
  {
    "id": 1,
    "test_record_id": 1,
    "table_name": "test_records",
    "field_name": "raw_data",
    "old_value": "1250.5",
    "new_value": "1280.0",
    "reason": "재측정 결과 반영",
    "changed_by": "이시험",
    "changed_at": "2026-04-03T14:30:00"
  }
]
```

---

## 공통 응답 코드

| 코드 | 의미 |
|------|------|
| `200` | 성공 |
| `201` | 생성 성공 |
| `400` | 잘못된 요청 (교정 만료, 잠긴 레코드 등) |
| `404` | 리소스 없음 |
| `422` | 유효성 검사 실패 |
| `500` | 서버 내부 오류 |
