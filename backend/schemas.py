from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Customer ──────────────────────────────────────────────────────────────────
class CustomerCreate(BaseModel):
    name: str
    business_no: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None


class CustomerOut(CustomerCreate):
    id: int
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Staff ─────────────────────────────────────────────────────────────────────
class StaffCreate(BaseModel):
    name: str
    employee_no: str
    role: str   # 관리자 / 시험원 / 검토자 / 승인자 / 접수담당
    email: Optional[str] = None


class StaffOut(StaffCreate):
    id: int
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── TestOrder ─────────────────────────────────────────────────────────────────
class TestOrderCreate(BaseModel):
    customer_id: int
    requested_due_date: Optional[datetime] = None
    notes: Optional[str] = None


class TestOrderUpdate(BaseModel):
    status: Optional[str] = None
    requested_due_date: Optional[datetime] = None
    notes: Optional[str] = None


class TestOrderOut(BaseModel):
    id: int
    order_no: str
    customer_id: int
    customer_name: Optional[str] = None
    order_date: datetime
    requested_due_date: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── OrderItem ─────────────────────────────────────────────────────────────────
class OrderItemCreate(BaseModel):
    sample_name: str
    test_standard: Optional[str] = None
    quantity: int = 1
    unit_price: float = 0


class OrderItemOut(OrderItemCreate):
    id: int
    test_order_id: int
    sample_id_code: Optional[str] = None
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Equipment ─────────────────────────────────────────────────────────────────
class EquipmentCreate(BaseModel):
    model_name: str
    serial_no: Optional[str] = None
    manufacturer: Optional[str] = None
    calibration_date: Optional[datetime] = None
    next_calibration_date: Optional[datetime] = None
    location: Optional[str] = None
    status: str = "정상"


class EquipmentUpdate(BaseModel):
    model_name: Optional[str] = None
    serial_no: Optional[str] = None
    manufacturer: Optional[str] = None
    calibration_date: Optional[datetime] = None
    next_calibration_date: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = None


class EquipmentOut(EquipmentCreate):
    id: int
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── TestRecord ────────────────────────────────────────────────────────────────
class TestRecordCreate(BaseModel):
    order_item_id: int
    equipment_id: Optional[int] = None
    staff_id: Optional[int] = None
    raw_data: Optional[float] = None
    uncertainty: Optional[float] = None
    unit: Optional[str] = None
    env_cond: Optional[str] = None
    calculation_note: Optional[str] = None
    result: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TestRecordUpdate(BaseModel):
    equipment_id: Optional[int] = None
    raw_data: Optional[float] = None
    uncertainty: Optional[float] = None
    unit: Optional[str] = None
    env_cond: Optional[str] = None
    calculation_note: Optional[str] = None
    result: Optional[str] = None
    end_date: Optional[datetime] = None
    reason: str  # 수정 사유 필수


class TestRecordOut(BaseModel):
    id: int
    order_item_id: int
    equipment_id: Optional[int] = None
    staff_id: Optional[int] = None
    staff_name: Optional[str] = None
    equipment_name: Optional[str] = None
    raw_data: Optional[float] = None
    uncertainty: Optional[float] = None
    unit: Optional[str] = None
    env_cond: Optional[str] = None
    calculation_note: Optional[str] = None
    result: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_locked: bool
    version_no: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── ApprovalLog ───────────────────────────────────────────────────────────────
class ApprovalCreate(BaseModel):
    test_record_id: int
    staff_id: int
    step: str    # 계약 / 검토 / 승인
    action: str  # 승인 / 반려
    comment: Optional[str] = None


class ApprovalOut(BaseModel):
    id: int
    test_record_id: int
    staff_id: int
    staff_name: Optional[str] = None
    step: str
    action: str
    comment: Optional[str] = None
    signature_hash: Optional[str] = None
    signed_at: datetime

    class Config:
        from_attributes = True


# ── AuditLog ──────────────────────────────────────────────────────────────────
class AuditLogOut(BaseModel):
    id: int
    test_record_id: Optional[int] = None
    table_name: Optional[str] = None
    record_id: Optional[int] = None
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: str
    changed_by: Optional[int] = None
    changed_by_name: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True


# ── Billing ───────────────────────────────────────────────────────────────────
class BillingCreate(BaseModel):
    test_order_id: int
    total_amount: float = 0
    notes: Optional[str] = None


class BillingUpdate(BaseModel):
    paid_amount: Optional[float] = None
    payment_method: Optional[str] = None
    payment_date: Optional[datetime] = None
    is_paid: Optional[bool] = None
    invoice_no: Optional[str] = None
    tax_invoice_issued: Optional[bool] = None
    notes: Optional[str] = None


class BillingOut(BillingCreate):
    id: int
    order_no: Optional[str] = None
    customer_name: Optional[str] = None
    paid_amount: float
    payment_method: Optional[str] = None
    payment_date: Optional[datetime] = None
    is_paid: bool
    invoice_no: Optional[str] = None
    tax_invoice_issued: bool
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_orders: int
    orders_in_progress: int
    pending_approvals: int
    expiring_equipment: int
    completed_today: int
    unpaid_billing: int
