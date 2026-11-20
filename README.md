# 유사 차트 오버랩 사이트

현재 나스닥/S&P500/코스피 차트와 모양이 비슷한 과거 3개 구간을 찾아 캔들+줌 차트로 보여줍니다.
GitHub Actions가 평일 아침 7:30(한국시간)에 자동 갱신 → GitHub Pages로 공개.

## 설치 (한 번만)
1. GitHub에서 새 저장소 만들기 (예: `fractal-chart`, Public)
2. 이 폴더의 파일 전체를 저장소에 올리기 (`.github` 폴더 포함)
3. 저장소 Settings → Pages → Source: **GitHub Actions** 선택
4. Actions 탭 → update-charts → Run workflow
5. 완료 후 주소: `https://<내아이디>.github.io/fractal-chart/`
