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

SERVICE_DIRECTORY = {
    "emergency": {
        "service": "Emergency department",
        "message": "Call local emergency services or go to the nearest emergency department now.",
    },
    "urgent": {
        "service": "Urgent care clinic",
        "message": "Seek same-day medical care, especially if symptoms are worsening.",
    },
    "routine": {
        "service": "Primary care clinic",
        "message": "Book a non-emergency appointment with a primary care clinician.",
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
    return (
        f"Recommended service for {location}: {service['service']}. "
        f"{service['message']}"
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
        f"Estimated patient cost for {level} care: {estimated_patient_cost:,.0f} VND. "
        "This is a planning estimate, not a hospital quote."
    )


def appointment_preparation(service_type: str) -> str:
    level = _normalize_urgency(service_type)
    if level == "emergency":
        return (
            "Preparation: do not delay care. Bring ID, insurance card if available, "
            "current medication list, allergy list, and recent medical records if easy to access."
        )

    return (
        "Preparation: bring ID, insurance card, current medication list, allergy list, "
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
            "args_schema": 'recommend_care_service(urgency="emergency", location="Hanoi")',
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
