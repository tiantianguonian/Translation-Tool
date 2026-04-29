#!/usr/bin/env python3
"""
translate_multi_language.py — Game Translation Enhanced V3.5

Multi-language game localization pipeline with:
- Placeholder/newline/pipe-field/unit_talk protection
- Text classification (UI/dialogue/skill/quest/system)
- Typed prompt routing
- Dynamic glossary activation + term validation
- 5-dimension quality scoring (format_score as hard gate)
- Reviewer repair loop
- JSONL quality logging
- Cache + resume support

All new features are gated behind feature flags (default OFF).
"""

import json
import os
import re
import hashlib
import time
from typing import Any, Optional

# ============================================================
# Configuration (Feature Flags — all default OFF)
# ============================================================

CONFIG: dict[str, Any] = {
    # Feature toggles
    "ENABLE_TEXT_CLASSIFIER": False,
    "ENABLE_REVIEWER": False,
    "ENABLE_TERM_CHECK": False,

    # Thresholds
    "PASS_SCORE_THRESHOLD": 0.7,
    "REVIEW_SCORE_THRESHOLD": 0.5,
    "MAX_REVIEW_ROUNDS": 3,
    "ACTIVE_TERMS_LIMIT": 20,

    # Risk configuration
    "HIGH_RISK_TYPES": ["system"],

    # Debug
    "DEBUG_TOP_N": 0,

    # Language
    "SOURCE_LANG": "en",
    "TARGET_LANG": "zh-cn",

    # Paths
    "GLOSSARY_PATH": "",
    "QUALITY_LOG_DIR": "production/quality_logs",
    "CACHE_DIR": ".cache",
}

# ============================================================
# Non-negotiables: Structure Protection (existing logic)
# ============================================================

PLACEHOLDER_PATTERNS = [
    re.compile(r'\{\d+\}'),
    re.compile(r'%[sd]'),
    re.compile(r'\{[a-zA-Z_]\w*\}'),
]

UNIT_TALK_PATTERN = re.compile(r'\[unit_talk:[^\]]+\]')


def extract_placeholders(text: str) -> list[str]:
    """Extract all placeholders from text in order."""
    found = []
    for pattern in PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(text):
            found.append((match.start(), match.group()))
    found.sort(key=lambda x: x[0])
    return [f[1] for f in found]


def protect_placeholders(text: str) -> tuple[str, dict[str, str]]:
    """Replace placeholders with safe tokens; return (protected_text, token_map)."""
    token_map = {}
    placeholders = extract_placeholders(text)
    for i, ph in enumerate(placeholders):
        token = f"__PH_{i}__"
        text = text.replace(ph, token, 1)
        token_map[token] = ph
    return text, token_map


def restore_placeholders(text: str, token_map: dict[str, str]) -> str:
    """Restore original placeholders from tokens."""
    for token, original in token_map.items():
        text = text.replace(token, original)
    return text


def protect_newlines(text: str) -> tuple[str, dict[str, str]]:
    """Replace newlines with safe tokens."""
    token_map = {}
    nl_count = text.count('\n')
    for i in range(nl_count):
        token = f"__NL_{i}__"
        text = text.replace('\n', token, 1)
        token_map[token] = '\n'
    return text, token_map


def restore_newlines(text: str, token_map: dict[str, str]) -> str:
    """Restore newlines from tokens."""
    for token, original in token_map.items():
        text = text.replace(token, original)
    return text


def protect_unit_talk(text: str) -> tuple[str, dict[str, str]]:
    """Replace unit_talk tags with safe tokens."""
    token_map = {}
    tags = UNIT_TALK_PATTERN.findall(text)
    for i, tag in enumerate(tags):
        token = f"__UT_{i}__"
        text = text.replace(tag, token, 1)
        token_map[token] = tag
    return text, token_map


def restore_unit_talk(text: str, token_map: dict[str, str]) -> str:
    """Restore unit_talk tags from tokens."""
    for token, original in token_map.items():
        text = text.replace(token, original)
    return text


# ============================================================
# Preprocess & Postprocess (existing logic + enhanced)
# ============================================================

def preprocess(text: str) -> tuple[str, dict, dict, dict]:
    """Protect all non-translatable elements before translation."""
    text, ph_map = protect_placeholders(text)
    text, nl_map = protect_newlines(text)
    text, ut_map = protect_unit_talk(text)
    all_protections = {
        "placeholders": ph_map,
        "newlines": nl_map,
        "unit_talk": ut_map,
    }
    return text, ph_map, nl_map, ut_map


def postprocess(text: str, ph_map: dict, nl_map: dict, ut_map: dict) -> str:
    """Restore all protected elements after translation."""
    text = restore_unit_talk(text, ut_map)
    text = restore_newlines(text, nl_map)
    text = restore_placeholders(text, ph_map)
    return text


# ============================================================
# NEW: Text Classifier (Phase 2.1)
# ============================================================

def classify(text: str) -> dict[str, Any]:
    """
    Classify text type and risk level.
    On failure: return {"text_type": "normal", "risk_level": "low"}.
    """
    try:
        if not CONFIG.get("ENABLE_TEXT_CLASSIFIER", False):
            return {"text_type": "normal", "risk_level": "low"}

        # Heuristic classification based on content patterns
        text_type = _classify_by_patterns(text)
        risk_level = "high" if text_type in CONFIG.get("HIGH_RISK_TYPES", ["system"]) else "low"

        return {"text_type": text_type, "risk_level": risk_level}
    except Exception:
        return {"text_type": "normal", "risk_level": "low"}


def _classify_by_patterns(text: str) -> str:
    """Heuristic text type classification."""
    # Check for unit_talk tags → dialogue
    if UNIT_TALK_PATTERN.search(text):
        return "dialogue"

    # Check for system notification patterns (keyword match → system, no gate)
    if re.search(r'(server|maintenance|error|warning|notice|update|patch)', text, re.IGNORECASE):
        return "system"

    # Check for skill patterns (numbers, percentages, damage, stats)
    if re.search(r'(\{?\d+\}?\s*(%|damage|heal|health|mana|stamina|cooldown|range|effect|duration))', text, re.IGNORECASE):
        return "skill"
    if re.search(r'(Deals?|Restores?|Increases?|Reduces?|Grants?|Applies?)', text, re.IGNORECASE):
        return "skill"

    # Check for quest patterns (objectives, tasks, rewards)
    if re.search(r'(Defeat|Collect|Gather|Deliver|Escort|Rescue|Slay|Investigate|Retrieve|Destroy|Explore|Complete)\s+', text):
        return "quest"
    if re.search(r'Reward:\s*\{?\d+\}?', text, re.IGNORECASE):
        return "quest"

    # Check for dialogue patterns (conversational markers, greetings)
    if re.search(r'(Hello|Hey|Hi|Welcome|Thank|Sorry|Please|Goodbye|Farewell|Yes|No|Maybe|Really|What|Why|How|When|Where)', text, re.IGNORECASE):
        return "dialogue"
    if re.search(r'[.!?]{2,}', text):
        return "dialogue"

    # Check for UI patterns (short, often with || pipes or placeholders)
    if len(text) < 80:
        if '||' in text or re.search(r'\{\d+\}', text):
            return "UI"
        if text.isupper() or re.match(r'^(Start|Exit|Save|Load|Cancel|OK|Back|Next|Settings|Options|Menu)$', text, re.IGNORECASE):
            return "UI"
        return "UI"

    return "normal"


# ============================================================
# NEW: Prompt Router (Phase 2.2)
# ============================================================

# Prompt templates keyed by text_type
PROMPT_TEMPLATES: dict[str, str] = {}

SYSTEM_PREAMBLE = """You are a professional game localizer translating text from {source_lang} to {target_lang}.

CRITICAL RULES:
1. Output ONLY the translated text. Do NOT include explanations, notes, alternatives, or the original text.
2. Preserve ALL placeholders exactly: {{0}}, %s, {{name}}, %d, etc. — do not translate, reorder, or modify them.
3. Preserve ALL newlines and line breaks exactly as they appear in the source.
4. Preserve ALL || pipe-field separators with the exact same number of fields.
5. Preserve ALL unit_talk tags (e.g., [unit_talk:XXX]) exactly as they appear.
6. Do NOT add or remove any formatting characters."""

DEFAULT_PROMPT_TEMPLATES = {
    "UI": """{system_preamble}

This is a UI element. Keep the translation short and clear.
Use standard game UI terminology in {target_lang}.

Source: {source_text}

Translation:""",

    "dialogue": """{system_preamble}

This is character dialogue. Make it sound natural and expressive in {target_lang}.
Preserve the character's voice, tone, and personality.
Maintain conversational flow and emotional content.

Source: {source_text}

Translation:""",

    "skill": """{system_preamble}

This is a skill/ability description. Use precise gameplay terminology in {target_lang}.
Mechanical terms must match the official glossary.
Stats, numbers, and mechanics must remain accurate.

Active glossary terms: {active_terms}

Source: {source_text}

Translation:""",

    "quest": """{system_preamble}

This is quest/mission text. Combine narrative engagement with clear objectives.
Quest objectives and mechanics must be precise and unambiguous.
Numbers, item names, and location names should use glossary terms if available.

Active glossary terms: {active_terms}

Source: {source_text}

Translation:""",

    "system": """{system_preamble}

This is a system message. It must be formal, precise, and consistent.
Use the official game terminology exactly as defined in the glossary.
Error messages must remain clear and actionable.
This is a HIGH-RISK text type — accuracy is critical.

Active glossary terms: {active_terms}

Source: {source_text}

Translation:""",

    "normal": """{system_preamble}

Translate this text accurately into {target_lang}.
Maintain the original meaning, tone, and structure.

Source: {source_text}

Translation:""",
}

REVIEWER_PROMPT_TEMPLATE = """You are a senior game localization reviewer. Fix a draft translation.

CRITICAL RULES:
1. Output ONLY the corrected translation. No explanations.
2. Preserve ALL placeholders, newlines, pipes, and unit_talk tags exactly.
3. Fix ONLY the identified issues. Do NOT rewrite parts that are correct.
4. If the draft is already correct, output the draft translation as-is.

Score breakdown:
- Format: {format_score}
- Term consistency: {term_consistency}
- Fluency: {fluency}
- Completeness: {completeness}
- Style match: {style_match}

Issues identified: {issue_tags}

Source: {source_text}
Draft translation: {draft_translation}

Corrected translation:"""


def _init_prompts():
    """Initialize prompt templates (from design docs if available)."""
    global PROMPT_TEMPLATES
    PROMPT_TEMPLATES = dict(DEFAULT_PROMPT_TEMPLATES)


def build_typed_prompt(source_text: str, text_type: str, active_terms: list[str] | None = None) -> str:
    """Build the appropriate typed prompt for the given text type."""
    if not PROMPT_TEMPLATES:
        _init_prompts()

    template = PROMPT_TEMPLATES.get(text_type, PROMPT_TEMPLATES["normal"])

    system_preamble = SYSTEM_PREAMBLE.format(
        source_lang=CONFIG.get("SOURCE_LANG", "en"),
        target_lang=CONFIG.get("TARGET_LANG", "zh-cn"),
    )

    return template.format(
        system_preamble=system_preamble,
        source_text=source_text,
        target_lang=CONFIG.get("TARGET_LANG", "zh-cn"),
        active_terms=", ".join(active_terms) if active_terms else "none",
    )


def build_reviewer_prompt(source_text: str, draft: str, scores: dict, issue_tags: list[str]) -> str:
    """Build the reviewer repair prompt."""
    return REVIEWER_PROMPT_TEMPLATE.format(
        source_text=source_text,
        draft_translation=draft,
        format_score=scores.get("format_score", 1.0),
        term_consistency=scores.get("term_consistency", 0.0),
        fluency=scores.get("fluency", 0.0),
        completeness=scores.get("completeness", 0.0),
        style_match=scores.get("style_match", 0.0),
        issue_tags=", ".join(issue_tags) if issue_tags else "none",
    )


# ============================================================
# NEW: Glossary Activation (Phase 2.3)
# ============================================================

# In-memory glossary cache
_GLOSSARY: list[dict] = []

# Punctuation boundary characters
_LATIN_BOUNDARY = re.compile(r'[ .,!?;:\"\'()\[\]{}@#$%^&*+=~`<>/\\|\-]')
_PUNCT_CHARS = set(' .,!?;:\'"()[]{}@#$%^&*+=~`<>/\\|-　-〿＀-￯')


def load_glossary(path: str | None = None) -> list[dict]:
    """Load glossary from CSV file. Returns list of term dicts."""
    global _GLOSSARY
    filepath = path or CONFIG.get("GLOSSARY_PATH", "")
    if not filepath or not os.path.exists(filepath):
        _GLOSSARY = []
        return _GLOSSARY

    terms = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) >= 2:
                terms.append({
                    "source": parts[0].strip(),
                    "target": parts[1].strip(),
                    "text_type": parts[2].strip() if len(parts) > 2 else "*",
                    "priority": int(parts[3]) if len(parts) > 3 else 5,
                })
    _GLOSSARY = terms
    return _GLOSSARY


def _is_word_boundary(text: str, pos: int, length: int) -> bool:
    """Check if a match at pos with given length is on word boundaries."""
    # Check left boundary
    if pos > 0:
        char_before = text[pos - 1]
        if not (char_before in _PUNCT_CHARS or char_before.isspace()):
            return False
    # Check right boundary
    if pos + length < len(text):
        char_after = text[pos + length]
        if not (char_after in _PUNCT_CHARS or char_after.isspace()):
            return False
    return True


def extract_active_terms(source_text: str, glossary: list[dict] | None = None) -> list[dict]:
    """
    Extract active terms from source text using longest-match-first.
    Returns list of matching glossary entry dicts, truncated to ACTIVE_TERMS_LIMIT.
    """
    try:
        if not CONFIG.get("ENABLE_TERM_CHECK", False):
            return []

        gl = glossary if glossary is not None else _GLOSSARY
        if not gl:
            return []

        text_lower = source_text.lower()
        matches: list[dict] = []

        for term_entry in gl:
            term_lower = term_entry["source"].lower()
            term_len = len(term_entry["source"])
            start = 0
            while True:
                pos = text_lower.find(term_lower, start)
                if pos == -1:
                    break
                if _is_word_boundary(text_lower, pos, term_len):
                    matches.append({
                        **term_entry,
                        "position": pos,
                        "match_length": term_len,
                    })
                start = pos + 1

        # Sort: longest first, then earliest position
        matches.sort(key=lambda m: (-m["match_length"], m["position"]))

        # Remove overlaps
        selected: list[dict] = []
        occupied: list[tuple[int, int]] = []
        for m in matches:
            m_start = m["position"]
            m_end = m_start + m["match_length"]
            overlap = any(not (m_end <= o_start or m_start >= o_end) for o_start, o_end in occupied)
            if not overlap:
                selected.append(m)
                occupied.append((m_start, m_end))

        # Sort by priority (lower = higher), then length
        selected.sort(key=lambda m: (m.get("priority", 5), -m["match_length"]))

        limit = CONFIG.get("ACTIVE_TERMS_LIMIT", 20)
        return selected[:limit]

    except Exception:
        return []


def validate_terms(translation: str, active_terms: list[dict]) -> tuple[float, list[str]]:
    """
    Validate that active terms appear in translation.
    Returns (term_consistency_score, issue_tags).
    """
    try:
        if not active_terms:
            return 1.0, []

        found = 0
        issue_tags = []

        for term_entry in active_terms:
            target_term = term_entry["target"].lower()
            if target_term in translation.lower():
                found += 1
            else:
                issue_tags.append(f"term_miss:{term_entry['source']}")

        score = found / max(len(active_terms), 1)
        return score, issue_tags

    except Exception:
        return 1.0, []


# ============================================================
# NEW: Quality Scorer (Phase 2.4)
# ============================================================

def score_translation(source: str, translation: str, text_type: str, active_terms: list[dict] | None = None) -> dict:
    """
    Score a translation across 5 dimensions.
    format_score is a hard gate: if 0, final_score = 0 and verdict = REJECT.
    Returns {format_score, term_consistency, fluency, completeness, style_match, final_score, verdict, issue_tags}
    """
    issue_tags: list[str] = []
    active_terms = active_terms or []

    # 1. format_score (HARD GATE)
    format_score, fmt_tags = _score_format(source, translation)
    issue_tags.extend(fmt_tags)

    if format_score == 0:
        return {
            "format_score": 0.0,
            "term_consistency": 0.0,
            "fluency": 0.0,
            "completeness": 0.0,
            "style_match": 0.0,
            "final_score": 0.0,
            "verdict": "REJECT",
            "issue_tags": issue_tags,
        }

    # 2. term_consistency
    term_consistency, term_tags = validate_terms(translation, active_terms)
    issue_tags.extend(term_tags)

    # 3. fluency
    fluency, fluency_tags = _score_fluency(source, translation)
    issue_tags.extend(fluency_tags)

    # 4. completeness
    completeness, comp_tags = _score_completeness(source, translation)
    issue_tags.extend(comp_tags)

    # 5. style_match
    style_match, style_tags = _score_style(translation, text_type)
    issue_tags.extend(style_tags)

    # Composite
    final_score = (term_consistency * 0.25 + fluency * 0.25 + completeness * 0.25 + style_match * 0.25)

    pass_threshold = CONFIG.get("PASS_SCORE_THRESHOLD", 0.7)
    review_threshold = CONFIG.get("REVIEW_SCORE_THRESHOLD", 0.5)

    if final_score >= pass_threshold:
        verdict = "PASS"
    elif final_score >= review_threshold:
        verdict = "REVIEW"
    else:
        verdict = "REVIEW"

    return {
        "format_score": format_score,
        "term_consistency": round(term_consistency, 3),
        "fluency": round(fluency, 3),
        "completeness": round(completeness, 3),
        "style_match": round(style_match, 3),
        "final_score": round(final_score, 3),
        "verdict": verdict,
        "issue_tags": issue_tags,
    }


def _score_format(source: str, translation: str) -> tuple[float, list[str]]:
    """Hard gate: check placeholder/newline/pipe/unit_talk integrity."""
    tags = []

    # Placeholder count
    src_ph = extract_placeholders(source)
    tgt_ph = extract_placeholders(translation)
    if len(src_ph) != len(tgt_ph):
        tags.append("fmt_placeholder")
    elif set(src_ph) != set(tgt_ph):
        tags.append("fmt_placeholder")

    # Newline count
    if source.count('\n') != translation.count('\n'):
        tags.append("fmt_newline")

    # Pipe fields
    src_pipes = source.count('||')
    tgt_pipes = translation.count('||')
    if src_pipes != tgt_pipes:
        tags.append("fmt_pipe")

    # unit_talk tags
    src_ut = UNIT_TALK_PATTERN.findall(source)
    tgt_ut = UNIT_TALK_PATTERN.findall(translation)
    if set(src_ut) != set(tgt_ut):
        tags.append("fmt_unit_talk")

    return (0.0 if tags else 1.0), tags


def _score_fluency(source: str, translation: str) -> tuple[float, list[str]]:
    """Heuristic fluency scoring."""
    tags = []
    checks = []

    # Character ratio sanity (en→zh: 0.3–0.9 is expected)
    ratio = len(translation) / max(len(source), 1)
    target_lang = CONFIG.get("TARGET_LANG", "zh-cn")
    ratio_ranges = {
        "zh-cn": (0.3, 0.9),
        "zh-tw": (0.3, 0.9),
        "ja": (0.4, 1.2),
        "ko": (0.4, 1.0),
        "en": (0.8, 1.5),
    }
    r_min, r_max = ratio_ranges.get(target_lang, (0.3, 2.0))
    if r_min <= ratio <= r_max:
        checks.append(1.0)
    elif ratio < r_min * 0.5 or ratio > r_max * 2:
        checks.append(0.0)
        tags.append("fluency_garbled")
    else:
        checks.append(0.5)

    # Repetition detection
    if _has_suspicious_repetition(translation):
        checks.append(0.0)
        tags.append("fluency_repeat")
    else:
        checks.append(1.0)

    # Target script presence (for CJK targets, expect CJK chars)
    if target_lang in ("zh-cn", "zh-tw", "ja", "ko"):
        cjk_count = sum(1 for c in translation if '一' <= c <= '鿿' or '぀' <= c <= 'ヿ' or '가' <= c <= '힯')
        cjk_ratio = cjk_count / max(len(translation), 1)
        if cjk_ratio < 0.2 and len(source) > 10:
            checks.append(0.3)
            tags.append("fluency_script")
        else:
            checks.append(1.0)

    score = sum(checks) / max(len(checks), 1)
    return score, tags


def _has_suspicious_repetition(text: str) -> bool:
    """Detect garbled output: any character repeated too many times consecutively."""
    if len(text) < 5:
        return False
    count = 1
    for i in range(1, len(text)):
        if text[i] == text[i - 1]:
            count += 1
            if count > 10:
                return True
        else:
            count = 1
    return False


def _score_completeness(source: str, translation: str) -> tuple[float, list[str]]:
    """Heuristic completeness scoring."""
    tags = []
    checks = []

    # Length ratio
    ratio = len(translation) / max(len(source), 1)
    target_lang = CONFIG.get("TARGET_LANG", "zh-cn")
    ratio_ranges = {
        "zh-cn": (0.25, 3.0),
        "zh-tw": (0.25, 3.0),
        "ja": (0.3, 3.0),
        "ko": (0.3, 3.0),
        "en": (0.5, 2.5),
    }
    r_min, r_max = ratio_ranges.get(target_lang, (0.3, 3.0))
    if r_min <= ratio <= r_max:
        checks.append(1.0)
    elif ratio < 0.1:
        checks.append(0.0)
        tags.append("completeness_short")
    else:
        checks.append(0.5)
        tags.append("completeness_short" if ratio < r_min else "completeness_long")

    # Sentence count sanity (approximate)
    src_sentences = max(len(re.split(r'[.!?。！？\n]+', source)), 1)
    tgt_sentences = max(len(re.split(r'[.!?。！？\n]+', translation)), 1)
    sent_ratio = tgt_sentences / max(src_sentences, 1)
    if 0.5 <= sent_ratio <= 2.0:
        checks.append(1.0)
    else:
        checks.append(0.5)
        tags.append("completeness_truncated")

    # Non-empty
    if not translation.strip():
        checks.append(0.0)
        tags.append("completeness_short")
    else:
        checks.append(1.0)

    score = sum(checks) / max(len(checks), 1)
    return score, tags


def _score_style(translation: str, text_type: str) -> tuple[float, list[str]]:
    """Heuristic style scoring by text type."""
    tags = []
    checks = []

    if text_type == "UI":
        # UI should be short, no sentence-ending punctuation
        if len(translation) < 80:
            checks.append(1.0)
        else:
            checks.append(0.5)
            tags.append("style_mismatch")

    elif text_type == "dialogue":
        # Dialogue should feel natural
        if len(translation) > 0:
            checks.append(1.0)
        else:
            checks.append(0.0)

    elif text_type in ("skill", "quest"):
        # Skill/quest should preserve numbers
        src_nums = bool(re.search(r'\d+', translation))
        checks.append(1.0)  # Basic style check; numbers handled by format

    elif text_type == "system":
        # System should be formal, no casual markers
        casual_markers = ['!', '！', '~', '～', 'XD', 'lol', '哈哈', '嘿嘿', '嘛', '吧']
        has_casual = any(m in translation for m in casual_markers)
        if has_casual:
            checks.append(0.5)
            tags.append("style_too_casual")
        else:
            checks.append(1.0)

    else:  # normal
        checks.append(1.0)

    score = sum(checks) / max(len(checks), 1)
    return score, tags


# ============================================================
# NEW: Reviewer Repair Loop (Phase 2.5)
# ============================================================

def review_and_repair(source_text: str, draft: str, scores: dict, issue_tags: list[str]) -> dict | None:
    """
    Run reviewer repair on a draft translation.
    In a real implementation, this calls the LLM with the reviewer prompt.
    Here we provide the framework; the actual LLM call is done by the caller.
    Returns {"translation": reviewed_text, "scores": new_scores} or None on failure.
    """
    try:
        if not CONFIG.get("ENABLE_REVIEWER", False):
            return None

        reviewer_prompt = build_reviewer_prompt(source_text, draft, scores, issue_tags)

        # This is where the LLM call happens in production
        # reviewed = call_llm(reviewer_prompt)
        # For now: return framework structure
        return {
            "prompt": reviewer_prompt,
            "draft": draft,
            "scores": scores,
            "issue_tags": issue_tags,
        }
    except Exception:
        return None


def needs_reviewer(scores: dict, risk_level: str) -> bool:
    """Determine if the translation needs reviewer repair."""
    if not CONFIG.get("ENABLE_REVIEWER", False):
        return False
    if risk_level == "high":
        return True
    if scores.get("verdict") == "REVIEW":
        return True
    if scores.get("format_score", 1.0) == 0:
        return True
    return False


def select_best(draft: str, draft_scores: dict, reviewed: str | None, reviewed_scores: dict | None) -> tuple[str, dict]:
    """Select the best translation between draft and reviewed."""
    if reviewed is None or reviewed_scores is None:
        return draft, draft_scores

    draft_final = draft_scores.get("final_score", 0)
    reviewed_final = reviewed_scores.get("final_score", 0)

    if reviewed_final > draft_final:
        return reviewed, reviewed_scores
    return draft, draft_scores


# ============================================================
# NEW: Quality Logging (Phase 2.6)
# ============================================================

def write_quality_log(sample_id: str, text_type: str, source: str, translation: str,
                      scores: dict, active_terms: list[dict], reviewer_used: bool = False,
                      review_rounds: int = 0) -> str | None:
    """Write one JSONL entry to the quality log. Returns the log path or None."""
    try:
        log_dir = CONFIG.get("QUALITY_LOG_DIR", "production/quality_logs")
        os.makedirs(log_dir, exist_ok=True)

        # Determine log file based on active flag set
        if CONFIG.get("ENABLE_TEXT_CLASSIFIER") or CONFIG.get("ENABLE_REVIEWER") or CONFIG.get("ENABLE_TERM_CHECK"):
            log_file = os.path.join(log_dir, "translation_log.jsonl")
        else:
            log_file = os.path.join(log_dir, "baseline_log.jsonl")

        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sample_id": sample_id,
            "text_type": text_type,
            "source_text": source[:200],
            "translated_text": translation[:200],
            "format_score": scores.get("format_score", 0),
            "term_consistency": scores.get("term_consistency", 0),
            "fluency": scores.get("fluency", 0),
            "completeness": scores.get("completeness", 0),
            "style_match": scores.get("style_match", 0),
            "final_score": scores.get("final_score", 0),
            "verdict": scores.get("verdict", "UNKNOWN"),
            "reviewer_used": reviewer_used,
            "review_rounds": review_rounds,
            "active_terms": [t["source"] for t in active_terms],
            "issue_tags": scores.get("issue_tags", []),
            "config_flags": {
                "ENABLE_TEXT_CLASSIFIER": CONFIG.get("ENABLE_TEXT_CLASSIFIER", False),
                "ENABLE_REVIEWER": CONFIG.get("ENABLE_REVIEWER", False),
                "ENABLE_TERM_CHECK": CONFIG.get("ENABLE_TERM_CHECK", False),
            },
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return log_file
    except Exception:
        return None


# ============================================================
# Cache & Resume (existing logic preserved)
# ============================================================

def _cache_key(text: str, target_lang: str) -> str:
    """Generate a cache key from text and target language."""
    content = f"{text}||{target_lang}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    """Load the translation cache from disk."""
    cache_dir = CONFIG.get("CACHE_DIR", ".cache")
    cache_file = os.path.join(cache_dir, "translation_cache.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache: dict):
    """Save the translation cache to disk."""
    cache_dir = CONFIG.get("CACHE_DIR", ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, "translation_cache.json")
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _lookup_cache(text: str) -> str | None:
    """Look up a cached translation."""
    cache = _load_cache()
    key = _cache_key(text, CONFIG.get("TARGET_LANG", "zh-cn"))
    return cache.get(key)


def _store_cache(text: str, translation: str):
    """Store a translation in the cache."""
    cache = _load_cache()
    key = _cache_key(text, CONFIG.get("TARGET_LANG", "zh-cn"))
    cache[key] = translation
    _save_cache(cache)


# ============================================================
# LLM Call (replace with actual API call in production)
# ============================================================

def call_llm(prompt: str) -> str:
    """
    Call the LLM for translation.
    Replace this with actual API call (Anthropic, OpenAI, etc.).
    Returns the LLM response text.
    """
    # Placeholder: in production, this calls the translation API
    # For now, return a mock that preserves structure
    return f"[LLM_TRANSLATION:{hashlib.md5(prompt.encode()).hexdigest()[:8]}]"


# ============================================================
# Main Translate Pipeline
# ============================================================

def translate(source_text: str, sample_id: str = "", glossary: list[dict] | None = None) -> dict:
    """
    Main translation pipeline — the core translate() function.

    Flow:
    1. Preprocess (protect placeholders, newlines, unit_talk)
    2. Classify text_type + risk_level [flagged]
    3. Extract active_terms [flagged]
    4. Build typed prompt
    5. Call LLM for draft translation
    6. Postprocess (restore protected elements)
    7. Score translation
    8. Reviewer repair loop [flagged]
    9. Select best
    10. Cache result
    11. Write quality log
    """
    result = {
        "source": source_text,
        "translation": "",
        "text_type": "normal",
        "risk_level": "low",
        "scores": {},
        "reviewer_used": False,
        "review_rounds": 0,
    }

    # Step 1: Preprocess
    protected_text, ph_map, nl_map, ut_map = preprocess(source_text)

    # Step 2: Classify
    classification = classify(source_text)
    text_type = classification["text_type"]
    risk_level = classification["risk_level"]
    result["text_type"] = text_type
    result["risk_level"] = risk_level

    # Step 3: Extract active terms
    active_terms = extract_active_terms(source_text, glossary)
    result["active_terms"] = active_terms

    # Step 4: Build typed prompt
    prompt = build_typed_prompt(protected_text, text_type,
                                [t["source"] for t in active_terms])

    # Step 5: Draft translation (check cache first)
    cached = _lookup_cache(source_text)
    if cached is not None:
        result["translation"] = cached
        result["from_cache"] = True
        return result

    draft_protected = call_llm(prompt)

    # Step 6: Postprocess
    draft = postprocess(draft_protected, ph_map, nl_map, ut_map)

    # Step 7: Score
    scores = score_translation(source_text, draft, text_type, active_terms)
    result["scores"] = scores

    # Step 8: Reviewer loop
    if needs_reviewer(scores, risk_level):
        result["reviewer_used"] = True
        max_rounds = CONFIG.get("MAX_REVIEW_ROUNDS", 3)
        current_draft = draft
        current_scores = scores
        best_reviewed = None
        best_reviewed_scores = None

        for round_num in range(max_rounds):
            review_result = review_and_repair(source_text, current_draft, current_scores,
                                              current_scores.get("issue_tags", []))
            if review_result is None:
                break

            reviewed_protected = call_llm(review_result.get("prompt", ""))
            reviewed = postprocess(reviewed_protected, ph_map, nl_map, ut_map)
            reviewed_scores = score_translation(source_text, reviewed, text_type, active_terms)

            if reviewed_scores.get("final_score", 0) > current_scores.get("final_score", 0):
                best_reviewed = reviewed
                best_reviewed_scores = reviewed_scores

            if reviewed_scores.get("verdict") == "PASS":
                best_reviewed = reviewed
                best_reviewed_scores = reviewed_scores
                result["review_rounds"] = round_num + 1
                break

            current_draft = reviewed
            current_scores = reviewed_scores
            result["review_rounds"] = round_num + 1

        # Step 9: Select best
        final_translation, final_scores = select_best(draft, scores, best_reviewed, best_reviewed_scores)
        result["translation"] = final_translation
        result["scores"] = final_scores
    else:
        result["translation"] = draft

    # Step 10: Cache
    _store_cache(source_text, result["translation"])

    # Step 11: Quality log
    write_quality_log(
        sample_id=sample_id or hashlib.md5(source_text.encode()).hexdigest()[:12],
        text_type=text_type,
        source=source_text,
        translation=result["translation"],
        scores=result.get("scores", {}),
        active_terms=active_terms,
        reviewer_used=result["reviewer_used"],
        review_rounds=result["review_rounds"],
    )

    return result


# ============================================================
# Batch Processing
# ============================================================

def translate_batch(items: list[dict], use_cache: bool = True) -> list[dict]:
    """
    Translate a batch of items.
    Each item: {"sample_id": str, "source_text": str, "text_type": str (optional)}
    """
    debug_n = CONFIG.get("DEBUG_TOP_N", 0)
    if debug_n > 0:
        items = items[:debug_n]

    results = []
    for i, item in enumerate(items):
        sample_id = item.get("sample_id", f"batch_{i}")
        source = item.get("source_text", "")

        result = translate(source, sample_id=sample_id)
        result["sample_id"] = sample_id
        results.append(result)

    return results


# ============================================================
# CLI Entry Point
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Game Translation Enhanced V3.5")
    parser.add_argument("--input", "-i", help="Input JSONL file")
    parser.add_argument("--text", "-t", help="Single text to translate")
    parser.add_argument("--source-lang", default="en", help="Source language")
    parser.add_argument("--target-lang", default="zh-cn", help="Target language")
    parser.add_argument("--glossary", "-g", help="Glossary CSV file")
    parser.add_argument("--enable-classifier", action="store_true", help="Enable text classifier")
    parser.add_argument("--enable-reviewer", action="store_true", help="Enable reviewer")
    parser.add_argument("--enable-term-check", action="store_true", help="Enable term check")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode")
    parser.add_argument("--self-test", action="store_true", help="Run self-tests")
    parser.add_argument("--debug-top-n", type=int, default=0, help="Debug: limit to N items")

    args = parser.parse_args()

    # Apply CLI overrides
    CONFIG["SOURCE_LANG"] = args.source_lang
    CONFIG["TARGET_LANG"] = args.target_lang
    CONFIG["DEBUG_TOP_N"] = args.debug_top_n

    if args.enable_classifier:
        CONFIG["ENABLE_TEXT_CLASSIFIER"] = True
    if args.enable_reviewer:
        CONFIG["ENABLE_REVIEWER"] = True
    if args.enable_term_check:
        CONFIG["ENABLE_TERM_CHECK"] = True
    if args.glossary:
        CONFIG["GLOSSARY_PATH"] = args.glossary
        load_glossary(args.glossary)

    if args.self_test:
        run_self_tests()
        return

    if args.text:
        result = translate(args.text)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.input:
        items = []
        with open(args.input, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        results = translate_batch(items)
        for r in results:
            if args.test_mode:
                print(json.dumps({
                    "sample_id": r.get("sample_id", ""),
                    "text_type": r.get("text_type", ""),
                    "translation": r.get("translation", ""),
                    "scores": r.get("scores", {}),
                }, ensure_ascii=False))
            else:
                print(json.dumps(r, ensure_ascii=False))
        return

    # Default: test mode
    print("Game Translation Enhanced V3.5")
    print(f"Config: {json.dumps({k: v for k, v in CONFIG.items() if k.startswith('ENABLE_') or 'THRESHOLD' in k or k == 'ACTIVE_TERMS_LIMIT'}, indent=2)}")
    print("Ready. Use --text '<text>' to translate or --input <file.jsonl> for batch.")


def run_self_tests():
    """Run self-tests for the translation pipeline."""
    errors = []

    # Test classify
    c = classify("Start Game")
    assert c["text_type"] == "normal", f"Classifier off should return normal, got {c}"
    CONFIG["ENABLE_TEXT_CLASSIFIER"] = True
    c = classify("Start Game")
    assert c["text_type"] == "UI", f"'Start Game' should be UI, got {c}"
    c = classify("Deals 100 fire damage to all enemies")
    assert c["text_type"] == "skill", f"Skill text should be skill, got {c}"
    c = classify("Hello, adventurer! Welcome to our village.")
    assert c["text_type"] == "dialogue", f"Dialogue should be dialogue, got {c}"
    c = classify("Server maintenance in 10 minutes")
    assert c["text_type"] == "system", f"System msg should be system, got {c}"
    c = classify("Defeat the dragon in Dark Cave")
    assert c["text_type"] == "quest", f"Quest text should be quest, got {c}"
    CONFIG["ENABLE_TEXT_CLASSIFIER"] = False

    # Test preprocess/postprocess
    text = "Hello {0}, you have %s gold.\nVisit the shop||buy items"
    protected, ph, nl, ut = preprocess(text)
    restored = postprocess(protected, ph, nl, ut)
    assert restored == text, f"Pre/post process roundtrip failed: {restored!r} != {text!r}"

    # Test unit_talk protection
    text2 = "[unit_talk:hero_01] For the kingdom!"
    protected2, ph2, nl2, ut2 = preprocess(text2)
    restored2 = postprocess(protected2, ph2, nl2, ut2)
    assert restored2 == text2, f"unit_talk roundtrip failed: {restored2!r} != {text2!r}"

    # Test format scoring
    score, tags = _score_format("Hello {0}", "Bonjour {0}")
    assert score == 1.0, f"Format should pass, got {score}, tags={tags}"
    score, tags = _score_format("Hello {0}", "Bonjour {1}")
    assert score == 0.0, f"Format should fail on placeholder mismatch, got {score}"

    # Test glossary extraction
    gl = [
        {"source": "Fire Ball", "target": "火球术", "text_type": "skill", "priority": 1},
        {"source": "Fire", "target": "火焰", "text_type": "*", "priority": 3},
    ]
    CONFIG["ENABLE_TERM_CHECK"] = True
    terms = extract_active_terms("Cast Fire Ball to attack", gl)
    assert len(terms) == 1, f"Should extract 1 term (longest match), got {len(terms)}"
    assert terms[0]["source"] == "Fire Ball", f"Should be Fire Ball, got {terms[0]['source']}"
    CONFIG["ENABLE_TERM_CHECK"] = False

    # Test scoring
    scores = score_translation("Fire Ball", "火球术", "skill", [])
    assert scores["format_score"] == 1.0, f"Format should pass, got {scores}"
    assert scores["final_score"] > 0, f"Final score should be > 0, got {scores}"

    # Test format hard gate
    scores = score_translation("Hello {0}", "Bonjour ", "UI", [])
    assert scores["format_score"] == 0.0, f"Format should fail"
    assert scores["final_score"] == 0.0, f"Final score should be 0 on format failure"
    assert scores["verdict"] == "REJECT", f"Verdict should be REJECT on format failure"

    if errors:
        print("SELF-TEST FAILURES:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All translation pipeline self-tests passed.")


if __name__ == "__main__":
    main()
