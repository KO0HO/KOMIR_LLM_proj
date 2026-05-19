from pathlib import Path
import fitz  # pymupdf


def pdf_to_images(pdf_path: str, out_dir: str, zoom: float = 2.0):
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

    doc = fitz.open(pdf_path)

    for page_idx, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        out_path = out_dir / f"page_{page_idx:03d}.png"
        pix.save(out_path)

        print(f"[저장 완료] {out_path}")

    print(f"\n총 {len(doc)}개 페이지 변환 완료")
    doc.close()


if __name__ == "__main__":
    pdf_to_images(
        pdf_path="/home/stat/KYH/KOMIR_LLM_proj/data/주간광물가격동향_20260518.pdf",
        out_dir="/home/stat/KYH/KOMIR_LLM_proj/outputs/page_images_week",
        zoom=2.0
    )