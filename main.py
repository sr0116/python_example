import strawberry
from typing import Optional, List
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
# from db.database import Base, Session as SessionLocal, engine
from db.models import EmployeeModel
import redis

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

EMPLOYEE_ID_COUNTER_KEY = "employee:id:counter"
EMPLOYEE_ALL_SET_KEY = "employee:all-set"


def employee_redis_key(emp_id: int) -> str:
    return f"employee:id:{emp_id}"


@strawberry.type
class Employee:
    id: strawberry.ID
    name: str
    age: int
    job: str
    language:str
    pay: int

@strawberry.input
class EmployeeInput:
    name: str
    age: int
    job: str
    language: str
    pay: int

# ORM 객체 -> GraphQL 타입 변환 도움미
def redis_to_graphql(emp_id: int, emp: dict) -> Employee:
    return Employee(
        id = str(emp_id),
        name = emp.name,
        age= emp.age,
        job= emp.job,
        language = emp.language,
        pay = emp.pay
    )

@strawberry.type
class Query:
    @strawberry.field
    def employees(self) -> List[Employee]:
        ids = r.smembers(EMPLOYEE_ALL_SET_KEY)
        result: List[Employee] = []
        for id_str in ids:
            key = employee_redis_key(int(id_str))
            data = r.hgetall(key)
            if data:
                result.append(redis_to_graphql(int(id_str), data))
        result.sort(key=lambda emp: emp.id)
        return result

@strawberry.type
class Mutation:
    # Redis 등록 로직
    @strawberry.mutation
    def createEmployee(self, input: EmployeeInput) -> Employee:
        # 새 직원 ID 생성
        new_id = r.incr(EMPLOYEE_ID_COUNTER_KEY)

        key = employee_redis_key(new_id)

        # Redis Hash에 저장
        r.hset(
            key,
            mapping={
                "name": input.name,
                "age": input.age,
                "job": input.job,
                "language": input.language,
                "pay": input.pay,
            },
        )

        # 전체 목록 집합에 추가
        r.sadd(EMPLOYEE_ALL_SET_KEY, new_id)

        # 방금 저장된 데이터 가져오기
        data = r.hgetall(key)

        # Employee GraphQL 타입 변환
        return Employee(
            id=str(new_id),
            name=data["name"],
            age=int(data["age"]),
            job=data["job"],
            language=data["language"],
            pay=int(data["pay"]),
        )

    @strawberry.mutation
    def updateEmployee(self, id: strawberry.ID, input: EmployeeInput) -> Employee:
        emp_id = int(id)
        key = employee_redis_key(emp_id)

        # 존재 여부 확인
        if not r.exists(key):
            raise ValueError("Employee not found")

        # Hash 업데이트
        r.hset(
            key,
            mapping={
                "name": input.name,
                "age": input.age,
                "job": input.job,
                "language": input.language,
                "pay": input.pay,
            },
        )

        updated_data = r.hgetall(key)

        return Employee(
            id=str(emp_id),
            name=updated_data["name"],
            age=int(updated_data["age"]),
            job=updated_data["job"],
            language=updated_data["language"],
            pay=int(updated_data["pay"]),
        )

    @strawberry.mutation
    def deleteEmployee(self, id: strawberry.ID) -> strawberry.ID:
        emp_id = int(id)
        key = employee_redis_key(emp_id)

        # 존재 여부
        if not r.exists(key):
            raise ValueError("Employee not found")

        # 직원 Hash 삭제
        r.delete(key)

        # 전체 목록 Set에서도 제거
        r.srem(EMPLOYEE_ALL_SET_KEY, emp_id)

        return strawberry.ID(str(emp_id))


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

def init_sample_data():
    """서버 최초 실행 시 Redis에 샘플 직원 데이터 넣기 (이미 있으면 스킵)"""

    # 이미 직원 데이터가 존재하면 스킵
    if r.scard(EMPLOYEE_ALL_SET_KEY) > 0:
        return

    samples = [
        {"name": "John",  "age": 35, "job": "frontend",  "language": "react",      "pay": 400},
        {"name": "Peter", "age": 28, "job": "backend",   "language": "java",       "pay": 300},
        {"name": "Sue",   "age": 38, "job": "publisher", "language": "javascript", "pay": 400},
        {"name": "Susan", "age": 45, "job": "pm",        "language": "python",     "pay": 500},
    ]

    for emp in samples:
        # 새로운 ID 증가
        new_id = r.incr(EMPLOYEE_ID_COUNTER_KEY)

        # 키 구성
        key = employee_redis_key(new_id)

        # Redis Hash 저장
        r.hset(key, mapping=emp)

        # 전체 직원 목록 set 추가
        r.sadd(EMPLOYEE_ALL_SET_KEY, new_id)



app = FastAPI()


@app.on_event("startup")
def startup_event():
    init_sample_data()


# CORS 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    return {"message": "FastAPI GraphQL Employee 서버 동작 중....."}






