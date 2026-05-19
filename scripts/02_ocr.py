from pathlib import Path
import json
from paddleocr import PaddleOCR


# def convert_result_to_items(result):
    # """
    # PaddleOCR 3.x predict 결과를 JSON 저장용 구조로 변환.
    # 버전/모델 설정에 따라 반환 구조가 조금 다를 수 있어서 방어적으로 처리함.
    # """

    # page_items = []

    # if result is None:
    #     return page_items

    # # PaddleOCR 3.x는 보통 결과 객체 리스트를 반환함
    # for res in result:
    #     # 일부 결과 객체는 dict처럼 접근 가능하거나 json/dict 변환 메서드를 가짐
    #     try:
    #         if hasattr(res, "json"):
    #             data = res.json
    #         elif hasattr(res, "to_dict"):
    #             data = res.to_dict()
    #         elif isinstance(res, dict):
    #             data = res
    #         else:
    #             data = dict(res)
    #     except Exception:
    #         # fallback: 객체 내부 dict 확인
    #         data = getattr(res, "__dict__", {})

    #     # 자주 나오는 키 후보들
    #     rec_texts = data.get("rec_texts", [])
    #     rec_scores = data.get("rec_scores", [])
    #     rec_polys = data.get("rec_polys", data.get("dt_polys", []))

    #     for idx, text in enumerate(rec_texts):
    #         score = None
    #         bbox = None

    #         if idx < len(rec_scores):
    #             try:
    #                 score = float(rec_scores[idx])
    #             except Exception:
    #                 score = None

    #         if idx < len(rec_polys):
    #             try:
    #                 bbox = rec_polys[idx].tolist()
    #             except Exception:
    #                 bbox = rec_polys[idx]

    #         page_items.append({
    #             "bbox": bbox,
    #             "text": text,
    #             "score": score
    #         })

    # return page_items

def convert_result_to_items(result):
    """
    PaddleOCR 3.x predict 결과를 JSON 저장용 구조로 변환.

    현재 확인된 구조:
    result: list
      - OCRResult
        - res.json:
          {
            "res": {
              "rec_texts": [...],
              "rec_scores": [...],
              "rec_polys": [...],
              "rec_boxes": [...]
            }
          }
    """

    page_items = []

    if result is None:
        return page_items

    for res in result:
        # PaddleOCR 3.x OCRResult는 dict처럼 동작하고 json 속성을 가짐
        if hasattr(res, "json"):
            data = res.json
            if callable(data):
                data = data()
        elif isinstance(res, dict):
            data = res
        else:
            data = getattr(res, "__dict__", {})

        # 실제 OCR 결과는 data["res"] 안에 있음
        if isinstance(data, dict) and "res" in data:
            data = data["res"]

        if not isinstance(data, dict):
            print("[경고] OCR 결과를 dict로 변환하지 못했습니다.")
            continue

        rec_texts = data.get("rec_texts", [])
        rec_scores = data.get("rec_scores", [])
        rec_polys = data.get("rec_polys", [])
        rec_boxes = data.get("rec_boxes", [])

        print(f"[DEBUG] 추출 텍스트 라인 수: {len(rec_texts)}")

        for idx, text in enumerate(rec_texts):
            score = None
            polygon = None
            box = None

            if idx < len(rec_scores):
                score = float(rec_scores[idx])

            if idx < len(rec_polys):
                polygon = rec_polys[idx]

            if idx < len(rec_boxes):
                box = rec_boxes[idx]

            page_items.append({
                "line_id": idx + 1,
                "text": text,
                "score": score,
                "polygon": polygon,
                "box": box
            })

    return page_items

def run_ocr(
    image_dir="outputs/page_images",
    out_dir="outputs/ocr_raw",
    lang="korean",
    min_score=0.0
):
    image_dir = Path(image_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not image_dir.exists():
        raise FileNotFoundError(f"이미지 디렉토리를 찾을 수 없습니다: {image_dir}")

    image_paths = sorted(
        list(image_dir.glob("*.png")) +
        list(image_dir.glob("*.jpg")) +
        list(image_dir.glob("*.jpeg"))
    )

    if len(image_paths) == 0:
        raise FileNotFoundError(f"OCR 대상 이미지가 없습니다: {image_dir}")

    print(f"[INFO] OCR 대상 이미지 수: {len(image_paths)}")
    print(f"[INFO] 입력 디렉토리: {image_dir}")
    print(f"[INFO] 출력 디렉토리: {out_dir}")

    # PaddleOCR 3.x 방식
    ocr = PaddleOCR(
        lang=lang,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True
    )

    for idx, img_path in enumerate(image_paths, start=1):
        print(f"\n[{idx}/{len(image_paths)}] OCR 실행: {img_path.name}")

        result = ocr.predict(str(img_path))
        page_items = convert_result_to_items(result)

        if min_score > 0:
            page_items = [
                item for item in page_items
                if item["score"] is not None and item["score"] >= min_score
            ]

        out_path = out_dir / f"{img_path.stem}.json"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(page_items, f, ensure_ascii=False, indent=2)

        print(f"[저장 완료] {out_path}")
        print(f"[INFO] 인식 텍스트 라인 수: {len(page_items)}")

    print("\n[DONE] 전체 OCR 완료")


if __name__ == "__main__":
    run_ocr(
        image_dir="outputs/page_images_week",
        out_dir="outputs/ocr_raw_week",
        lang="korean",
        min_score=0.0
    )