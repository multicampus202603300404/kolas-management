from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, Text, create_engine
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    business_no = Column(String(20), unique=True)
    contact_name = Column(String(100))
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    address = Column(Text)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_orders = relationship("TestOrder", back_populates="customer")


class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    employee_no = Column(String(50), unique=True)
    role = Column(String(50))  # 관리자 / 시험원 / 검토자 / 승인자 / 접수담당
    email = Column(String(200))
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_records = relationship("TestRecord", back_populates="staff")
    approval_logs = relationship("ApprovalLog", back_populates="staff")
    audit_logs = relationship("AuditLog", back_populates="changed_by_staff")


class TestOrder(Base):
    __tablename__ = "test_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    requested_due_date = Column(DateTime)
    status = Column(String(20), default="접수")  # 접수 / 시험중 / 검토중 / 완료 / 취소
    notes = Column(Text)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="test_orders")
    order_items = relationship("OrderItem", back_populates="test_order")
    billing = relationship("Billing", back_populates="test_order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    test_order_id = Column(Integer, ForeignKey("test_orders.id"), nullable=False)
    sample_name = Column(String(300), nullable=False)
    sample_id_code = Column(String(50), unique=True)  # QR/바코드 코드
    test_standard = Column(String(200))               # KS/ISO 규격
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_order = relationship("TestOrder", back_populates="order_items")
    test_record = relationship("TestRecord", back_populates="order_item", uselist=False)
    test_reports = relationship("TestReport", back_populates="order_item")


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(200), nullable=False)
    serial_no = Column(String(100))
    manufacturer = Column(String(200))
    calibration_date = Column(DateTime)       # 교정 만료일
    next_calibration_date = Column(DateTime)
    location = Column(String(200))
    status = Column(String(50), default="정상")  # 정상 / 교정중 / 고장
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_records = relationship("TestRecord", back_populates="equipment")


class TestRecord(Base):
    __tablename__ = "test_records"

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    staff_id = Column(Integer, ForeignKey("staff.id"))

    raw_data = Column(Float)        # 측정값
    uncertainty = Column(Float)     # 측정불확도
    unit = Column(String(50))
    env_cond = Column(String(200))  # 온습도 조건
    calculation_note = Column(Text)
    result = Column(String(20))     # 합격 / 불합격

    start_date = Column(DateTime)
    end_date = Column(DateTime)

    is_locked = Column(Boolean, default=False)  # 최종 승인 후 잠금(ReadOnly)
    version_no = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_item = relationship("OrderItem", back_populates="test_record")
    equipment = relationship("Equipment", back_populates="test_records")
    staff = relationship("Staff", back_populates="test_records")
    audit_logs = relationship("AuditLog", back_populates="test_record")
    approval_logs = relationship("ApprovalLog", back_populates="test_record")


class TestReport(Base):
    __tablename__ = "test_reports"

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False)
    report_no = Column(String(100), unique=True)
    version_no = Column(Integer, default=1)
    issued_at = Column(DateTime)
    is_valid = Column(Boolean, default=True)
    invalidated_at = Column(DateTime)
    invalidation_reason = Column(Text)
    is_deleted = Column(Boolean, default=False)

    order_item = relationship("OrderItem", back_populates="test_reports")


class ApprovalLog(Base):
    __tablename__ = "approval_logs"

    id = Column(Integer, primary_key=True, index=True)
    test_record_id = Column(Integer, ForeignKey("test_records.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    step = Column(String(20))    # 계약 / 검토 / 승인
    action = Column(String(20))  # 승인 / 반려 / 대기
    comment = Column(Text)
    signature_hash = Column(String(256))  # 전자서명 해시
    signed_at = Column(DateTime, default=datetime.utcnow)

    test_record = relationship("TestRecord", back_populates="approval_logs")
    staff = relationship("Staff", back_populates="approval_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    test_record_id = Column(Integer, ForeignKey("test_records.id"))
    table_name = Column(String(100))
    record_id = Column(Integer)
    field_name = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    reason = Column(Text, nullable=False)  # 수정 사유 필수
    changed_by = Column(Integer, ForeignKey("staff.id"))
    changed_at = Column(DateTime, default=datetime.utcnow)

    test_record = relationship("TestRecord", back_populates="audit_logs")
    changed_by_staff = relationship("Staff", back_populates="audit_logs")


class Billing(Base):
    __tablename__ = "billing"

    id = Column(Integer, primary_key=True, index=True)
    test_order_id = Column(Integer, ForeignKey("test_orders.id"), nullable=False)
    total_amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    payment_method = Column(String(50))  # Cash / Card / Transfer
    payment_date = Column(DateTime)
    is_paid = Column(Boolean, default=False)
    invoice_no = Column(String(100))
    tax_invoice_issued = Column(Boolean, default=False)
    notes = Column(Text)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    test_order = relationship("TestOrder", back_populates="billing")
