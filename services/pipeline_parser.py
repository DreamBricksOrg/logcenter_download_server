import re

from bson import json_util

_OBJECT_ID_RE = re.compile(r'ObjectId\(\s*"([a-fA-F0-9]{24})"\s*\)')
_ISO_DATE_RE = re.compile(r'ISODate\(\s*"([^"]+)"\s*\)')
_UNQUOTED_KEY_RE = re.compile(r'([{,]\s*)([A-Za-z_$][A-Za-z0-9_$]*)(\s*:)')

FORBIDDEN_STAGES = {"$out", "$merge"}


class PipelineParseError(ValueError):
    pass


def _strip_comments(text):
    """Removes // line comments, respecting string literals."""
    result = []
    in_string = False
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if in_string:
            result.append(ch)
            if ch == '\\' and i + 1 < length:
                result.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            result.append(ch)
            i += 1
            continue
        if ch == '/' and i + 1 < length and text[i + 1] == '/':
            while i < length and text[i] != '\n':
                i += 1
            continue
        result.append(ch)
        i += 1
    return ''.join(result)


def _quote_keys(text):
    return _UNQUOTED_KEY_RE.sub(r'\1"\2"\3', text)


def parse(raw_text):
    """Converts a Compass/shell-style aggregation pipeline (unquoted keys,
    ObjectId(...), ISODate(...), // comments) into a list of stage dicts
    usable with pymongo's Collection.aggregate()."""
    if not raw_text or not raw_text.strip():
        raise PipelineParseError("O pipeline está vazio.")

    text = _strip_comments(raw_text)
    text = _OBJECT_ID_RE.sub(r'{"$oid": "\1"}', text)
    text = _ISO_DATE_RE.sub(r'{"$date": "\1"}', text)
    text = _quote_keys(text)

    try:
        stages = json_util.loads(text)
    except Exception as exc:
        raise PipelineParseError(f"Pipeline com sintaxe inválida: {exc}") from exc

    if not isinstance(stages, list) or not all(isinstance(stage, dict) for stage in stages):
        raise PipelineParseError("O pipeline precisa ser uma lista de estágios (objetos).")

    for stage in stages:
        forbidden = FORBIDDEN_STAGES.intersection(stage.keys())
        if forbidden:
            raise PipelineParseError(
                f"Estágio {', '.join(sorted(forbidden))} não é permitido — esta ferramenta é somente leitura."
            )

    return stages
