# KOMIR LLM Project

KOMIR_LLM 프로젝트는 KOMIS 광물시장 PDF 보고서를 AI가 활용 가능한 구조화 데이터로 변환하기 위한 PoC 프로젝트입니다.

본 프로젝트의 핵심 목적은 PDF 문서를 단순 OCR하는 것이 아니라, 문서 내 텍스트, 표, 섹션, 페이지 정보를 추출하여 Markdown, JSONL, CSV, metadata 형태의 AI-Ready 데이터로 전환하는 것입니다.

---

## 1. Project Goal

본 프로젝트는 PDF 기반 광물시장 보고서를 AI 분석 및 RAG 질의응답에 활용할 수 있도록 구조화하는 것을 목표로 합니다.

주요 목표는 다음과 같습니다.

- PDF 문서의 기계 판독성 확보
- 문서 내 제목, 본문, 표, 차트, 주석 영역 분리
- 페이지, 섹션, 광종, 문서 유형 등 메타데이터 부여
- RAG 검색에 적합한 chunk 단위 데이터 생성
- 광물 가격 동향, 시장 이슈, 기관별 가격 전망 데이터를 분석 가능한 형태로 변환

---

## 2. Use Case

본 프로젝트의 산출물은 다음 업무에 활용할 수 있습니다.

- KOMIS 문서 기반 RAG 질의응답
- 광물 가격 변동 원인 설명
- 월간 시장 이슈 자동 요약
- 기관별 가격 전망 비교
- 광종별 수급 리스크 탐색
- PDF 보고서의 AI-Ready 데이터 자산화

---

## 3. Pipeline

현재 파이프라인은 다음 순서로 구성됩니다.

```text
PDF
→ Page Image Rendering
→ PaddleOCR
→ OCR JSON
→ Markdown
→ Structured JSONL
→ RAG-ready Dataset
```

---

## 4. Directory Structure

```text
KOMIR_LLM_proj/
├── data/
│   └── raw_pdf/
│       └── .gitkeep
├── external/
│   └── .gitkeep
├── outputs/
│   └── .gitkeep
├── scripts/
│   ├── 01_pdf_to_images.py
│   ├── 02_ocr.py
│   └── 03_build_markdown.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 5. Scripts

### 5.1 PDF to Images

`scripts/01_pdf_to_images.py`

PDF 파일을 페이지별 PNG 이미지로 변환합니다.

Input:

```text
data/raw_pdf/*.pdf
```

Output:

```text
outputs/page_images/page_001.png
outputs/page_images/page_002.png
...
```

---

### 5.2 OCR

`scripts/02_ocr.py`

PaddleOCR를 사용하여 페이지 이미지에서 텍스트, 인식 점수, 좌표 정보를 추출합니다.

Input:

```text
outputs/page_images/*.png
```

Output:

```text
outputs/ocr_raw/page_001.json
outputs/ocr_raw/page_002.json
...
```

PaddleOCR 3.x 기준 OCR 결과 구조는 다음과 같습니다.

```text
res.json
└── res
    ├── rec_texts
    ├── rec_scores
    ├── rec_polys
    └── rec_boxes
```

---

### 5.3 Build Markdown

`scripts/03_build_markdown.py`

OCR JSON 결과를 읽어 페이지별 Markdown과 전체 Markdown 초안을 생성합니다.

Output:

```text
outputs/markdown/pages/page_001.md
outputs/markdown/월간_전략광종_인사이트_2026_05_ocr.md
outputs/structured/ocr_lines.jsonl
outputs/structured/ocr_lines.json
```

---

## 6. Environment

권장 환경은 다음과 같습니다.

```text
Python 3.11
PaddleOCR 3.x
paddlepaddle 3.2.2
```

CPU 환경에서 `paddlepaddle 3.3.x` 사용 시 oneDNN/PIR 관련 오류가 발생할 수 있습니다.

예시 오류:

```text
NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support
```

현재 프로젝트에서는 안정적인 실행을 위해 다음 버전을 권장합니다.

```text
paddlepaddle==3.2.2
```

---

## 7. Installation

```bash
conda create -n paddle_ocr python=3.11 -y
conda activate paddle_ocr

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

PaddleOCR GitHub 소스 기준으로 사용할 경우 외부 레포는 `external/` 하위에 분리합니다.

```bash
mkdir -p external
cd external

git clone https://github.com/PaddlePaddle/PaddleOCR.git
cd PaddleOCR

pip install -e .
```

---

## 8. Run Pipeline

프로젝트 루트에서 실행합니다.

```bash
cd /home/stat/KYH/KOMIR_LLM_proj
conda activate paddle_ocr
```

### Step 1. PDF to Images

```bash
python scripts/01_pdf_to_images.py
```

### Step 2. OCR

```bash
python scripts/02_ocr.py
```

### Step 3. Build Markdown

```bash
python scripts/03_build_markdown.py
```

---

## 9. AI-Ready Data Concept

본 프로젝트에서 AI-Ready 데이터화는 다음을 의미합니다.

- PDF 문서의 텍스트를 기계 판독 가능한 형태로 변환
- 문서의 페이지, 섹션, 광종, 표, 주석 정보를 구조화
- 원문 PDF와 변환 결과 간 추적성 확보
- 표 데이터를 CSV 또는 Excel 형태로 분리
- RAG 검색에 적합한 JSONL chunk 생성
- 문서 출처, 발행월, 문서 유형, 광종 등 metadata 부여

---

## 10. Current Status

현재까지 완료한 작업은 다음과 같습니다.

- PDF 페이지 이미지 변환 스크립트 작성
- PaddleOCR 기반 OCR 실행 스크립트 작성
- PaddleOCR 3.x 결과 구조 파싱 방식 확인
- OCR 결과를 JSON으로 저장하는 구조 구성
- OCR JSON을 Markdown으로 변환하는 초기 스크립트 작성

---

## 11. Next Steps

향후 작업 예정 항목은 다음과 같습니다.

- OCR Markdown 품질 점검
- 제목, 본문, 목차, 주석 분류 규칙 보정
- 광종별 섹션 태깅 규칙 추가
- 표 추출 스크립트 작성
- RAG용 chunk 생성 스크립트 작성
- 문서 metadata 자동 생성

---

## 12. Notes

본 프로젝트는 현재 PoC 단계입니다.

따라서 OCR 결과와 Markdown 결과는 자동 생성 초안이며, 다음 항목은 추가 검수 및 후처리가 필요합니다.

- 표 구조 복원 정확도
- 차트 내 텍스트 인식 결과
- OCR 오인식 문자
- 목차와 본문 섹션 구분
- 광종별 문단 분리


최종 목표는 PDF 문서를 단순 텍스트로 변환하는 것이 아니라, AI가 검색, 요약, 비교, 추론에 활용할 수 있는 구조화 문서 데이터로 전환하는 것입니다.