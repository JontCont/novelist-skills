from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from locale_config import load_config, tokenize
from sdd_core import corpus_hash, file_hash, iter_knowledge_files


@dataclass
class Chunk:
    path: str
    line: int
    text: str
    tokens: list[str]


@dataclass
class Result:
    path: str
    line: int
    score: float
    text: str


def load_chunks(project: Path, config: dict) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in iter_knowledge_files(project):
        relative_path = path.relative_to(project).as_posix()
        if relative_path == ".novelist/config.json":
            continue
        if path.suffix.lower() == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
            if relative_path == "characters.json":
                values = value.get("characters", [])
            elif relative_path == "progress.json":
                current = {key: item for key, item in value.items() if key != "chapter_history"}
                values = [current, *value.get("chapter_history", [])]
            else:
                values = [value]
            for item in values:
                text = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
                chunks.append(Chunk(relative_path, 1, text, tokenize(text, config)))
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        start = 0
        paragraph: list[str] = []
        for index, line in enumerate(lines + [""]):
            if line.strip():
                if not paragraph:
                    start = index + 1
                paragraph.append(line.strip())
            elif paragraph:
                text = " ".join(paragraph)
                chunks.append(Chunk(relative_path, start, text, tokenize(text, config)))
                paragraph = []
    return chunks


def rank(chunks: list[Chunk], query: str, limit: int, config: dict) -> list[Result]:
    query_counts = Counter(tokenize(query, config))
    if not query_counts or not chunks:
        return []

    document_frequency = Counter(token for chunk in chunks for token in set(chunk.tokens))
    average_length = sum(len(chunk.tokens) for chunk in chunks) / len(chunks)
    results: list[Result] = []
    for chunk in chunks:
        counts = Counter(chunk.tokens)
        score = 0.0
        for token, query_weight in query_counts.items():
            frequency = counts[token]
            if not frequency:
                continue
            inverse_frequency = math.log(1 + (len(chunks) - document_frequency[token] + 0.5) / (document_frequency[token] + 0.5))
            denominator = frequency + 1.2 * (0.25 + 0.75 * len(chunk.tokens) / max(average_length, 1))
            score += query_weight * inverse_frequency * frequency * 2.2 / denominator
        if chunk.path in {"story.json", "characters.json", "progress.json"}:
            score *= 1.3
        elif chunk.path.startswith("canon/"):
            score *= 1.15
        if score > 0:
            results.append(Result(chunk.path, chunk.line, round(score, 4), chunk.text[:700]))
    return sorted(results, key=lambda result: (-result.score, result.path, result.line))[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Retrieve relevant novel knowledge")
    parser.add_argument("project", type=Path)
    parser.add_argument("query")
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--receipt", help="approved chapter task path to bind this retrieval to")
    args = parser.parse_args()

    project = args.project.resolve()
    if not (project / "state.json").is_file():
        parser.error(f"not a novel project: {project}")
    try:
        config = load_config(project)
    except (json.JSONDecodeError, ValueError) as error:
        parser.error(f"invalid locale configuration: {error}")
    results = rank(load_chunks(project, config), args.query, max(args.top, 1), config)
    if args.receipt:
        task = (project / args.receipt).resolve()
        try:
            task_relative = task.relative_to(project).as_posix()
        except ValueError:
            parser.error("receipt task must be inside the novel project")
        if not task.is_file() or not task_relative.startswith("chapters/tasks/"):
            parser.error(f"invalid chapter task: {task_relative}")
        receipt = {
            "query": args.query,
            "content_locale": config["content_locale"],
            "task": task_relative,
            "task_sha256": file_hash(task),
            "corpus_sha256": corpus_hash(project),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sources": [asdict(result) for result in results],
        }
        receipt_path = project / ".novelist/retrievals" / f"{task.stem}.json"
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        for result in results:
            print(f"[{result.score:.4f}] {result.path}:{result.line}\n{result.text}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
