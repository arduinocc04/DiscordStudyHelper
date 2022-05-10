---
theme: gaia
_class: lead
paginate: true
backgroundColor: #fff
marp: true
backgroundImage: url('https://marp.app/assets/hero-background.svg')
---

# **디스코드 API를 활용한 학습도움 봇 만들기**
30725 조다니엘

---

# 기능
- 사진으로 문제 올리기
- 누가 풀었고 안 풀었는지 확인
- 문제 북마크

---

<!--# 실제

----->

# 사용한 라이브러리
- logging
- requests
- asyncio
- nest_asyncio
- websockets
- json
- time

---

# 디스코드 API의 구성

## Discord HTTP API
 - 봇의 명령어 등록, 메세지 보내기 등 다양한 명령

## Discord GATEWAY API
 - 봇이 정상적으로 동작하는지 확인(Heartbeat)
 - 이벤트 받기

---

# 디스코드 API 작동 방식

