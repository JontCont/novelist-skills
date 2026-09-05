from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path


SUPPORTED_LOCALES = ("zh-Hant", "zh-Hans", "ja", "en")
SKILL_CONTEXT = {"protocol": "novelist-sdd", "version": 1}
LOCALE_ALIASES = {
    "zh-hant": "zh-Hant",
    "zh-tw": "zh-Hant",
    "zh-hk": "zh-Hant",
    "zh-hans": "zh-Hans",
    "zh-cn": "zh-Hans",
    "zh-sg": "zh-Hans",
    "ja": "ja",
    "ja-jp": "ja",
    "en": "en",
    "en-us": "en",
    "en-gb": "en",
}
LOCALE_LABELS = {
    "zh-Hant": ("Traditional Chinese", "Traditional Chinese characters"),
    "zh-Hans": ("Simplified Chinese", "Simplified Chinese characters"),
    "ja": ("Japanese", "Japanese orthography"),
    "en": ("English", "English orthography"),
}
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u3400-\u9fff\u3040-\u30ff]+")
CJK_PATTERN = re.compile(r"[\u3400-\u9fff\u3040-\u30ff]+")


def normalize_locale(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("content_locale must be a string")
    locale = LOCALE_ALIASES.get(value.strip().lower())
    if locale is None:
        raise ValueError(f"unsupported locale: {value}; choose {', '.join(SUPPORTED_LOCALES)}")
    return locale


def default_config(locale: str) -> dict:
    normalized = normalize_locale(locale)
    return {
        "schema_version": 1,
        "skill_context": SKILL_CONTEXT.copy(),
        "content_locale": normalized,
        "retrieval": {
            "normalization": "NFKC",
            "tokenizer": "cjk-bigram" if normalized != "en" else "word",
            "stopwords": [],
            "term_aliases": {},
        },
    }


def load_config(project: Path) -> dict:
    path = project / ".novelist/config.json"
    if not path.is_file():
        return default_config("zh-Hant")
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("locale configuration must be an object")
    if config.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    if config.get("skill_context") != SKILL_CONTEXT:
        raise ValueError("skill_context marker is missing or incompatible")
    locale = normalize_locale(config.get("content_locale", "zh-Hant"))
    retrieval = config.get("retrieval", {})
    if not isinstance(retrieval, dict):
        raise ValueError("retrieval must be an object")
    merged = default_config(locale)
    merged["retrieval"].update(retrieval)
    merged["content_locale"] = locale
    validate_retrieval(merged["retrieval"])
    return merged


def validate_retrieval(retrieval: dict) -> None:
    if retrieval.get("normalization") not in {"NFC", "NFKC"}:
        raise ValueError("retrieval normalization must be NFC or NFKC")
    if retrieval.get("tokenizer") not in {"cjk-bigram", "word"}:
        raise ValueError("retrieval tokenizer must be cjk-bigram or word")
    stopwords = retrieval.get("stopwords")
    if not isinstance(stopwords, list) or not all(isinstance(value, str) for value in stopwords):
        raise ValueError("retrieval stopwords must be an array of strings")
    aliases = retrieval.get("term_aliases")
    if not isinstance(aliases, dict) or not all(
        isinstance(canonical, str)
        and canonical
        and isinstance(values, list)
        and all(isinstance(value, str) and value for value in values)
        for canonical, values in aliases.items()
    ):
        raise ValueError("retrieval term_aliases must map terms to arrays of strings")


def locale_description(locale: str) -> tuple[str, str]:
    return LOCALE_LABELS[normalize_locale(locale)]


def normalize_text(text: str, form: str = "NFKC") -> str:
    if form not in {"NFC", "NFKC"}:
        raise ValueError("retrieval normalization must be NFC or NFKC")
    return unicodedata.normalize(form, text).casefold()


def basic_tokens(text: str, tokenizer: str, normalization: str) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_PATTERN.findall(normalize_text(text, normalization)):
        if tokenizer == "cjk-bigram" and CJK_PATTERN.fullmatch(match):
            tokens.extend(
                [match] if len(match) == 1 else [match[index : index + 2] for index in range(len(match) - 1)]
            )
        else:
            tokens.append(match)
    return tokens


def tokenize(text: str, config: dict) -> list[str]:
    locale = normalize_locale(config.get("content_locale", "zh-Hant"))
    retrieval = config.get("retrieval", {})
    normalization = retrieval.get("normalization", "NFKC")
    tokenizer = retrieval.get("tokenizer", "word" if locale == "en" else "cjk-bigram")
    normalized = normalize_text(text, normalization)
    expansion: list[str] = []
    for canonical, aliases in retrieval.get("term_aliases", {}).items():
        terms = [canonical, *aliases]
        if any(normalize_text(term, normalization) in normalized for term in terms):
            expansion.extend(terms)
    tokens = basic_tokens(" ".join([text, *expansion]), tokenizer, normalization)
    stopwords = {
        token
        for value in retrieval.get("stopwords", [])
        for token in basic_tokens(value, tokenizer, normalization)
    }
    return [token for token in tokens if token not in stopwords]
