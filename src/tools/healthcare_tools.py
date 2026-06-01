from typing import Dict, List


RED_FLAG_KEYWORDS = {
    "chest pain",
    "đau ngực",
    "shortness of breath",
    "khó thở",
    "difficulty breathing",
    "severe bleeding",
    "chảy máu nặng",
    "unconscious",
    "bất tỉnh",
    "fainting",
    "ngất",
    "stroke",
    "đột quỵ",
    "weakness on one side",
    "yếu một bên",
    "liệt một bên",
    "suicidal",
    "tự tử",
    "seizure",
    "co giật",
    "confusion",
    "lú lẫn",
    "không tỉnh táo",
}

VINMEC_FACILITIES = {
    "hanoi": {
        "name": "Vinmec Times City",
        "city": "Hà Nội",
        "address": "458 Minh Khai, Vĩnh Tuy, Hà Nội",
        "hotline": "024 3974 3556",
    },
    "ha noi": {
        "name": "Vinmec Times City",
        "city": "Hà Nội",
        "address": "458 Minh Khai, Vĩnh Tuy, Hà Nội",
        "hotline": "024 3974 3556",
    },
    "hà nội": {
        "name": "Vinmec Times City",
        "city": "Hà Nội",
        "address": "458 Minh Khai, Vĩnh Tuy, Hà Nội",
        "hotline": "024 3974 3556",
    },
    "ho chi minh": {
        "name": "Vinmec Central Park",
        "city": "TP. Hồ Chí Minh",
        "address": "720A Điện Biên Phủ, TP. Hồ Chí Minh",
        "hotline": "028 3622 1166",
    },
    "hồ chí minh": {
        "name": "Vinmec Central Park",
        "city": "TP. Hồ Chí Minh",
        "address": "720A Điện Biên Phủ, TP. Hồ Chí Minh",
        "hotline": "028 3622 1166",
    },
    "da nang": {
        "name": "Vinmec Đà Nẵng",
        "city": "Đà Nẵng",
        "address": "Đà Nẵng",
        "hotline": "023 6371 1111",
    },
    "đà nẵng": {
        "name": "Vinmec Đà Nẵng",
        "city": "Đà Nẵng",
        "address": "Đà Nẵng",
        "hotline": "023 6371 1111",
    },
    "nha trang": {
        "name": "Vinmec Nha Trang",
        "city": "Nha Trang",
        "address": "Nha Trang",
        "hotline": "025 8390 0168",
    },
    "hai phong": {
        "name": "Vinmec Hải Phòng",
        "city": "Hải Phòng",
        "address": "Hải Phòng",
        "hotline": "022 5730 9888",
    },
    "hải phòng": {
        "name": "Vinmec Hải Phòng",
        "city": "Hải Phòng",
        "address": "Hải Phòng",
        "hotline": "022 5730 9888",
    },
    "ha long": {
        "name": "Vinmec Hạ Long",
        "city": "Hạ Long",
        "address": "Hạ Long",
        "hotline": "020 3382 8188",
    },
    "hạ long": {
        "name": "Vinmec Hạ Long",
        "city": "Hạ Long",
        "address": "Hạ Long",
        "hotline": "020 3382 8188",
    },
    "phu quoc": {
        "name": "Vinmec Phú Quốc",
        "city": "Phú Quốc",
        "address": "Phú Quốc",
        "hotline": "029 7398 5588",
    },
    "phú quốc": {
        "name": "Vinmec Phú Quốc",
        "city": "Phú Quốc",
        "address": "Phú Quốc",
        "hotline": "029 7398 5588",
    },
    "can tho": {
        "name": "Vinmec Cần Thơ",
        "city": "Cần Thơ",
        "address": "Cần Thơ",
        "hotline": "029 2368 3003",
    },
    "cần thơ": {
        "name": "Vinmec Cần Thơ",
        "city": "Cần Thơ",
        "address": "Cần Thơ",
        "hotline": "029 2368 3003",
    },
}

DEFAULT_VINMEC_FACILITY = {
    "name": "Vinmec nearest facility",
    "city": "khu vực gần bạn",
    "address": "Vui lòng kiểm tra cơ sở Vinmec gần nhất trên vinmec.com",
    "hotline": "024 3975 6789",
}

SERVICE_DIRECTORY = {
    "emergency": {
        "service": "Khoa Cấp cứu / Emergency department",
        "message": "Gọi cấp cứu địa phương hoặc đến khoa cấp cứu gần nhất ngay.",
    },
    "urgent": {
        "service": "Khám khẩn trong ngày / Same-day urgent visit",
        "message": "Nên đặt lịch khám trong ngày, đặc biệt nếu triệu chứng tăng lên.",
    },
    "routine": {
        "service": "Khám chuyên khoa hoặc phòng khám đa khoa",
        "message": "Có thể đặt lịch khám không khẩn cấp tại cơ sở Vinmec phù hợp.",
    },
}

VISIT_COSTS_VND = {
    "emergency": 1_500_000,
    "urgent": 600_000,
    "routine": 300_000,
}


def assess_symptom_urgency(symptoms: str, age: int = 0, duration_hours: float = 0) -> str:
    """
    Rule-based educational triage helper. It is not a diagnosis.
    """
    text = symptoms.strip().lower()
    matched_flags = sorted(flag for flag in RED_FLAG_KEYWORDS if flag in text)

    if matched_flags:
        return (
            "Urgency: emergency. Red flags detected: "
            f"{', '.join(matched_flags)}. This is not a diagnosis; the patient should "
            "call local emergency services or go to an emergency department now."
        )

    if int(age) >= 65 or float(duration_hours) >= 72:
        return (
            "Urgency: urgent. No emergency red flag was detected, but age or symptom "
            "duration suggests same-day medical evaluation. This is not a diagnosis."
        )

    return (
        "Urgency: routine. No emergency red flag was detected from the provided text. "
        "Monitor symptoms and book a primary care appointment if symptoms persist. "
        "This is not a diagnosis."
    )


def recommend_care_service(urgency: str, location: str = "local area") -> str:
    level = _normalize_urgency(urgency)
    service = SERVICE_DIRECTORY[level]
    facility = _find_vinmec_facility(location)
    return (
        f"Vinmec navigation for {location}: {service['service']}. "
        f"Suggested facility: {facility['name']} ({facility['city']}). "
        f"Address: {facility['address']}. Hotline: {facility['hotline']}. "
        f"{service['message']} "
        "This is an educational routing suggestion, not an official Vinmec booking confirmation."
    )


def estimate_visit_cost(service_type: str, insurance_status: str = "unknown") -> str:
    level = _normalize_urgency(service_type)
    base_cost = VISIT_COSTS_VND[level]
    insurance = insurance_status.strip().lower()

    if insurance in {"insured", "yes", "covered"}:
        estimated_patient_cost = base_cost * 0.3
    elif insurance in {"none", "uninsured", "no"}:
        estimated_patient_cost = base_cost
    else:
        estimated_patient_cost = base_cost * 0.7

    return (
        f"Estimated Vinmec-style patient cost for {level} care: {estimated_patient_cost:,.0f} VND. "
        "This is a lab planning estimate, not an official Vinmec service fee or hospital quote."
    )


def appointment_preparation(service_type: str) -> str:
    level = _normalize_urgency(service_type)
    if level == "emergency":
        return (
            "Vinmec visit preparation: do not delay care. Bring ID, insurance card if available, "
            "current medication list, allergy list, and recent medical records if easy to access."
        )

    return (
        "Vinmec visit preparation: bring ID, insurance card, current medication list, allergy list, "
        "symptom timeline, and questions for the clinician."
    )


def get_tools() -> List[Dict[str, object]]:
    return [
        {
            "name": "assess_symptom_urgency",
            "description": (
                "Educational triage helper that identifies emergency, urgent, or routine "
                "care level from symptoms. It does not diagnose."
            ),
            "args_schema": 'assess_symptom_urgency(symptoms="chest pain and shortness of breath", age=62, duration_hours=2)',
            "func": assess_symptom_urgency,
        },
        {
            "name": "recommend_care_service",
            "description": "Recommend an appropriate care service from an urgency level and location.",
            "args_schema": 'recommend_care_service(urgency="emergency", location="Hà Nội")',
            "func": recommend_care_service,
        },
        {
            "name": "estimate_visit_cost",
            "description": "Estimate patient cost in VND for emergency, urgent, or routine care.",
            "args_schema": 'estimate_visit_cost(service_type="urgent", insurance_status="insured")',
            "func": estimate_visit_cost,
        },
        {
            "name": "appointment_preparation",
            "description": "List documents and information to prepare for a medical visit.",
            "args_schema": 'appointment_preparation(service_type="routine")',
            "func": appointment_preparation,
        },
    ]


def _normalize_urgency(value: str) -> str:
    text = value.strip().lower()
    if "emergency" in text:
        return "emergency"
    if "urgent" in text or "same-day" in text:
        return "urgent"
    return "routine"


def _find_vinmec_facility(location: str) -> Dict[str, str]:
    text = location.strip().lower()
    for key, facility in VINMEC_FACILITIES.items():
        if key in text:
            return facility
    return DEFAULT_VINMEC_FACILITY
