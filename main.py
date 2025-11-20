import strawberry
from typing import Optional, List

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter


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

# 더미 데이터
EMPLOYEES: List[Employee] = [
    Employee(id="1", name="John",  age=35, job="frontend",  language="react",      pay=400),
    Employee(id="2", name="Peter", age=28, job="backend",   language="java",       pay=300),
    Employee(id="3", name="Sue",   age=38, job="publisher", language="javascript", pay=400),
    Employee(id="4", name="Susan", age=45, job="pm",        language="python",     pay=500),
]


@strawberry.type
class Query:
    @strawberry.field
    def employees(self) -> List[Employee]:
        return EMPLOYEES

@strawberry.type
class Mutation:
    @strawberry.mutation
    def createEmployee(self, input: EmployeeInput) -> Employee:
        # 등록 쿼리
        new_emp = Employee(
            id = 10,
            name = input.name,
            age = input.age,
            job = input.job,
            language = input.language,
            pay = input.pay
        )
        EMPLOYEES.append(new_emp)
        return new_emp

    @strawberry.mutation
    def updateEmployee(self, id:strawberry.ID, input: EmployeeInput) -> Employee:
        # 수정 쿼리
        for idx, emp in enumerate(EMPLOYEES):
            if emp.id == id:
                update = Employee(
                    id=emp.id,
                    name=input.name,
                    age=input.age,
                    job=input.job,
                    language=input.language,
                    pay=input.pay
                )
                EMPLOYEES[idx] = update
                return update
        raise ValueError("Employee not found")

    @strawberry.mutation
    def deleteEmployee(self, id:strawberry.ID) -> strawberry.ID:
        global EMPLOYEES
        EMPLOYEES = [e for e in EMPLOYEES if e.id != id]
        return id


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)


app = FastAPI()

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










