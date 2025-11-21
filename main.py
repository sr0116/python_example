import strawberry
from typing import List
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from starlette.middleware.cors import CORSMiddleware

from pymongo import MongoClient
from bson.objectid import ObjectId


# ==============================
# 1) MongoDB 연결
# ==============================
client = MongoClient("mongodb://admin:admin1234@localhost:27017/?authSource=admin")
db = client["employee_db"]
employees_col = db["employees"]
counter_col = db["counters"]  # ID 자동 증가용


# ==============================
# 2) Counter(시퀀스) 함수
# ==============================
def get_next_sequence(name: str) -> int:
    result = counter_col.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return result["seq"]


# ==============================
# 3) GraphQL 타입 정의
# ==============================
@strawberry.type
class Employee:
    id: strawberry.ID
    name: str
    age: int
    job: str
    language: str
    pay: int


@strawberry.input
class EmployeeInput:
    name: str
    age: int
    job: str
    language: str
    pay: int


# ==============================
# 4) Mongo → GraphQL 변환 함수
# ==============================
def mongo_to_graphql(doc) -> Employee:
    return Employee(
        id=str(doc["id"]),
        name=doc["name"],
        age=doc["age"],
        job=doc["job"],
        language=doc["language"],
        pay=doc["pay"]
    )


# ==============================
# 5) Query
# ==============================
@strawberry.type
class Query:
    @strawberry.field
    def employees(self) -> List[Employee]:
        docs = employees_col.find().sort("id", 1)
        return [mongo_to_graphql(doc) for doc in docs]


# ==============================
# 6) Mutation
# ==============================
@strawberry.type
class Mutation:
    @strawberry.mutation
    def createEmployee(self, input: EmployeeInput) -> Employee:
        new_id = get_next_sequence("employee_id")

        doc = {
            "id": new_id,
            "name": input.name,
            "age": input.age,
            "job": input.job,
            "language": input.language,
            "pay": input.pay
        }

        employees_col.insert_one(doc)

        return mongo_to_graphql(doc)

    @strawberry.mutation
    def updateEmployee(self, id: strawberry.ID, input: EmployeeInput) -> Employee:
        emp_id = int(id)

        doc = employees_col.find_one({"id": emp_id})
        if not doc:
            raise ValueError("Employee not found")

        employees_col.update_one(
            {"id": emp_id},
            {"$set": {
                "name": input.name,
                "age": input.age,
                "job": input.job,
                "language": input.language,
                "pay": input.pay,
            }}
        )

        updated = employees_col.find_one({"id": emp_id})
        return mongo_to_graphql(updated)

    @strawberry.mutation
    def deleteEmployee(self, id: strawberry.ID) -> strawberry.ID:
        emp_id = int(id)

        result = employees_col.delete_one({"id": emp_id})
        if result.deleted_count == 0:
            raise ValueError("Employee not found")

        return strawberry.ID(str(emp_id))


# ==============================
# 7) 초기 샘플 데이터 세팅
# ==============================
def init_sample_data():
    if employees_col.count_documents({}) > 0:
        return

    samples = [
        {"name": "John",  "age": 35, "job": "frontend",  "language": "react",      "pay": 400},
        {"name": "Peter", "age": 28, "job": "backend",   "language": "java",       "pay": 300},
        {"name": "Sue",   "age": 38, "job": "publisher", "language": "javascript", "pay": 400},
        {"name": "Susan", "age": 45, "job": "pm",        "language": "python",     "pay": 500},
    ]

    for emp in samples:
        new_id = get_next_sequence("employee_id")
        emp_doc = {"id": new_id, **emp}
        employees_col.insert_one(emp_doc)


# ==============================
# 8) FastAPI 설정
# ==============================
app = FastAPI()


@app.on_event("startup")
def startup_event():
    init_sample_data()


# CORS
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

# GraphQL 라우터
schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    return {"message": "FastAPI Mongo + GraphQL Employee Server Running"}
