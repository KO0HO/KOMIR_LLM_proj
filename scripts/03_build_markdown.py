from pathlib import Path
import json
import re


def clean_text(text: str) -> str:
    """
    OCR 텍스트 후처리.
    PaddleOCR 결과에서 자주 나오는 깨짐/불필요 문자를 최소 정리.
    """
    if text is None:
        return ""

    text = str(text).strip()

    # PDF/OCR에서 섞일 수 있는 특수 공백 정리
    text = text.replace("\u3000", " ")
    text = text.replace("￾", " ")
    text = text.replace("\ufeff", "")

    # 공백 정리
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_box_y(item: dict) -> int:
    """
    OCR item의 y 좌표 반환.
    """
    box = item.get("box")

    if isinstance(box, list) and len(box) >= 4:
        return int(box[1])

    polygon = item.get("polygon")
    if isinstance(polygon, list) and len(polygon) > 0:
        try:
            return int(min(p[1] for p in polygon))
        except Exception:
            pass

    return 0


def get_box_x(item: dict) -> int:
    """
    OCR item의 x 좌표 반환.
    """
    box = item.get("box")

    if isinstance(box, list) and len(box) >= 4:
        return int(box[0])

    polygon = item.get("polygon")
    if isinstance(polygon, list) and len(polygon) > 0:
        try:
            return int(min(p[0] for p in polygon))
        except Exception:
            pass

    return 0


def sort_ocr_items(items: list[dict]) -> list[dict]:
    """
    OCR 결과를 위에서 아래, 왼쪽에서 오른쪽 순서로 정렬.
    """
    return sorted(items, key=lambda x: (get_box_y(x), get_box_x(x)))


def classify_line(text: str) -> str:
    """
    간단한 규칙 기반 라인 분류.
    이후 RAG chunk 생성 시 section 구분에 활용 가능.
    """
    t = text.strip()

    if not t:
        return "empty"

    # 제목 후보
    if any(key in t for key in ["전략광종", "인사이트"]):
        return "title"

    # 대분류 섹션
    if re.match(r"^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|I|II|III|IV|V|VI)[\.\s]", t):
        return "section"

    # 번호 섹션
    if re.match(r"^\d+\.\s*", t):
        return "subsection"

    # bullet
    if t.startswith(("", "•", "-", "‐", "※", "▷", "❙")):
        return "bullet"

    # 페이지 번호/목차 번호처럼 보이는 짧은 숫자
    if re.match(r"^\d{1,2}$", t):
        return "page_or_index"

    return "body"


def line_to_markdown(text: str, line_type: str) -> str:
    """
    분류 결과를 Markdown 문법으로 변환.
    """
    if line_type == "title":
        return f"# {text}"

    if line_type == "section":
        return f"## {text}"

    if line_type == "subsection":
        return f"### {text}"

    if line_type == "bullet":
        # OCR bullet 문자를 markdown bullet로 정리
        cleaned = text
        cleaned = cleaned.lstrip("").strip()
        cleaned = cleaned.lstrip("•").strip()
        cleaned = cleaned.lstrip("‐").strip()
        cleaned = cleaned.lstrip("-").strip()

        if text.startswith("※"):
            return f"> {text}"

        if text.startswith(("▷", "❙")):
            return f"### {text}"

        return f"- {cleaned}"

    if line_type == "page_or_index":
        # 목차 번호나 페이지 번호는 일단 숨기지 않고 주석처럼 남김
        return f"<!-- index/page: {text} -->"

    return text


def build_page_markdown(page_json_path: Path) -> tuple[str, list[dict]]:
    """
    OCR JSON 하나를 Markdown 텍스트로 변환.
    """
    with open(page_json_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    items = sort_ocr_items(items)

    lines = []
    structured_lines = []

    page_no_match = re.search(r"page_(\d+)", page_json_path.stem)
    page_no = int(page_no_match.group(1)) if page_no_match else None

    lines.append(f"\n\n---\n")
    lines.append(f"<!-- page: {page_no} -->\n")

    for item in items:
        raw_text = item.get("text", "")
        text = clean_text(raw_text)

        if not text:
            continue

        line_type = classify_line(text)
        md_line = line_to_markdown(text, line_type)

        lines.append(md_line)

        structured_lines.append({
            "page": page_no,
            "line_id": item.get("line_id"),
            "text": text,
            "type": line_type,
            "score": item.get("score"),
            "box": item.get("box"),
            "polygon": item.get("polygon")
        })

    page_md = "\n\n".join(lines).strip() + "\n"

    return page_md, structured_lines


def build_markdown(
    ocr_dir="outputs/ocr_raw",
    out_md_dir="outputs/markdown",
    out_structured_dir="outputs/structured",
    document_title="월간 전략광종 인사이트 2026년 5월호",
    output_name="월간_전략광종_인사이트_2026_05_ocr.md"
):
    ocr_dir = Path(ocr_dir)
    out_md_dir = Path(out_md_dir)
    out_structured_dir = Path(out_structured_dir)

    page_md_dir = out_md_dir / "pages"

    out_md_dir.mkdir(parents=True, exist_ok=True)
    page_md_dir.mkdir(parents=True, exist_ok=True)
    out_structured_dir.mkdir(parents=True, exist_ok=True)

    json_paths = sorted(ocr_dir.glob("page_*.json"))

    if len(json_paths) == 0:
        raise FileNotFoundError(f"OCR JSON 파일이 없습니다: {ocr_dir}")

    full_md_lines = [
        f"# {document_title}",
        "",
        "> 이 문서는 PaddleOCR 결과를 기반으로 자동 생성된 Markdown 초안입니다.",
        "> 표 구조, 차트, 일부 OCR 오인식은 후처리 및 검수가 필요합니다.",
        ""
    ]

    all_structured_lines = []

    print(f"[INFO] Markdown 변환 대상 페이지 수: {len(json_paths)}")

    for page_json_path in json_paths:
        print(f"[처리 중] {page_json_path.name}")

        page_md, structured_lines = build_page_markdown(page_json_path)

        page_md_path = page_md_dir / f"{page_json_path.stem}.md"
        with open(page_md_path, "w", encoding="utf-8") as f:
            f.write(page_md)

        full_md_lines.append(page_md)
        all_structured_lines.extend(structured_lines)

        print(f"[저장 완료] {page_md_path}")

    # 전체 Markdown 저장
    full_md_path = out_md_dir / output_name
    with open(full_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(full_md_lines))

    # 구조화 라인 JSONL 저장
    structured_jsonl_path = out_structured_dir / "ocr_lines.jsonl"
    with open(structured_jsonl_path, "w", encoding="utf-8") as f:
        for row in all_structured_lines:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # 구조화 라인 JSON 저장
    structured_json_path = out_structured_dir / "ocr_lines.json"
    with open(structured_json_path, "w", encoding="utf-8") as f:
        json.dump(all_structured_lines, f, ensure_ascii=False, indent=2)

    print("\n[DONE] Markdown 생성 완료")
    print(f"[전체 Markdown] {full_md_path}")
    print(f"[페이지 Markdown] {page_md_dir}")
    print(f"[구조화 JSONL] {structured_jsonl_path}")
    print(f"[구조화 JSON] {structured_json_path}")


if __name__ == "__main__":
    build_markdown(
        ocr_dir="/home/stat/KYH/KOMIR_LLM_proj/outputs/ocr_raw_week",
        out_md_dir="/home/stat/KYH/KOMIR_LLM_proj/outputs/markdown_week",
        out_structured_dir="/home/stat/KYH/KOMIR_LLM_proj/outputs/structured_week",
        document_title="주간광물가격동향_20260518",
        output_name="주간광물가격동향_20260518.pdf.md"
    )
    
    