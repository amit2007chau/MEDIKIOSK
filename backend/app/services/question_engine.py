from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Question:
    id: str
    category: str
    en: str
    hi: str
    input_type: str = "choice_or_text"
    required: bool = True
    options: tuple[str, ...] = ()


QUESTIONS: dict[str, Question] = {
    "chief_complaint": Question("chief_complaint", "complaint", "What is your main problem today?", "आज आपकी मुख्य समस्या क्या है?", options=("Fever", "Cough", "Chest pain", "Breathlessness", "Headache", "Abdominal pain", "Vomiting", "Diarrhea", "General complaint")),
    "fever_duration": Question("fever_duration", "symptoms", "When did the fever start?", "बुखार कब शुरू हुआ?"),
    "fever_temperature": Question("fever_temperature", "symptoms", "Did you measure your temperature?", "क्या आपने अपना तापमान मापा?", options=("Yes", "No")),
    "fever_chills": Question("fever_chills", "symptoms", "Do you have chills?", "क्या आपको ठंड लग रही है?", options=("Yes", "No")),
    "cough_duration": Question("cough_duration", "symptoms", "How long have you had the cough?", "आपको खांसी कब से है?"),
    "cough_sputum": Question("cough_sputum", "symptoms", "Are you bringing up phlegm?", "क्या खांसी के साथ बलगम आ रहा है?", options=("Yes", "No")),
    "chest_duration": Question("chest_duration", "symptoms", "When did the chest pain start?", "सीने में दर्द कब शुरू हुआ?"),
    "chest_severity": Question("chest_severity", "symptoms", "How severe is the pain (0 to 10)?", "दर्द कितना गंभीर है (0 से 10)?", options=("Mild", "Moderate", "Severe")),
    "breathing_difficulty": Question("breathing_difficulty", "symptoms", "Are you having difficulty breathing?", "क्या आपको सांस लेने में कठिनाई हो रही है?", options=("No", "Mild", "Severe")),
    "headache_duration": Question("headache_duration", "symptoms", "When did the headache start?", "सिरदर्द कब शुरू हुआ?"),
    "abdominal_duration": Question("abdominal_duration", "symptoms", "When did the abdominal pain start?", "पेट दर्द कब शुरू हुआ?"),
    "vomiting_frequency": Question("vomiting_frequency", "symptoms", "How often have you vomited?", "आपको कितनी बार उल्टी हुई?"),
    "diarrhea_frequency": Question("diarrhea_frequency", "symptoms", "How often have you had loose motions?", "आपको कितनी बार दस्त हुए?"),
    "medical_history": Question("medical_history", "history", "Do you have any past medical conditions?", "क्या आपको पहले से कोई बीमारी है?"),
    "allergies": Question("allergies", "history", "Do you have any allergies?", "क्या आपको कोई एलर्जी है?"),
}

FLOWS = {
    "fever": ["fever_duration", "fever_temperature", "fever_chills", "breathing_difficulty"],
    "cough": ["cough_duration", "cough_sputum", "breathing_difficulty"],
    "chest pain": ["chest_duration", "chest_severity", "breathing_difficulty"],
    "breathlessness": ["breathing_difficulty"],
    "headache": ["headache_duration"],
    "abdominal pain": ["abdominal_duration"],
    "vomiting": ["vomiting_frequency"],
    "diarrhea": ["diarrhea_frequency"],
    "general complaint": [],
}
TAIL = ["medical_history", "allergies"]


def serialize(question: Question, language: str) -> dict:
    return {"id": question.id, "category": question.category, "question": question.hi if language == "hi" else question.en, "input_type": question.input_type, "required": question.required, "options": list(question.options)}


def next_question(answers: dict[str, str], language: str) -> dict | None:
    if "chief_complaint" not in answers:
        return serialize(QUESTIONS["chief_complaint"], language)
    complaint = answers["chief_complaint"].strip().lower()
    path = FLOWS.get(complaint, FLOWS["general complaint"]) + TAIL
    for question_id in path:
        if question_id not in answers:
            return serialize(QUESTIONS[question_id], language)
    return None


def all_question_definitions() -> list[dict]:
    return [asdict(q) for q in QUESTIONS.values()]
