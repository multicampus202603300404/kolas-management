import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import models
import schemas
from models import (
    AuditLog, ApprovalLog, Billing, Customer, Equipment,
    OrderItem, Staff, TestOrder, TestRecord, TestReport,
)

# ── DB setup ──────────────────────────────────────────────────────────────────
# Vercel 환경은 /tmp 만 쓰기 가능
if os.environ.get("VERCEL"):
    DATABASE_URL = "sqlite:////tmp/kolas.db"
else:
    DATABASE_URL = "sqlite:///./kolas.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="K-LIMS API", version="1.0.0",
              description="KOLAS 인증 기관용 통합 시험 관리 플랫폼")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _gen_order_no(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(TestOrder).filter(
        func.strftime("%Y", TestOrder.order_date) == str(year)
    ).count()
    return f"KOLAS-{year}-{count + 1:03d}"


def _gen_sample_code() -> str:
    return "S-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def _sign(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _record_audit(db: Session, *, test_record_id: int, table_name: str,
                  record_id: int, field_name: str, old_value: str,
                  new_value: str, reason: str, changed_by: Optional[int]):
    log = AuditLog(
        test_record_id=test_record_id,
        table_name=table_name,
        record_id=record_id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        changed_by=changed_by,
    )
    db.add(log)


# ── Seed data ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
def seed():
    db = SessionLocal()
    try:
        if db.query(Staff).count() > 0:
            return  # 이미 초기화됨

        staff_list = [
            Staff(name="김관리", employee_no="EMP001", role="관리자",  email="admin@kolas.kr"),
            Staff(name="이시험", employee_no="EMP002", role="시험원",  email="tester@kolas.kr"),
            Staff(name="박검토", employee_no="EMP003", role="검토자",  email="review@kolas.kr"),
            Staff(name="최승인", employee_no="EMP004", role="승인자",  email="approve@kolas.kr"),
            Staff(name="정접수", employee_no="EMP005", role="접수담당", email="recept@kolas.kr"),
        ]
        db.add_all(staff_list)

        customers = [
            Customer(name="(주)한국전자", business_no="123-45-67890",
                     contact_name="홍길동", contact_phone="010-1234-5678",
                     contact_email="hong@korea.com"),
            Customer(name="삼성전기(주)", business_no="234-56-78901",
                     contact_name="이순신", contact_phone="010-9876-5432",
                     contact_email="lee@samsung.com"),
        ]
        db.add_all(customers)
        db.flush()

        equipment_list = [
            Equipment(model_name="디지털 멀티미터 DMM-5000", serial_no="SN20240001",
                      manufacturer="Keysight", location="시험실 A",
                      calibration_date=datetime.utcnow() + timedelta(days=30),
                      next_calibration_date=datetime.utcnow() + timedelta(days=30)),
            Equipment(model_name="온습도 데이터로거 DL-200", serial_no="SN20240002",
                      manufacturer="Vaisala", location="시험실 B",
                      calibration_date=datetime.utcnow() + timedelta(days=5),
                      next_calibration_date=datetime.utcnow() + timedelta(days=5)),
            Equipment(model_name="LCR 미터 E4980A", serial_no="SN20240003",
                      manufacturer="Agilent", location="시험실 A",
                      calibration_date=datetime.utcnow() + timedelta(days=180),
                      next_calibration_date=datetime.utcnow() + timedelta(days=180)),
        ]
        db.add_all(equipment_list)
        db.flush()

        # 샘플 의뢰
        order = TestOrder(
            order_no="KOLAS-2026-001",
            customer_id=customers[0].id,
            status="시험중",
            order_date=datetime.utcnow() - timedelta(days=2),
            requested_due_date=datetime.utcnow() + timedelta(days=5),
        )
        db.add(order)
        db.flush()

        item = OrderItem(
            test_order_id=order.id,
            sample_name="PCB 기판 절연저항 시험",
            sample_id_code=_gen_sample_code(),
            test_standard="KS C IEC 60664-1",
            unit_price=150000,
        )
        db.add(item)
        db.flush()

        record = TestRecord(
            order_item_id=item.id,
            equipment_id=equipment_list[0].id,
            staff_id=staff_list[1].id,
            raw_data=1250.5,
            uncertainty=12.5,
            unit="MΩ",
            env_cond="온도 23±2℃, 습도 50±5%RH",
            result="합격",
            start_date=datetime.utcnow() - timedelta(hours=3),
        )
        db.add(record)
        db.flush()

        db.add(Billing(
            test_order_id=order.id,
            total_amount=150000,
            invoice_no=f"INV-2026-001",
        ))

        db.commit()
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/dashboard/stats", response_model=schemas.DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    warn_date = datetime.utcnow() + timedelta(days=30)

    total_orders = db.query(TestOrder).filter(TestOrder.is_deleted == False).count()
    orders_in_progress = db.query(TestOrder).filter(
        TestOrder.is_deleted == False,
        TestOrder.status.in_(["접수", "시험중", "검토중"])
    ).count()
    pending_approvals = db.query(ApprovalLog).filter(
        ApprovalLog.action == "대기"
    ).count()
    expiring_equipment = db.query(Equipment).filter(
        Equipment.is_deleted == False,
        Equipment.calibration_date <= warn_date,
        Equipment.calibration_date >= datetime.utcnow(),
    ).count()
    completed_today = db.query(TestOrder).filter(
        TestOrder.is_deleted == False,
        TestOrder.status == "완료",
        func.date(TestOrder.updated_at) == str(today),
    ).count()
    unpaid_billing = db.query(Billing).filter(
        Billing.is_deleted == False,
        Billing.is_paid == False,
    ).count()

    return schemas.DashboardStats(
        total_orders=total_orders,
        orders_in_progress=orders_in_progress,
        pending_approvals=pending_approvals,
        expiring_equipment=expiring_equipment,
        completed_today=completed_today,
        unpaid_billing=unpaid_billing,
    )


@app.get("/api/dashboard/recent-orders")
def get_recent_orders(db: Session = Depends(get_db)):
    orders = (
        db.query(TestOrder)
        .filter(TestOrder.is_deleted == False)
        .order_by(TestOrder.created_at.desc())
        .limit(10)
        .all()
    )
    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "order_no": o.order_no,
            "customer_name": o.customer.name if o.customer else "",
            "status": o.status,
            "order_date": o.order_date.isoformat() if o.order_date else None,
            "requested_due_date": o.requested_due_date.isoformat() if o.requested_due_date else None,
            "item_count": len([i for i in o.order_items if not i.is_deleted]),
        })
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Customers
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/customers", response_model=List[schemas.CustomerOut])
def list_customers(search: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Customer).filter(Customer.is_deleted == False)
    if search:
        q = q.filter(Customer.name.contains(search))
    return q.order_by(Customer.created_at.desc()).all()


@app.post("/api/customers", response_model=schemas.CustomerOut)
def create_customer(body: schemas.CustomerCreate, db: Session = Depends(get_db)):
    c = Customer(**body.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@app.get("/api/customers/{cid}", response_model=schemas.CustomerOut)
def get_customer(cid: int, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == cid, Customer.is_deleted == False).first()
    if not c:
        raise HTTPException(404, "고객을 찾을 수 없습니다.")
    return c


@app.put("/api/customers/{cid}", response_model=schemas.CustomerOut)
def update_customer(cid: int, body: schemas.CustomerCreate, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == cid, Customer.is_deleted == False).first()
    if not c:
        raise HTTPException(404, "고객을 찾을 수 없습니다.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return c


@app.delete("/api/customers/{cid}")
def delete_customer(cid: int, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == cid).first()
    if not c:
        raise HTTPException(404)
    c.is_deleted = True
    db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Staff
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/staff", response_model=List[schemas.StaffOut])
def list_staff(db: Session = Depends(get_db)):
    return db.query(Staff).filter(Staff.is_deleted == False).order_by(Staff.id).all()


@app.post("/api/staff", response_model=schemas.StaffOut)
def create_staff(body: schemas.StaffCreate, db: Session = Depends(get_db)):
    s = Staff(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ═══════════════════════════════════════════════════════════════════════════════
# TestOrders
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/orders", response_model=List[schemas.TestOrderOut])
def list_orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(TestOrder).filter(TestOrder.is_deleted == False)
    if status:
        q = q.filter(TestOrder.status == status)
    orders = q.order_by(TestOrder.created_at.desc()).all()
    result = []
    for o in orders:
        d = schemas.TestOrderOut.model_validate(o)
        d.customer_name = o.customer.name if o.customer else None
        result.append(d)
    return result


@app.post("/api/orders", response_model=schemas.TestOrderOut)
def create_order(body: schemas.TestOrderCreate, db: Session = Depends(get_db)):
    cust = db.query(Customer).filter(Customer.id == body.customer_id).first()
    if not cust:
        raise HTTPException(404, "고객을 찾을 수 없습니다.")
    order = TestOrder(
        order_no=_gen_order_no(db),
        **body.model_dump(),
    )
    db.add(order)
    db.flush()

    # 정산 레코드 자동 생성
    billing = Billing(test_order_id=order.id)
    db.add(billing)

    db.commit()
    db.refresh(order)
    d = schemas.TestOrderOut.model_validate(order)
    d.customer_name = cust.name
    return d


@app.get("/api/orders/{oid}")
def get_order(oid: int, db: Session = Depends(get_db)):
    o = db.query(TestOrder).filter(TestOrder.id == oid, TestOrder.is_deleted == False).first()
    if not o:
        raise HTTPException(404)
    items = []
    for item in o.order_items:
        if item.is_deleted:
            continue
        rec = None
        if item.test_record:
            r = item.test_record
            rec = {
                "id": r.id,
                "raw_data": r.raw_data,
                "uncertainty": r.uncertainty,
                "unit": r.unit,
                "result": r.result,
                "is_locked": r.is_locked,
                "staff_name": r.staff.name if r.staff else None,
                "equipment_name": r.equipment.model_name if r.equipment else None,
            }
        items.append({
            "id": item.id,
            "sample_name": item.sample_name,
            "sample_id_code": item.sample_id_code,
            "test_standard": item.test_standard,
            "unit_price": item.unit_price,
            "test_record": rec,
        })
    return {
        "id": o.id,
        "order_no": o.order_no,
        "customer_name": o.customer.name if o.customer else None,
        "customer_id": o.customer_id,
        "order_date": o.order_date,
        "requested_due_date": o.requested_due_date,
        "status": o.status,
        "notes": o.notes,
        "items": items,
    }


@app.put("/api/orders/{oid}", response_model=schemas.TestOrderOut)
def update_order(oid: int, body: schemas.TestOrderUpdate, db: Session = Depends(get_db)):
    o = db.query(TestOrder).filter(TestOrder.id == oid, TestOrder.is_deleted == False).first()
    if not o:
        raise HTTPException(404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(o, k, v)
    db.commit()
    db.refresh(o)
    d = schemas.TestOrderOut.model_validate(o)
    d.customer_name = o.customer.name if o.customer else None
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# OrderItems
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/orders/{oid}/items", response_model=schemas.OrderItemOut)
def add_item(oid: int, body: schemas.OrderItemCreate, db: Session = Depends(get_db)):
    o = db.query(TestOrder).filter(TestOrder.id == oid).first()
    if not o:
        raise HTTPException(404)
    item = OrderItem(
        test_order_id=oid,
        sample_id_code=_gen_sample_code(),
        **body.model_dump(),
    )
    db.add(item)
    # 정산 금액 갱신
    if o.billing:
        o.billing.total_amount += body.unit_price * body.quantity
    db.commit()
    db.refresh(item)
    return item


@app.get("/api/orders/{oid}/items", response_model=List[schemas.OrderItemOut])
def list_items(oid: int, db: Session = Depends(get_db)):
    return db.query(OrderItem).filter(
        OrderItem.test_order_id == oid,
        OrderItem.is_deleted == False,
    ).all()


# ═══════════════════════════════════════════════════════════════════════════════
# Equipment
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/equipment", response_model=List[schemas.EquipmentOut])
def list_equipment(db: Session = Depends(get_db)):
    return db.query(Equipment).filter(Equipment.is_deleted == False).order_by(Equipment.id).all()


@app.post("/api/equipment", response_model=schemas.EquipmentOut)
def create_equipment(body: schemas.EquipmentCreate, db: Session = Depends(get_db)):
    eq = Equipment(**body.model_dump())
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq


@app.put("/api/equipment/{eid}", response_model=schemas.EquipmentOut)
def update_equipment(eid: int, body: schemas.EquipmentUpdate, db: Session = Depends(get_db)):
    eq = db.query(Equipment).filter(Equipment.id == eid, Equipment.is_deleted == False).first()
    if not eq:
        raise HTTPException(404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(eq, k, v)
    db.commit()
    db.refresh(eq)
    return eq


@app.delete("/api/equipment/{eid}")
def delete_equipment(eid: int, db: Session = Depends(get_db)):
    eq = db.query(Equipment).filter(Equipment.id == eid).first()
    if not eq:
        raise HTTPException(404)
    eq.is_deleted = True
    db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# TestRecords
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/test-records", response_model=List[schemas.TestRecordOut])
def list_records(db: Session = Depends(get_db)):
    records = db.query(TestRecord).filter(TestRecord.is_deleted == False)\
        .order_by(TestRecord.created_at.desc()).limit(50).all()
    result = []
    for r in records:
        d = schemas.TestRecordOut.model_validate(r)
        d.staff_name = r.staff.name if r.staff else None
        d.equipment_name = r.equipment.model_name if r.equipment else None
        result.append(d)
    return result


@app.post("/api/test-records", response_model=schemas.TestRecordOut)
def create_record(body: schemas.TestRecordCreate, db: Session = Depends(get_db)):
    # 장비 교정 유효성 검사
    if body.equipment_id:
        eq = db.query(Equipment).filter(Equipment.id == body.equipment_id).first()
        if eq and eq.calibration_date and eq.calibration_date < datetime.utcnow():
            raise HTTPException(400, f"장비 '{eq.model_name}'의 교정 기간이 만료되었습니다.")

    record = TestRecord(**body.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    d = schemas.TestRecordOut.model_validate(record)
    d.staff_name = record.staff.name if record.staff else None
    d.equipment_name = record.equipment.model_name if record.equipment else None
    return d


@app.put("/api/test-records/{rid}", response_model=schemas.TestRecordOut)
def update_record(rid: int, body: schemas.TestRecordUpdate, db: Session = Depends(get_db)):
    r = db.query(TestRecord).filter(TestRecord.id == rid, TestRecord.is_deleted == False).first()
    if not r:
        raise HTTPException(404)
    if r.is_locked:
        raise HTTPException(400, "최종 승인된 시험 기록은 수정할 수 없습니다.")

    update_fields = body.model_dump(exclude={"reason"}, exclude_unset=True)
    for field, new_val in update_fields.items():
        old_val = getattr(r, field, None)
        if old_val != new_val:
            _record_audit(
                db,
                test_record_id=rid,
                table_name="test_records",
                record_id=rid,
                field_name=field,
                old_value=str(old_val),
                new_value=str(new_val),
                reason=body.reason,
                changed_by=None,
            )
            setattr(r, field, new_val)

    r.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(r)
    d = schemas.TestRecordOut.model_validate(r)
    d.staff_name = r.staff.name if r.staff else None
    d.equipment_name = r.equipment.model_name if r.equipment else None
    return d


@app.get("/api/test-records/{rid}", response_model=schemas.TestRecordOut)
def get_record(rid: int, db: Session = Depends(get_db)):
    r = db.query(TestRecord).filter(TestRecord.id == rid, TestRecord.is_deleted == False).first()
    if not r:
        raise HTTPException(404)
    d = schemas.TestRecordOut.model_validate(r)
    d.staff_name = r.staff.name if r.staff else None
    d.equipment_name = r.equipment.model_name if r.equipment else None
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# Approvals
# ═══════════════════════════════════════════════════════════════════════════════
APPROVAL_STEPS = ["계약", "검토", "승인"]


@app.get("/api/approvals", response_model=List[schemas.ApprovalOut])
def list_approvals(db: Session = Depends(get_db)):
    logs = db.query(ApprovalLog).order_by(ApprovalLog.signed_at.desc()).limit(100).all()
    result = []
    for a in logs:
        d = schemas.ApprovalOut.model_validate(a)
        d.staff_name = a.staff.name if a.staff else None
        result.append(d)
    return result


@app.get("/api/approvals/pending")
def list_pending(db: Session = Depends(get_db)):
    rows = db.query(ApprovalLog).filter(ApprovalLog.action == "대기")\
        .order_by(ApprovalLog.signed_at.asc()).all()
    result = []
    for a in rows:
        result.append({
            "id": a.id,
            "test_record_id": a.test_record_id,
            "step": a.step,
            "staff_name": a.staff.name if a.staff else None,
            "signed_at": a.signed_at.isoformat(),
        })
    return result


@app.post("/api/approvals", response_model=schemas.ApprovalOut)
def submit_approval(body: schemas.ApprovalCreate, db: Session = Depends(get_db)):
    record = db.query(TestRecord).filter(TestRecord.id == body.test_record_id).first()
    if not record:
        raise HTTPException(404, "시험 기록을 찾을 수 없습니다.")
    staff = db.query(Staff).filter(Staff.id == body.staff_id).first()
    if not staff:
        raise HTTPException(404, "직원을 찾을 수 없습니다.")

    sig_data = f"{body.test_record_id}:{body.staff_id}:{body.step}:{datetime.utcnow().isoformat()}"
    log = ApprovalLog(
        test_record_id=body.test_record_id,
        staff_id=body.staff_id,
        step=body.step,
        action=body.action,
        comment=body.comment,
        signature_hash=_sign(sig_data),
    )
    db.add(log)

    # 최종 승인(승인 단계) 시 → 레코드 잠금
    if body.step == "승인" and body.action == "승인":
        record.is_locked = True
        # 의뢰 상태 완료로 변경
        item = db.query(OrderItem).filter(OrderItem.id == record.order_item_id).first()
        if item:
            order = db.query(TestOrder).filter(TestOrder.id == item.test_order_id).first()
            if order:
                order.status = "완료"
                order.updated_at = datetime.utcnow()
        # 성적서 자동 발행
        report_no = f"RPT-{datetime.utcnow().year}-{random.randint(10000, 99999)}"
        rpt = TestReport(
            order_item_id=record.order_item_id,
            report_no=report_no,
            version_no=1,
            issued_at=datetime.utcnow(),
        )
        db.add(rpt)

    db.commit()
    db.refresh(log)
    d = schemas.ApprovalOut.model_validate(log)
    d.staff_name = staff.name
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# Billing
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/billing", response_model=List[schemas.BillingOut])
def list_billing(db: Session = Depends(get_db)):
    bills = db.query(Billing).filter(Billing.is_deleted == False)\
        .order_by(Billing.created_at.desc()).all()
    result = []
    for b in bills:
        d = schemas.BillingOut.model_validate(b)
        if b.test_order:
            d.order_no = b.test_order.order_no
            d.customer_name = b.test_order.customer.name if b.test_order.customer else None
        result.append(d)
    return result


@app.post("/api/billing", response_model=schemas.BillingOut)
def create_billing(body: schemas.BillingCreate, db: Session = Depends(get_db)):
    b = Billing(**body.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    d = schemas.BillingOut.model_validate(b)
    if b.test_order:
        d.order_no = b.test_order.order_no
        d.customer_name = b.test_order.customer.name if b.test_order.customer else None
    return d


@app.put("/api/billing/{bid}", response_model=schemas.BillingOut)
def update_billing(bid: int, body: schemas.BillingUpdate, db: Session = Depends(get_db)):
    b = db.query(Billing).filter(Billing.id == bid, Billing.is_deleted == False).first()
    if not b:
        raise HTTPException(404)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    db.commit()
    db.refresh(b)
    d = schemas.BillingOut.model_validate(b)
    if b.test_order:
        d.order_no = b.test_order.order_no
        d.customer_name = b.test_order.customer.name if b.test_order.customer else None
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# Audit Logs
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/audit-logs", response_model=List[schemas.AuditLogOut])
def list_audit_logs(record_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(AuditLog)
    if record_id:
        q = q.filter(AuditLog.test_record_id == record_id)
    logs = q.order_by(AuditLog.changed_at.desc()).limit(200).all()
    result = []
    for a in logs:
        d = schemas.AuditLogOut.model_validate(a)
        d.changed_by_name = a.changed_by_staff.name if a.changed_by_staff else None
        result.append(d)
    return result
