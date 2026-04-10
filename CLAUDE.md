# 프로젝트 지침

## 언어

모든 응답, 분석, 리포트, 산출물(.md 파일)은 한글로 작성합니다.
코드 주석, 변수명, 커밋 메시지 등 코드 관련 내용은 영어를 유지합니다.

## CLAUDE.md 관리 원칙

- 이 파일은 최대한 간결하고 명확하게 유지합니다
- 중복된 지침을 작성하지 않습니다
- 불필요하거나 오래된 지침은 삭제합니다

## 프로젝트 정보
- 과제명: test
- 기록자: 윤성재

## 코드 작성 방침

### 1. 코딩 전에 생각하기
- 가정을 명시적으로 밝히고, 불확실하면 질문
- 여러 해석이 가능하면 조용히 선택하지 말고 선택지를 제시
- 더 간단한 접근이 있으면 제안
- 혼란스러운 요소는 넘어가지 말고 명확히 짚기

### 2. 단순성 우선
- 요청된 것 이상의 기능을 추가하지 않음
- 한 번만 쓰이는 코드에 추상화를 만들지 않음
- 불필요한 "유연성"이나 "설정 가능성"을 넣지 않음
- 발생할 수 없는 시나리오에 대한 에러 핸들링을 하지 않음
- 50줄이면 될 것을 200줄로 만들지 않음

### 3. 외과적 변경
- 관련 없는 코드, 주석, 포맷을 개선하지 않음
- 동작하는 코드를 리팩토링하지 않음
- 기존 스타일을 따름
- 내 변경으로 생긴 미사용 코드만 정리 (기존 dead code는 건드리지 않음)
- 모든 변경된 줄은 사용자의 요청에 직접 연결되어야 함

### 4. 목표 기반 실행
- 모호한 태스크를 측정 가능한 목표와 검증 단계로 변환
- 다단계 작업에는 각 단계별 체크포인트가 있는 구조화된 계획 수립
- 강한 기준은 독립적 반복을 가능하게 하고, 약한 기준은 끊임없는 확인을 필요로 함

### 5. 문서 동기화
- 코드 변경이 프로젝트의 README.md 내용에 영향을 줄 때 (API 변경, 새 기능 추가, 설정 변경, 사용법 변경 등) 반드시 README.md도 함께 업데이트

### 6. 분기 처리
- 메이저 테스크 완료시마다 git 분기 처리.

## gstack

- 웹 브라우징에는 gstack의 /browse 스킬을 사용하고, mcp__claude-in-chrome__* 도구는 사용하지 않습니다.
- 사용 가능한 스킬: /office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review, /design-consultation, /design-shotgun, /design-html, /review, /ship, /land-and-deploy, /canary, /benchmark, /browse, /connect-chrome, /qa, /qa-only, /design-review, /setup-browser-cookies, /setup-deploy, /retro, /investigate, /document-release, /codex, /cso, /autoplan, /plan-devex-review, /devex-review, /careful, /freeze, /guard, /unfreeze, /gstack-upgrade, /learn
- gstack 스킬이 동작하지 않으면 `cd ~/.claude/skills/gstack && ./setup`을 실행하세요.

## Skill routing

When the user's request matches an available skill, ALWAYS invoke it using the Skill
tool as your FIRST action. Do NOT answer directly, do NOT use other tools first.
The skill has specialized workflows that produce better results than ad-hoc answers.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health