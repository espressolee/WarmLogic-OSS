# WarmLogic Console

WarmLogic Runtime Suite를 위한 최소 콘솔 UI.

- Run overview
- GOVDEC / decision log drill-down
- CE ledger 브라우저
- Cohort status 뷰(파일럿용)

---

## 1. 아키텍처 개요

- Backend: Flask (minimal demo)
  - `/api/v1/runs`
  - `/api/v1/runs/<run_id>`
  - `/api/v1/runs/<run_id>/decisions`
  - `/api/v1/runs/<run_id>/verify`
  - `/api/v1/ce-ledger`
- Frontend: static HTML/JS (`console/static/index.html`) fetching API directly.
- Auth (v1): `X-API-Key` header (`WL_CONSOLE_API_KEY`); production-grade RBAC는 제외.

---

## 2. 로컬 데모 (Flask + static UI)

```bash
python console/app.py \
  --run-root out/osctl_runs \
  --ce-ledger ledger/pilots/TeamA/CE_Ledger_v1.jsonl \
  --host 127.0.0.1 --port 8765
# 브라우저: http://127.0.0.1:8765
```

- Flask는 이미 로컬에 설치되어 있거나 `pip install Flask>=3,<4` 로 설치.
- 데이터 소스는 osctl run 출력(`out/osctl_runs/*`)과 CE ledger 파일을 사용.

---

## 3. API Contract (v1)
- `GET /api/v1/runs` (query: limit, status)
- `GET /api/v1/runs/<run_id>`
- `GET /api/v1/ce-ledger`
- `GET /api/v1/cohorts`
- 응답 예시는 `eval_best_choices` 문서의 패턴을 따르며 JSON 포맷을 기본으로 한다.

## 4. 인증/보안 (v1)
- 기본: `X-API-Key` 헤더로 API 토큰(예: `WL_CONSOLE_API_KEY`) 전달.
- 생산용 RBAC/멀티테넌트는 미포함; 파일럿/연구용 한정.

## 5. CI Smoke Test
- 워크플로: `.github/workflows/console-smoke.yml`
  - Python 3.10 + Flask 설치
  - 콘솔 백엔드 기동
  - `curl`로 `/api/v1/runs`, `/api/v1/ce-ledger`, `/` 호출
  - 200 응답 + JSON 파싱 실패 시 FAIL
- 목적: 콘솔 변경 시 최소 라우팅/기동/응답 회귀를 즉시 탐지.

## 6. Limitations (v1)
- production-grade auth/RBAC 없음.
- multi-tenant / org-separated view 없음.
- 파일럿/연구용이며, 일반 SaaS 수준 UX는 목표 아님.

## 3. 주요 화면 / 기능 체크리스트 (v1)
- Run 리스트 페이지
- Run 상세 + GOVDEC 요약
- decision_log 테이블 + 필터
- CE ledger 리스트/상세
- Cohort status 리스트
- 기본 오류/로딩 상태 처리

---

## 4. 제한 사항 / TODO
- 인증/권한: v1 데모에서는 생략, 파일럿 요구에 맞춰 proxy/토큰 추가 예정.
- UI: 현재는 최소 HTML/JS. 정식 콘솔 프레임워크(React/TS 등)로 교체 예정.
- 다국어, 접근성(a11y), 테마 등은 v1에서는 Best-effort.

---

## 5. 관련 문서
- `docs/runtime/Console_Product_Spec_v1.md`
- `docs/runtime/Runtime_SLI_SLO_Spec_v1.md`
- `docs/api/Runtime_Console_API_v1.md`
