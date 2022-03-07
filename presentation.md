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

# 사용한 라이브러리
### asyncio
여러개의 명령을 동시에 처리하기 위해
### websockets
Websocket(Discord GATEWAY API에서 사용)을 사용하기 위해
### json
Dict 자료형 $\leftrightarrow$ JSON 문자열 변환을 간단하게 하기 위해

---

# 디스코드 API의 구성

## Discord HTTP API
 - 봇의 명령어 등록 등의 역할 수행(자료가 오고가고 하지는 않음)

## Discord GATEWAY API
 - 봇이 정상적으로 동작함 알림
 - 데이터 받기(자료가 오고감)

---

# tmp

```mermaid

sequenceDiagram
    participant Client
    participant GatewayAPI
    participant HttpAPI
    Client-->>GatewayAPI: Connect
    GatewayAPI->>Client: Hello(op:10)+heartbeat_interval(약 40초)
    rect rgb(10, 150, 150)
    loop 매 heartbeat_interval 마다
        Client->>GatewayAPI: Heartbeat(op:1)
        GatewayAPI->>Client: Hertbeat ack(op:11)
    end
    end
    rect rgb(100, 150, 150)
    opt 가끔
    GatewayAPI->>Client: Heartbeat(op:1)
    Client->>GatewayAPI: Heartbeat(op:1)(즉시 보내져야 함)
    GatewayAPI->>Client: Heartbeat ack(op:11)
    end
    end
    Client->>GatewayAPI: Identify(op:2)
    GatewayAPI->>Client: Ready(op:0)
    GatewayAPI->>Client: GuildCreate(op:0, s:2)
    rect rgb(100, 1150, 100)
    opt SLASH COMMAND(op:0, t:INTERACTION_CREATE)
    GatewayAPI->>Client: INTERACTION_CREATE
    Client->>HttpAPI: INTERACTION(즉시 보내져야 함)
    Client-->>HttpAPI: FOLLOWUP INTERACTIONS(15분 안에 보내져야 함)
    end
    end
```