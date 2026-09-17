"""Provider boundaries keep paid/cloud replacements out of the clinical workflow."""
from dataclasses import dataclass


@dataclass
class ASRResult:
    transcript: str
    language: str
    confidence: float


class MockASRProvider:
    def transcribe(self, _audio: bytes, language: str) -> ASRResult:
        text = "मुझे दो दिन से बुखार है" if language == "hi" else "I have had fever for two days"
        return ASRResult(transcript=text, language=language, confidence=0.9)


class MockTTSProvider:
    def synthesize(self, text: str, language: str) -> dict:
        return {"provider": "mock", "language": language, "text": text, "audio_available": False}


class MockLLMProvider:
    def summarize(self, factual_prompt: str) -> str:
        return factual_prompt


class MockHISAdapter:
    def send(self, fhir_bundle: dict) -> dict:
        return {"status": "SUCCESS", "adapter": "mock-his", "resource_count": len(fhir_bundle.get("entry", []))}


class MockABDMAdapter:
    def send(self, fhir_bundle: dict) -> dict:
        return {"status": "SUCCESS", "adapter": "mock-abdm", "resource_count": len(fhir_bundle.get("entry", []))}
